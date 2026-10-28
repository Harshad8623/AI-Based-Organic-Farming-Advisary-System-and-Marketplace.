"""Farmer listings with validated prices, explicit stock units and safe images."""
import os
import uuid
import warnings
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from models import db, Product, Order, User
from commerce import parse_stock, stock_text, price_paise

marketplace_bp = Blueprint('marketplace', __name__, url_prefix='/marketplace')
ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
CATEGORIES = {'Vegetables', 'Fruits', 'Grains', 'Pulses', 'Spices', 'Dairy', 'Herbs', 'Seeds', 'Fertilizers', 'Other'}


def _product_fields():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    if not 2 <= len(name) <= 100:
        raise ValueError('Product name must contain between 2 and 100 characters.')
    if len(description) > 3000:
        raise ValueError('Description must be 3,000 characters or fewer.')
    if category and category not in CATEGORIES:
        raise ValueError('Choose a category from the list.')
    paise = price_paise(request.form.get('price'))
    amount, unit = parse_stock(request.form.get('quantity'))
    return dict(name=name, description=description, category=category,
                price=paise / 100, quantity=stock_text(amount, unit))


def _save_image(file):
    """Verify real image bytes and re-encode to strip active content/metadata."""
    if not file or not file.filename:
        return None
    extension = file.filename.rsplit('.', 1)[-1].lower()
    if extension not in ALLOWED:
        raise ValueError('Upload a JPG, PNG or WebP image.')
    filename = None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(file.stream)
            if image.format not in {'JPEG', 'PNG', 'WEBP'} or image.width * image.height > 20_000_000:
                raise ValueError('Choose a JPG, PNG or WebP photo smaller than 20 megapixels.')
            image.verify()
            file.stream.seek(0)
            image = Image.open(file.stream)
            image.load()
            image = image.convert('RGB')
            image.thumbnail((1600, 1600))
            filename = f'{uuid.uuid4().hex}.jpg'
            image.save(Path(current_app.config['UPLOAD_FOLDER']) / filename, 'JPEG', quality=88)
            return filename
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning, ValueError):
        if filename:
            _delete_image(filename)
        raise ValueError('The image could not be read. Choose a valid JPG, PNG or WebP photo under 20 megapixels.') from None


def _delete_image(filename):
    if not filename:
        return
    root = Path(current_app.config['UPLOAD_FOLDER']).resolve()
    path = (root / filename).resolve()
    if path.parent == root and path.is_file():
        try:
            path.unlink()
        except OSError:
            current_app.logger.warning('Could not remove an old product image')


@marketplace_bp.route('/')
def listing():
    search = request.args.get('search', '').strip()[:100]
    category = request.args.get('category', '')
    query = Product.query
    if search:
        # Treat user input literally, including SQL LIKE wildcard characters.
        term = search.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.filter(Product.name.ilike(f'%{term}%', escape='\\'))
    if category:
        query = query.filter_by(category=category)
    sort = request.args.get('sort', 'newest')
    ordering = {'price_low': Product.price.asc(), 'price_high': Product.price.desc()}.get(sort, Product.created_at.desc())
    products = query.order_by(ordering, Product.id.desc()).all()
    categories = [row[0] for row in db.session.query(Product.category).distinct().order_by(Product.category).all() if row[0]]
    return render_template('marketplace/listing.html', products=products, categories=categories,
                           search=search, selected_category=category, selected_sort=sort)


@marketplace_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_farmer():
        abort(403)
    if request.method == 'POST':
        filename = None
        try:
            fields = _product_fields()
            filename = _save_image(request.files.get('image'))
            db.session.add(Product(farmer_id=current_user.id, image_filename=filename, **fields))
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            _delete_image(filename)
            flash(str(error), 'danger')
            return render_template('marketplace/add_product.html'), 400
        except Exception:
            db.session.rollback()
            _delete_image(filename)
            raise
        flash('Product added successfully.', 'success')
        return redirect(url_for('marketplace.my_products'))
    return render_template('marketplace/add_product.html')


@marketplace_bp.route('/my-products')
@login_required
def my_products():
    if not current_user.is_farmer():
        abort(403)
    products = Product.query.filter_by(farmer_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template('marketplace/my_products.html', products=products)


@marketplace_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_farmer():
        abort(403)
    product = db.get_or_404(Product, product_id)
    if product.farmer_id != current_user.id:
        abort(403)
    active_orders = Order.query.filter(Order.product_id == product_id, Order.status.in_(('pending', 'accepted', 'shipped'))).count()
    if active_orders:
        flash('Resolve all pending, accepted and shipped orders before removing this listing.', 'warning')
        return redirect(url_for('marketplace.my_products'))
    # Nullable relationships preserve completed order and rating history.
    filename = product.image_filename
    db.session.delete(product)
    db.session.commit()
    _delete_image(filename)
    flash('Product deleted. Completed orders and reviews remain in your history.', 'success')
    return redirect(url_for('marketplace.my_products'))


@marketplace_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not current_user.is_farmer():
        abort(403)
    product = db.get_or_404(Product, product_id)
    if product.farmer_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        filename = None
        old_image = product.image_filename
        try:
            fields = _product_fields()
            new_unit = parse_stock(fields['quantity'])[1]
            if new_unit != product.stock_unit and Order.query.filter(Order.product_id == product.id, Order.status.in_(('pending', 'accepted', 'shipped'))).first():
                raise ValueError('Keep the same stock unit until all active orders are resolved.')
            filename = _save_image(request.files.get('image'))
            for key, value in fields.items():
                setattr(product, key, value)
            if filename:
                product.image_filename = filename
            db.session.commit()
        except ValueError as error:
            db.session.rollback()
            _delete_image(filename)
            flash(str(error), 'danger')
            return render_template('marketplace/edit_product.html', product=product), 400
        except Exception:
            db.session.rollback()
            _delete_image(filename)
            raise
        if filename:
            _delete_image(old_image)
        flash('Product updated successfully.', 'success')
        return redirect(url_for('marketplace.my_products'))
    return render_template('marketplace/edit_product.html', product=product)


@marketplace_bp.route('/farmer/<int:farmer_id>')
def farmer_detail(farmer_id):
    farmer = db.session.get(User, farmer_id)
    if not farmer or not farmer.is_farmer():
        abort(404)
    products = Product.query.filter_by(farmer_id=farmer_id).all()
    return render_template('marketplace/farmer_detail.html', farmer=farmer, products=products)
