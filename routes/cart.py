"""Cart and checkout with immutable payment snapshots and atomic stock updates."""
import hashlib
import hmac
import json
import secrets
import re

import razorpay
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import db, CartItem, Product, Order, CheckoutAttempt, OrderReceipt
from commerce import parse_stock, stock_text, price_paise, order_quantity, MAX_TOTAL_PAISE

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def _payment_enabled():
    return bool((current_app.config.get('RAZORPAY_KEY_ID') or '').strip()
                and (current_app.config.get('RAZORPAY_KEY_SECRET') or '').strip())


def _razorpay_client():
    if not _payment_enabled():
        raise ValueError('Online payments are unavailable. Please use cash on delivery.')
    return razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'].strip(),
                                current_app.config['RAZORPAY_KEY_SECRET'].strip()))


def _buyer():
    if not current_user.is_buyer():
        abort(403)


def _address(value):
    if not isinstance(value, str) or not 5 <= len(value.strip()) <= 500:
        raise ValueError('Enter a delivery address between 5 and 500 characters.')
    return value.strip()


def _snapshot():
    items = CartItem.query.filter_by(buyer_id=current_user.id).order_by(CartItem.id).all()
    if not items:
        raise ValueError('Your cart is empty.')
    snapshot = []
    total = 0
    for item in items:
        product = item.product
        if product is None or product.farmer_id == current_user.id:
            raise ValueError('A product is no longer available. Please update your cart.')
        qty = order_quantity(item.quantity)
        available, unit = parse_stock(product.quantity)
        if qty > available:
            raise ValueError(f'Only {product.quantity} of {product.name} is available. Update your cart.')
        unit_paise = price_paise(product.price)
        total += unit_paise * qty
        snapshot.append({'cart_id': item.id, 'product_id': product.id,
                         'farmer_id': product.farmer_id, 'name': product.name,
                         'quantity': qty, 'unit_paise': unit_paise, 'unit': unit})
    if not 0 < total <= MAX_TOTAL_PAISE:
        raise ValueError('This order total is too large. Please split your order.')
    return snapshot, total


def _fulfil(attempt, method, payment_id=None):
    """Must be committed with the attempt claim in the same transaction.

    Conditional writes protect against stale carts and concurrent purchases on
    both SQLite and PostgreSQL; all lines roll back if any stock update fails.
    """
    snapshot = json.loads(attempt.items_json)
    for line in snapshot:
        product = db.session.get(Product, line['product_id'], populate_existing=True)
        if not product or product.farmer_id != line['farmer_id']:
            raise ValueError('A product is no longer available.')
        available, unit = parse_stock(product.quantity)
        if unit != line['unit'] or price_paise(product.price) != line['unit_paise']:
            raise ValueError(f'The price or unit of {line["name"]} changed. Please review your cart.')
        if available < line['quantity']:
            raise ValueError(f'Insufficient stock for {line["name"]}. Please review your cart.')
        updated = db.session.query(Product).filter(
            Product.id == product.id, Product.quantity == product.quantity,
            Product.price == product.price
        ).update({Product.quantity: stock_text(available - line['quantity'], unit)}, synchronize_session=False)
        if updated != 1:
            raise ValueError('Stock changed while ordering. Please review your cart and retry.')
        order = Order(
            buyer_id=attempt.buyer_id, farmer_id=line['farmer_id'], product_id=line['product_id'],
            quantity_ordered=line['quantity'], total_price=line['quantity'] * line['unit_paise'] / 100,
            delivery_location=attempt.delivery_location, payment_method=method,
            razorpay_order_id=attempt.gateway_order_id, razorpay_payment_id=payment_id,
            status='pending',
        )
        order.receipt = OrderReceipt(product_name=line['name'], unit=line['unit'], unit_price_paise=line['unit_paise'])
        db.session.add(order)
        # Only consume the original cart line. New items added during payment remain.
        item = db.session.get(CartItem, line['cart_id'])
        if item and item.buyer_id == attempt.buyer_id and item.product_id == line['product_id']:
            if item.quantity > line['quantity']:
                item.quantity -= line['quantity']
            else:
                db.session.delete(item)
    attempt.status = 'complete'
    attempt.payment_id = payment_id
    return len(snapshot)


