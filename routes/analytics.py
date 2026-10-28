"""Actual marketplace counts and private order activity; no simulated statistics."""
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Product, User, Order

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


def _month_starts(now):
    index = now.year * 12 + now.month - 1
    return [datetime((index-i)//12, (index-i)%12+1, 1, tzinfo=timezone.utc) for i in range(11, -1, -1)]


@analytics_bp.route('/')
@login_required
def dashboard():
    categories = db.session.query(Product.category, db.func.count(Product.id)).group_by(Product.category).all()
    owned_orders = Order.query.filter_by(**({'farmer_id': current_user.id} if current_user.is_farmer() else {'buyer_id': current_user.id})).all()
    months = _month_starts(datetime.now(timezone.utc))
    monthly = []
    for month in months:
        matches = [order for order in owned_orders if order.created_at and
                   (order.created_at.year, order.created_at.month) == (month.year, month.month)]
        delivered = [order for order in matches if order.status == 'delivered']
        monthly.append({'label': month.strftime('%b %Y'), 'orders': len(matches),
                        'delivered': len(delivered),
                        'amount': sum((Decimal(str(order.total_price)) for order in delivered), Decimal('0'))})
    statuses = {status: sum(order.status == status for order in owned_orders) for status in Order.STATUS_CHOICES}
    return render_template('analytics/dashboard.html', categories=categories, monthly=monthly, statuses=statuses,
        stats={'total_farmers': User.query.filter_by(role='farmer').count(),
               'total_buyers': User.query.filter_by(role='buyer').count(),
               'total_products': Product.query.count(), 'your_orders': len(owned_orders)})
