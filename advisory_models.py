"""Farmer-owned field context, observation reports and reported outcomes.

These are additive tables. Advice snapshots preserve what inputs and rules were
used at the time; editing a field never rewrites a past decision record.
"""
from datetime import datetime, timezone
from models import db


class FarmField(db.Model):
    __tablename__ = 'advisory_fields'
    __table_args__ = (
        db.CheckConstraint('area_m2 IS NULL OR area_m2 > 0', name='ck_advisory_field_positive_area'),
        db.CheckConstraint('version > 0', name='ck_advisory_field_version'),
    )
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False, default='')
    crop = db.Column(db.String(30), nullable=False)
    stage = db.Column(db.String(30), nullable=False)
    soil = db.Column(db.String(20), nullable=False, default='unknown')
    area_m2 = db.Column(db.Numeric(14, 2))
    irrigation = db.Column(db.String(20), nullable=False, default='rainfed')
    planting_date = db.Column(db.Date)
    archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    observations = db.relationship('FieldObservation', back_populates='field', lazy=True)

    def context_snapshot(self):
        return {'field_id': self.id, 'name': self.name, 'location': self.location,
                'crop': self.crop, 'stage': self.stage, 'soil': self.soil,
                'area_m2': str(self.area_m2) if self.area_m2 is not None else None,
                'irrigation': self.irrigation,
                'planting_date': self.planting_date.isoformat() if self.planting_date else None}


class FieldObservation(db.Model):
    __tablename__ = 'field_observations'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    field_id = db.Column(db.Integer, db.ForeignKey('advisory_fields.id'), nullable=False, index=True)
    field_snapshot = db.Column(db.JSON, nullable=False)
    observation_data = db.Column(db.JSON, nullable=False)
    report_data = db.Column(db.JSON, nullable=False)
    submission_id = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    field = db.relationship('FarmField', back_populates='observations')
    followup = db.relationship('AdvisoryFollowup', back_populates='observation', uselist=False)
    task_links = db.relationship('AdvisoryTaskLink', back_populates='observation')


class AdvisoryFollowup(db.Model):
    __tablename__ = 'advisory_followups'
    __table_args__ = (db.CheckConstraint("verdict IN ('improved', 'unchanged', 'worse')", name='ck_advisory_followup_verdict'),)
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(db.Integer, db.ForeignKey('field_observations.id'), nullable=False, unique=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    verdict = db.Column(db.String(12), nullable=False)
    note = db.Column(db.String(500), nullable=False, default='')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    observation = db.relationship('FieldObservation', back_populates='followup')


class AdvisoryTaskLink(db.Model):
    __tablename__ = 'advisory_task_links'
    __table_args__ = (db.UniqueConstraint('observation_id', 'action_code', name='uq_advisory_action_task'),)
    id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(db.Integer, db.ForeignKey('field_observations.id'), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action_code = db.Column(db.String(80), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('farm_tasks.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    observation = db.relationship('FieldObservation', back_populates='task_links')
    task = db.relationship('FarmTask')
