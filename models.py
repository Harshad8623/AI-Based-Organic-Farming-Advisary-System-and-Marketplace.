"""
models.py
---------
SQLAlchemy database models for the Organic Farming Platform.
Tables: User, FarmerProfile, BuyerProfile, Product,
        Order, Rating, CartItem, CropRoadmap
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy.orm import validates

# Single SQLAlchemy instance shared across the app
db = SQLAlchemy()


# ---------------------------------------------------------------------------
# User Model
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    """Main user table — stores both farmers and buyers."""
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20),  nullable=False)  # 'farmer' | 'buyer'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    farmer_profile   = db.relationship('FarmerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    buyer_profile    = db.relationship('BuyerProfile',  backref='user', uselist=False, cascade='all, delete-orphan')
    products         = db.relationship('Product', backref='farmer', lazy=True, cascade='all, delete-orphan',
                                       foreign_keys='Product.farmer_id')
    orders_as_buyer  = db.relationship('Order', backref='buyer',  lazy=True, foreign_keys='Order.buyer_id')
    orders_as_farmer = db.relationship('Order', backref='farmer', lazy=True, foreign_keys='Order.farmer_id')
    cart_items       = db.relationship('CartItem', backref='buyer', lazy=True, cascade='all, delete-orphan')
    ratings_given    = db.relationship('Rating', backref='buyer',  lazy=True, foreign_keys='Rating.buyer_id')

    def is_farmer(self):
        return self.role == 'farmer'

    def is_buyer(self):
        return self.role == 'buyer'

    def __repr__(self):
        return f'<User {self.name} [{self.role}]>'


# ---------------------------------------------------------------------------
# Farmer Profile
# ---------------------------------------------------------------------------
class FarmerProfile(db.Model):
    """Extended profile for farmers."""
    __tablename__ = 'farmer_profiles'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farm_location = db.Column(db.String(200))
    soil_type     = db.Column(db.String(100))
    farm_size     = db.Column(db.String(50))   # e.g. "5 acres"
    phone         = db.Column(db.String(20))

    def __repr__(self):
        return f'<FarmerProfile user_id={self.user_id}>'


# ---------------------------------------------------------------------------
# Buyer Profile
# ---------------------------------------------------------------------------
class BuyerProfile(db.Model):
    """Extended profile for buyers."""
    __tablename__ = 'buyer_profiles'

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location = db.Column(db.String(200))
    phone    = db.Column(db.String(20))

    def __repr__(self):
        return f'<BuyerProfile user_id={self.user_id}>'


# ---------------------------------------------------------------------------
# Product (Marketplace)
# ---------------------------------------------------------------------------
class Product(db.Model):
    """Products listed by farmers in the marketplace."""
    __tablename__ = 'products'

    id             = db.Column(db.Integer, primary_key=True)
    farmer_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name           = db.Column(db.String(100), nullable=False)
    price          = db.Column(db.Float,  nullable=False)
    quantity       = db.Column(db.String(50),  nullable=False)
    description    = db.Column(db.Text)
    image_filename = db.Column(db.String(200))
    category       = db.Column(db.String(50))
    created_at     = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    orders     = db.relationship('Order',    backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade='all, delete-orphan')
    ratings    = db.relationship('Rating',   backref='product', lazy=True)

    @property
    def purchase_limit(self):
        from commerce import parse_stock, MAX_QUANTITY
        try:
            amount, _ = parse_stock(self.quantity)
            return min(int(amount), MAX_QUANTITY)
        except ValueError:
            return 0

    @property
    def stock_unit(self):
        from commerce import parse_stock
        try:
            return parse_stock(self.quantity)[1]
        except ValueError:
            return 'unit'

    @property
    def avg_rating(self):
        if not self.ratings:
            return 0
        return round(sum(r.stars for r in self.ratings) / len(self.ratings), 1)

    def __repr__(self):
        return f'<Product {self.name} by farmer_id={self.farmer_id}>'


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------
class Order(db.Model):
    """An order placed by a buyer for a farmer's product."""
    __tablename__ = 'orders'

    STATUS_CHOICES = ['pending', 'accepted', 'rejected', 'shipped', 'delivered']

    id                = db.Column(db.Integer, primary_key=True)
    buyer_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farmer_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id        = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)  # nullable: product may be deleted
    quantity_ordered  = db.Column(db.Integer, nullable=False, default=1)
    total_price       = db.Column(db.Float, nullable=False)
    delivery_location = db.Column(db.String(500), nullable=False)
    payment_method    = db.Column(db.String(20), nullable=False)  # 'cod' | 'upi' | 'razorpay'
    upi_id            = db.Column(db.String(100))                 # filled if UPI
    razorpay_order_id   = db.Column(db.String(100))               # Razorpay order reference
    razorpay_payment_id = db.Column(db.String(100))               # Razorpay payment reference
    status            = db.Column(db.String(20), nullable=False, default='pending')
    created_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    rating = db.relationship('Rating', backref='order', uselist=False, cascade='all, delete-orphan')
    receipt = db.relationship('OrderReceipt', backref='order', uselist=False, cascade='all, delete-orphan')

    @property
    def product_name(self):
        """Keep new receipts independent of mutable/deleted marketplace listings."""
        if self.receipt:
            return self.receipt.product_name
        return self.product.name if self.product else '(Product removed)'

    @property
    def quantity_unit(self):
        # An old record without a receipt has no reliable historical unit.
        return self.receipt.unit if self.receipt else ''

    @validates('status')
    def validate_status(self, key, value):
        if value not in self.STATUS_CHOICES:
            raise ValueError(f'Invalid order status: "{value}". Must be one of {self.STATUS_CHOICES}.')
        return value

    def status_index(self):
        # Returns position in the forward-progress flow; rejected = -1 (terminal failure state)
        statuses = ['pending', 'accepted', 'shipped', 'delivered']
        if self.status == 'rejected':
            return -1
        try:
            return statuses.index(self.status)
        except ValueError:
            return -1

    def __repr__(self):
        return f'<Order #{self.id} [{self.status}]>'


