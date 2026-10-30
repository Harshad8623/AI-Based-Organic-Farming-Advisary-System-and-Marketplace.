"""
routes/auth.py
--------------
Authentication routes: Register, Login, Logout.
Supports two roles: 'farmer' and 'buyer'.
"""

import re
import calendar
from datetime import datetime, date
from decimal import Decimal
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, FarmerProfile, BuyerProfile

# Pre-compiled email pattern for validation
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Show registration form and handle new user creation."""
    if current_user.is_authenticated:
        return _redirect_dashboard()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        role     = request.form.get('role', 'buyer')

        # Validate role — only farmer or buyer are allowed
        if role not in ('farmer', 'buyer'):
            flash('Choose Farmer or Buyer.', 'danger')
            return render_template('auth/register.html', selected_role='farmer'), 400

        # Basic validation
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', selected_role=role)

        if len(email) > 120 or not _EMAIL_RE.fullmatch(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', selected_role=role)

        if not 2 <= len(name) <= 100:
            flash('Name must be between 2 and 100 characters.', 'danger')
            return render_template('auth/register.html', selected_role=role)

        if not 8 <= len(password) <= 128:
            flash('Password must be between 8 and 128 characters.', 'danger')
            return render_template('auth/register.html', selected_role=role)

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', selected_role=role)

        location = request.form.get('location', '').strip()
        phone = request.form.get('phone', '').strip()
        soil_type = request.form.get('soil_type', '').strip()
        if len(location) > 200 or len(soil_type) > 100 or (phone and not re.fullmatch(r'[+\d ()-]{7,20}', phone)):
            flash('Check your location and phone number.', 'danger')
            return render_template('auth/register.html', selected_role=role), 400

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Create user with hashed password
        hashed_pw = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_pw, role=role)
        db.session.add(user)
        try:
            db.session.flush()  # get user.id before commit
        except IntegrityError:
            db.session.rollback()
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Create the appropriate profile
        if role == 'farmer':
            profile = FarmerProfile(
                user_id=user.id,
                farm_location=location,
                soil_type=soil_type,
                phone=phone
            )
            db.session.add(profile)
        else:
            profile = BuyerProfile(
                user_id=user.id,
                location=location,
                phone=phone
            )
            db.session.add(profile)

        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', selected_role='farmer')


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and role-based redirect."""
    if current_user.is_authenticated:
        return _redirect_dashboard()

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first() if len(email) <= 120 and len(password) <= 128 else None

        if user and check_password_hash(user.password, password):
            session.clear()
            login_user(user, remember=request.form.get('remember') == 'on')
            flash('You are signed in.', 'success')
            next_page = request.form.get('next') or request.args.get('next')
            # Security: Only allow relative redirects (prevent open redirect)
            if next_page and (not next_page.startswith('/') or next_page.startswith('//') or '\\' in next_page or
                              any(ord(c) < 32 for c in next_page) or urlsplit(next_page).netloc):
                next_page = None
            return redirect(next_page or _dashboard_url(user))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html')


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _dashboard_url(user):
    if user.role == 'farmer':
        return url_for('auth.farmer_dashboard')
    return url_for('auth.buyer_dashboard')


def _redirect_dashboard():
    return redirect(_dashboard_url(current_user))


@auth_bp.route('/farmer/dashboard')
@login_required
def farmer_dashboard():
    if not current_user.is_farmer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.buyer_dashboard'))
    from models import Product, Order, CropRoadmap
    products = Product.query.filter_by(farmer_id=current_user.id).all()
    pending_orders = Order.query.filter_by(
        farmer_id=current_user.id, status='pending'
    ).count()
    total_orders = Order.query.filter_by(farmer_id=current_user.id).count()
    total_revenue = db.session.query(
        db.func.sum(Order.total_price)
    ).filter_by(farmer_id=current_user.id, status='delivered').scalar() or 0
    roadmap_count = CropRoadmap.query.count()
    from advisory_models import FarmField
    from farm_tools_models import FarmTask, FarmLedgerEntry
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
    first_day = today.replace(day=1)
    last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
    tasks = FarmTask.query.filter_by(farmer_id=current_user.id, is_done=False)
    money = {'income': Decimal('0.00'), 'expense': Decimal('0.00')}
    for kind, amount in db.session.query(FarmLedgerEntry.kind, FarmLedgerEntry.amount).filter(
            FarmLedgerEntry.farmer_id == current_user.id,
            FarmLedgerEntry.entry_date >= first_day, FarmLedgerEntry.entry_date <= last_day).yield_per(100):
        money[kind] += amount
    farm_stats = {
        'fields_count': FarmField.query.filter_by(farmer_id=current_user.id, archived=False).count(),
        'open_tasks': tasks.count(),
        'overdue_tasks': tasks.filter(FarmTask.due_date < today).count(),
        'monthly_income': money['income'], 'monthly_expenses': money['expense'],
    }
    from routes.farm_tools import _advisory_task_context
    from routes.credit_book import due_balances
    due_tasks = tasks.filter(FarmTask.due_date <= today).order_by(FarmTask.due_date, FarmTask.id).limit(5).all()
    credit_due = due_balances(current_user.id, today)
    daily_home = {
        'today': today, 'due_tasks': due_tasks,
        'task_advice': _advisory_task_context(due_tasks, today),
        'overdue_count': farm_stats['overdue_tasks'], 'fields_count': farm_stats['fields_count'],
        'receive_due': credit_due['receive'], 'pay_due': credit_due['pay'],
    }
    return render_template('farmer/dashboard.html',
                           products=products,
                           pending_orders=pending_orders,
                           total_orders=total_orders,
                           total_revenue=round(total_revenue, 2),
                           roadmap_count=roadmap_count, farm_stats=farm_stats, daily_home=daily_home)


@auth_bp.route('/buyer/dashboard')
@login_required
def buyer_dashboard():
    if not current_user.is_buyer():
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.farmer_dashboard'))
    from models import Product
    products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    return render_template('buyer/dashboard.html', products=products)
