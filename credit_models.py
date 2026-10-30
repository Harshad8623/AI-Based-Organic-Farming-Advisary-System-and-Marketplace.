"""Private credit records. Paise integers keep settlements exact on every database."""
from datetime import datetime, timezone
from decimal import Decimal

from models import db


class CreditAccount(db.Model):
    __tablename__ = 'credit_accounts'
    __table_args__ = (
        db.CheckConstraint("direction IN ('receive', 'pay')", name='ck_credit_direction'),
        db.CheckConstraint('total_paise > 0', name='ck_credit_total_positive'),
        db.CheckConstraint('settled_paise >= 0 AND settled_paise <= total_paise', name='ck_credit_settled_bounds'),
        db.CheckConstraint('NOT voided OR settled_paise = 0', name='ck_credit_void_unpaid'),
    )
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    contact_name = db.Column(db.String(100), nullable=False)
    direction = db.Column(db.String(10), nullable=False)
    total_paise = db.Column(db.BigInteger, nullable=False)
    settled_paise = db.Column(db.BigInteger, nullable=False, default=0)
    entry_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, index=True)
    note = db.Column(db.String(300), nullable=False, default='')
    voided = db.Column(db.Boolean, nullable=False, default=False)
    void_reason = db.Column(db.String(240), nullable=False, default='')
    voided_at = db.Column(db.DateTime)
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    payments = db.relationship('CreditPayment', back_populates='account', lazy=True)

    @property
    def total(self):
        return Decimal(self.total_paise) / 100

    @property
    def settled(self):
        return Decimal(self.settled_paise) / 100

    @property
    def remaining(self):
        return Decimal(0 if self.voided else self.total_paise - self.settled_paise) / 100


class CreditPayment(db.Model):
    __tablename__ = 'credit_payments'
    __table_args__ = (
        db.CheckConstraint('amount_paise > 0', name='ck_credit_payment_positive'),
        db.CheckConstraint('balance_after_paise >= 0', name='ck_credit_payment_balance'),
    )
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('credit_accounts.id'), nullable=False, index=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount_paise = db.Column(db.BigInteger, nullable=False)
    balance_after_paise = db.Column(db.BigInteger, nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(240), nullable=False, default='')
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    account = db.relationship('CreditAccount', back_populates='payments')

    @property
    def amount(self):
        return Decimal(self.amount_paise) / 100

    @property
    def remaining(self):
        return Decimal(self.balance_after_paise) / 100