@cart_bp.route('/')
@login_required
def view_cart():
    _buyer()
    items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    total = 0
    for item in items:
        try:
            total += price_paise(item.product.price) * item.quantity
        except (ValueError, AttributeError):
            flash('A listing has an invalid price. Remove it or ask the farmer to update it.', 'warning')
    session.setdefault('checkout_token', secrets.token_hex(24))
    return render_template('cart/cart.html', items=items, total=total / 100,
                           checkout_token=session['checkout_token'],
                           razorpay_key=current_app.config.get('RAZORPAY_KEY_ID', '') if _payment_enabled() else '')


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    _buyer()
    product = db.get_or_404(Product, product_id)
    existing = CartItem.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    try:
        if product.farmer_id == current_user.id:
            raise ValueError('You cannot buy your own product.')
        qty = order_quantity(request.form.get('quantity', '1'))
        qty = order_quantity(qty + (existing.quantity if existing else 0))
        available, _ = parse_stock(product.quantity)
        price_paise(product.price)
        if qty > available:
            raise ValueError(f'Only {product.quantity} of {product.name} is available.')
        if existing:
            existing.quantity = qty
        else:
            db.session.add(CartItem(buyer_id=current_user.id, product_id=product.id, quantity=qty))
        db.session.commit()
        flash(f'{product.name} added to your cart.', 'success')
    except ValueError as error:
        db.session.rollback()
        flash(str(error), 'warning')
    return redirect(url_for('marketplace.listing'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    _buyer()
    item = db.get_or_404(CartItem, item_id)
    if item.buyer_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    _buyer()
    item = db.get_or_404(CartItem, item_id)
    if item.buyer_id != current_user.id:
        abort(403)
    try:
        qty = order_quantity(request.form.get('quantity'), allow_zero=True)
        if qty == 0:
            db.session.delete(item)
        else:
            available, _ = parse_stock(item.product.quantity)
            if qty > available:
                raise ValueError(f'Only {item.product.quantity} is available.')
            item.quantity = qty
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        flash(str(error), 'warning')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    _buyer()
    token = request.form.get('checkout_token', '')
    if not re.fullmatch(r'[a-f0-9]{48}', token) or not hmac.compare_digest(token, session.get('checkout_token', '')):
        flash('This checkout form has expired. Review your cart and try again.', 'warning')
        return redirect(url_for('cart.view_cart'))
    previous = db.session.get(CheckoutAttempt, token)
    if previous and previous.buyer_id == current_user.id and previous.status == 'complete':
        flash('This order was already placed. You have not been charged again.', 'info')
        return redirect(url_for('orders.buyer_orders'))
    try:
        location = _address(request.form.get('delivery_location'))
        snapshot, total = _snapshot()
        attempt = CheckoutAttempt(id=token, buyer_id=current_user.id, amount_paise=total,
                                  delivery_location=location, items_json=json.dumps(snapshot), status='processing')
        db.session.add(attempt)
        db.session.flush()  # Unique token claims this checkout before any stock mutation.
        count = _fulfil(attempt, 'cod')
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('This checkout has already been submitted. Check My Orders before retrying.', 'info')
        return redirect(url_for('orders.buyer_orders'))
    except ValueError as error:
        db.session.rollback()
        flash(str(error), 'warning')
        return redirect(url_for('cart.view_cart'))
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Checkout transaction failed')
        flash('We could not save your order. No order was placed. Please retry.', 'danger')
        return redirect(url_for('cart.view_cart'))
    session['checkout_token'] = secrets.token_hex(24)
    flash(f'{count} order(s) placed with cash on delivery. Track confirmation in My Orders.', 'success')
    return redirect(url_for('orders.buyer_orders'))


@cart_bp.route('/create-razorpay-order', methods=['POST'])
@login_required
def create_razorpay_order():
    _buyer()
    if not _payment_enabled():
        return jsonify(error='Online payments are unavailable. Please use cash on delivery.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='A JSON checkout request is required.'), 400
    try:
        location = _address(data.get('delivery_location'))
        snapshot, total = _snapshot()
    except ValueError as error:
        return jsonify(error=str(error)), 400
    attempt = CheckoutAttempt(id=secrets.token_hex(24), buyer_id=current_user.id, amount_paise=total,
                              delivery_location=location, items_json=json.dumps(snapshot), status='pending')
    try:
        gateway = _razorpay_client().order.create({
            'amount': total, 'currency': 'INR', 'receipt': attempt.id[:40],
            'notes': {'buyer_id': str(current_user.id), 'checkout_id': attempt.id},
        }, timeout=(5, 15))
        if not isinstance(gateway.get('id'), str) or not gateway['id']:
            raise ValueError('Missing payment order identifier')
        attempt.gateway_order_id = gateway['id']
        db.session.add(attempt)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.error('Payment order creation failed')
        return jsonify(error='Payment gateway is unavailable. No payment was taken; use COD or retry.'), 502
    return jsonify(razorpay_order_id=attempt.gateway_order_id, amount=total, currency='INR',
                   key=current_app.config['RAZORPAY_KEY_ID'].strip(), name=current_user.name, email=current_user.email)


@cart_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    _buyer()
    if not _payment_enabled():
        abort(503)
    gateway_id = request.form.get('razorpay_order_id', '')
    payment_id = request.form.get('razorpay_payment_id', '')
    signature = request.form.get('razorpay_signature', '')
    if not gateway_id or len(gateway_id) > 100 or not re.fullmatch(r'[a-f0-9]{64}', signature):
        abort(400, description='Invalid payment confirmation.')
    attempt = CheckoutAttempt.query.filter_by(gateway_order_id=gateway_id, buyer_id=current_user.id).first()
    if not attempt or not payment_id or len(payment_id) > 100:
        abort(400, description='Payment does not belong to this checkout.')
    secret = current_app.config['RAZORPAY_KEY_SECRET'].strip().encode()
    expected = hmac.new(secret, f'{gateway_id}|{payment_id}'.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        abort(400, description='Invalid payment signature.')
    if attempt.status == 'complete':
        flash('Your payment was already recorded. See My Orders.', 'info')
        return redirect(url_for('orders.buyer_orders'))
    try:
        payment = _razorpay_client().payment.fetch(payment_id, timeout=(5, 15))
        if (payment.get('order_id') != gateway_id or payment.get('currency') != 'INR'
                or payment.get('amount') != attempt.amount_paise or payment.get('status') != 'captured'):
            raise ValueError('Payment is not confirmed as captured for this order. Keep your payment reference and retry later.')
        claimed = CheckoutAttempt.query.filter_by(id=attempt.id, status='pending').update(
            {CheckoutAttempt.status: 'processing'}, synchronize_session=False)
        if claimed != 1:
            raise ValueError('This payment is already being processed. Check My Orders.')
        count = _fulfil(attempt, 'razorpay', payment_id)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        # A captured payment must never silently produce incorrect or oversold orders.
        flash(f'{error} If money was deducted, contact the platform operator with payment reference {payment_id}; do not pay again.', 'danger')
        return redirect(url_for('cart.view_cart'))
    except Exception:
        db.session.rollback()
        current_app.logger.error('Payment reconciliation failed')
        flash(f'Payment confirmation is temporarily unavailable. Keep reference {payment_id} and retry confirmation; do not pay again.', 'danger')
        return redirect(url_for('cart.view_cart'))
    flash(f'Payment confirmed. {count} order(s) placed.', 'success')
    return redirect(url_for('orders.buyer_orders'))
