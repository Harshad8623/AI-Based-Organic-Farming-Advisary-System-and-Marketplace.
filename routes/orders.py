"""
routes/orders.py
----------------
Order Management:
  - Buyer: view orders, submit ratings
  - Farmer: view incoming orders, accept/reject/ship/deliver
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, Order, Rating, Product
from commerce import parse_stock, stock_text
from datetime import datetime, timezone

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

STATUS_FLOW = {
    'pending':  ['accepted', 'rejected'],
    'accepted': ['shipped'],
    'shipped':  ['delivered'],
}


# ---------------------------------------------------------------------------
# Buyer: My Orders
# ---------------------------------------------------------------------------
@orders_bp.route('/my')
@login_required
def buyer_orders():
    if not current_user.is_buyer():
        flash('Only buyers can view their orders.', 'danger')
        return redirect(url_for('marketplace.listing'))

    orders = Order.query.filter_by(buyer_id=current_user.id)\
                        .order_by(Order.created_at.desc()).all()

    # Map order_id -> has rating
    rated_ids = {r.order_id for r in current_user.ratings_given}
    return render_template('orders/buyer_orders.html', orders=orders, rated_ids=rated_ids)


# ---------------------------------------------------------------------------
# Farmer: Incoming Orders
# ---------------------------------------------------------------------------
@orders_bp.route('/farmer')
@login_required
def farmer_orders():
    if not current_user.is_farmer():
        flash('Only farmers can view farmer orders.', 'danger')
        return redirect(url_for('marketplace.listing'))

    orders = Order.query.filter_by(farmer_id=current_user.id)\
                        .order_by(Order.created_at.desc()).all()
    return render_template('orders/farmer_orders.html', orders=orders,
                           delivered_revenue=sum(order.total_price for order in orders if order.status == 'delivered'))


# ---------------------------------------------------------------------------
# Farmer: Update Order Status
# ---------------------------------------------------------------------------
@orders_bp.route('/<int:order_id>/update', methods=['POST'])
@login_required
def update_status(order_id):
    if not current_user.is_farmer():
        abort(403)

    order = db.get_or_404(Order, order_id)
    if order.farmer_id != current_user.id:
        abort(403)

    new_status = request.form.get('status')
    allowed = STATUS_FLOW.get(order.status, [])

    if new_status not in allowed:
        flash(f'Cannot change status from "{order.status}" to "{new_status}".', 'danger')
        return redirect(url_for('orders.farmer_orders'))

    if new_status == 'rejected' and order.payment_method == 'razorpay':
        flash('This order is already paid online. Contact the platform operator to arrange a refund before cancellation; this page cannot issue refunds.', 'warning')
        return redirect(url_for('orders.farmer_orders'))

    # A conditional status transition makes retries and concurrent requests safe.
    changed = Order.query.filter_by(id=order.id, status=order.status).update(
        {Order.status: new_status, Order.updated_at: datetime.now(timezone.utc)}, synchronize_session=False)
    if changed != 1:
        db.session.rollback()
        flash('The order was updated elsewhere. Please review its current status.', 'warning')
        return redirect(url_for('orders.farmer_orders'))
    manual_stock_review = False
    if new_status == 'rejected' and order.product_id:
        product = db.session.get(Product, order.product_id, populate_existing=True)
        if product:
            try:
                available, unit = parse_stock(product.quantity)
            except ValueError:
                manual_stock_review = True
            else:
                # Historical orders predate reliable unit snapshots. Never infer
                # their stock adjustment from an ambiguous, subsequently edited listing.
                if not order.receipt or order.receipt.unit != unit:
                    manual_stock_review = True
                else:
                    restored = Product.query.filter_by(id=product.id, quantity=product.quantity).update(
                        {Product.quantity: stock_text(available + order.quantity_ordered, unit)}, synchronize_session=False)
                    if restored != 1:
                        db.session.rollback()
                        flash('Stock changed elsewhere. Please retry this status update.', 'warning')
                        return redirect(url_for('orders.farmer_orders'))
    db.session.commit()

    status_msg = {
        'accepted':  'Order accepted. The buyer can see the update in My Orders.',
        'rejected':  '❌ Order rejected.',
        'shipped':   '🚚 Order marked as shipped!',
        'delivered': '🎉 Order marked as delivered!',
    }
    flash(status_msg.get(new_status, 'Order status updated.'), 'success')
    if manual_stock_review:
        flash('This older order or listing has no reliable stock unit. Stock was left unchanged; count your available inventory and update the listing before selling again.', 'warning')
    return redirect(url_for('orders.farmer_orders'))


# ---------------------------------------------------------------------------
# Buyer: Rate Order
# ---------------------------------------------------------------------------
@orders_bp.route('/<int:order_id>/rate', methods=['GET', 'POST'])
@login_required
def rate_order(order_id):
    if not current_user.is_buyer():
        abort(403)

    order = db.get_or_404(Order, order_id)

    if order.buyer_id != current_user.id:
        abort(403)

    if order.status != 'delivered':
        flash('You can only rate delivered orders.', 'warning')
        return redirect(url_for('orders.buyer_orders'))

    if order.rating:
        flash('You have already rated this order.', 'info')
        return redirect(url_for('orders.buyer_orders'))

    if order.product_id is None:
        flash('This product has been removed by the farmer and cannot be rated.', 'warning')
        return redirect(url_for('orders.buyer_orders'))

    if request.method == 'POST':
        try:
            stars = int(request.form.get('stars', ''))
        except (ValueError, TypeError):
            stars = 0
        review = request.form.get('review', '').strip()

        if len(review) > 2000:
            flash('Review must be 2,000 characters or fewer.', 'danger')
            return redirect(url_for('orders.rate_order', order_id=order_id))

        if stars < 1 or stars > 5:
            flash('Please select a rating between 1 and 5 stars.', 'danger')
            return redirect(url_for('orders.rate_order', order_id=order_id))

        # Claim the order version before inserting a review. This also works
        # on existing databases without adding a unique index to old ratings.
        claimed = Order.query.filter_by(id=order.id, updated_at=order.updated_at).update(
            {Order.updated_at: datetime.now(timezone.utc)}, synchronize_session=False)
        if claimed != 1:
            db.session.rollback()
            flash('This order was updated elsewhere. Please review My Orders before retrying.', 'warning')
            return redirect(url_for('orders.buyer_orders'))

        rating = Rating(
            order_id   = order.id,
            buyer_id   = current_user.id,
            farmer_id  = order.farmer_id,
            product_id = order.product_id,
            stars      = stars,
            review     = review
        )
        db.session.add(rating)
        db.session.commit()
        flash(f'⭐ Thank you for your {stars}-star review!', 'success')
        return redirect(url_for('orders.buyer_orders'))

    return render_template('orders/rate_order.html', order=order)
