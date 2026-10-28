"""Private farmer planning records; independent of marketplace accounting."""

from datetime import datetime, timezone

from models import db


class FarmTask(db.Model):
    __tablename__ = 'farm_tasks'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    crop = db.Column(db.String(80), nullable=False, default='')
    due_date = db.Column(db.Date, nullable=False, index=True)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class FarmLedgerEntry(db.Model):
    __tablename__ = 'farm_ledger_entries'
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='ck_farm_ledger_positive_amount'),
        db.CheckConstraint("kind IN ('income', 'expense')", name='ck_farm_ledger_kind'),
    )

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    kind = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    note = db.Column(db.String(240), nullable=False, default='')
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