# ---------------------------------------------------------------------------
# Rating
# ---------------------------------------------------------------------------
class Rating(db.Model):
    """Star rating + review submitted by buyer after delivery."""
    __tablename__ = 'ratings'

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    buyer_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farmer_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)  # nullable: product may be deleted
    stars      = db.Column(db.Integer, nullable=False)  # 1-5
    review     = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Rating {self.stars}★ for order #{self.order_id}>'


# ---------------------------------------------------------------------------
# Cart Item
# ---------------------------------------------------------------------------
class CartItem(db.Model):
    """A single item in a buyer's cart."""
    __tablename__ = 'cart_items'

    id         = db.Column(db.Integer, primary_key=True)
    buyer_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False, default=1)

    def subtotal(self):
        return self.quantity * self.product.price

    def __repr__(self):
        return f'<CartItem product_id={self.product_id} qty={self.quantity}>'


# ---------------------------------------------------------------------------
# Crop Roadmap
# ---------------------------------------------------------------------------
class CropRoadmap(db.Model):
    """Detailed organic farming roadmap for a specific crop."""
    __tablename__ = 'crop_roadmaps'

    id               = db.Column(db.Integer, primary_key=True)
    crop_name        = db.Column(db.String(100), nullable=False)
    slug             = db.Column(db.String(100), unique=True, nullable=False)
    emoji            = db.Column(db.String(10), default='🌱')
    description      = db.Column(db.Text)
    season           = db.Column(db.String(50))   # Kharif / Rabi / Zaid / Year-round
    duration_days    = db.Column(db.Integer)       # Approx. seed-to-harvest days
    expected_yield   = db.Column(db.String(100))   # e.g. "20–25 tonnes/hectare"
    soil_type        = db.Column(db.String(200))
    climate          = db.Column(db.String(200))
    # JSON string of stages: [{"stage": "...", "days": "...", "actions": [...], "tips": [...]}]
    stages_json      = db.Column(db.Text)

    def __repr__(self):
        return f'<CropRoadmap {self.crop_name}>'


class CheckoutAttempt(db.Model):
    """Immutable checkout snapshot and durable replay protection.

    Added as a new table so existing installations require no column migration.
    """
    __tablename__ = 'checkout_attempts'
    id = db.Column(db.String(64), primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount_paise = db.Column(db.Integer, nullable=False)
    delivery_location = db.Column(db.String(500), nullable=False)
    items_json = db.Column(db.Text, nullable=False)
    gateway_order_id = db.Column(db.String(100), unique=True)
    payment_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class OrderReceipt(db.Model):
    """Immutable purchased listing details, additive for existing installations."""
    __tablename__ = 'order_receipts'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    unit_price_paise = db.Column(db.Integer, nullable=False)
