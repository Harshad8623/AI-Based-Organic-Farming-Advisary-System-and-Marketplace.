"""Shared freshness checks for saved plans and tasks derived from those plans."""
from datetime import timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func

from advisory_models import FieldObservation
from models import db


def latest_report_keys(farmer_id, field_ids):
    """Fetch only the latest timestamp/id for each owned field, without report JSON."""
    if not field_ids:
        return {}
    ranked = db.session.query(
        FieldObservation.field_id.label('field_id'), FieldObservation.id.label('id'),
        FieldObservation.created_at.label('created_at'),
        func.row_number().over(partition_by=FieldObservation.field_id,
            order_by=(FieldObservation.created_at.desc(), FieldObservation.id.desc())).label('position'),
    ).filter(FieldObservation.farmer_id == farmer_id,
             FieldObservation.field_id.in_(field_ids)).subquery()
    return {row.field_id: (row.created_at, row.id) for row in db.session.query(
        ranked.c.field_id, ranked.c.created_at, ranked.c.id).filter(ranked.c.position == 1).all()}


def _utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def report_is_stale(row, today, latest_key=None):
    """Use the same conditions on the original report and every derived task."""
    age = (today - _utc(row.created_at).astimezone(ZoneInfo('Asia/Kolkata')).date()).days
    try:
        review_days = max(1, min(7, int(row.report_data.get('next_review_days', 1))))
    except (ValueError, TypeError):
        review_days = 1
    current = row.field.context_snapshot()
    changed = any(current.get(key) != row.field_snapshot.get(key)
                  for key in ('crop', 'stage', 'soil', 'irrigation', 'planting_date', 'area_m2'))
    superseded = latest_key is not None and (_utc(latest_key[0]), latest_key[1]) > (_utc(row.created_at), row.id)
    return row.field.archived or age >= review_days or changed or superseded
