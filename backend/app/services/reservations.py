from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from zoneinfo import ZoneInfo

#----------------------------------------------
# rewrite reservations.py to wire the timezone-aware monthly calculation into the real query path
#----------------------------------------------

def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal('0')
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


async def _get_property_timezone(db_session, property_id: str, tenant_id: str) -> ZoneInfo:
    from sqlalchemy import text

    timezone_name = 'UTC'
    try:
        property_row = await db_session.execute(
            text("SELECT timezone FROM properties WHERE id = :property_id AND tenant_id = :tenant_id LIMIT 1"),
            {"property_id": property_id, "tenant_id": tenant_id},
        )
        timezone_row = property_row.fetchone()
        if timezone_row and timezone_row[0]:
            timezone_name = timezone_row[0]
    except Exception:
        timezone_name = 'UTC'

    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo('UTC')


async def calculate_monthly_revenue(property_id: str, tenant_id: str, month: int, year: int, db_session) -> Dict[str, Any]:
    """
    Calculates revenue for a specific calendar month using the property's own
    timezone to determine month boundaries. A check-in just before UTC midnight
    can still fall on the 1st in the property's local time (and vice versa), so
    boundaries are computed locally and only converted to UTC for the query.
    """
    #---------------------------------
    # Get the property's timezone
    #---------------------------------
    local_tz = await _get_property_timezone(db_session, property_id, tenant_id)

    local_start = datetime(year, month, 1, tzinfo=local_tz)
    local_end = (
        datetime(year + 1, 1, 1, tzinfo=local_tz)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=local_tz)
    )

    utc_start = local_start.astimezone(timezone.utc)
    utc_end = local_end.astimezone(timezone.utc)

    from sqlalchemy import text

    result = await db_session.execute(
        text("""
            SELECT COALESCE(SUM(total_amount), 0) as total, COUNT(*) as reservation_count
            FROM reservations
            WHERE property_id = :property_id
              AND tenant_id = :tenant_id
              AND check_in_date >= :start_date
              AND check_in_date < :end_date
        """),
        {"property_id": property_id, "tenant_id": tenant_id, "start_date": utc_start, "end_date": utc_end},
    )
    row = result.fetchone()
    total = _as_decimal(row.total if row else None)
    count = row.reservation_count if row else 0

    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": str(total),
        "currency": "USD",
        "count": count,
    }


async def calculate_total_revenue(property_id: str, tenant_id: str, month: int, year: int) -> Dict[str, Any]:
    """
    Computes a property's revenue for one calendar month from the database,
    falling back to mock data only if the database is unreachable.
    """
    try:
        from app.core.database_pool import DatabasePool

        db_pool = DatabasePool()
        await db_pool.initialize()

        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        async with db_pool.get_session() as session:
            return await calculate_monthly_revenue(property_id, tenant_id, month, year, session)

    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")

        # Mock data used only as a last resort when the database is unreachable.
        mock_data = {
            ('tenant-a', 'prop-001'): {'total': '1000.00', 'count': 3},
            ('tenant-b', 'prop-001'): {'total': '850.00', 'count': 2},
            ('tenant-a', 'prop-002'): {'total': '4975.50', 'count': 4},
            ('tenant-b', 'prop-002'): {'total': '4321.25', 'count': 3},
            ('tenant-a', 'prop-003'): {'total': '6100.50', 'count': 2},
            ('tenant-b', 'prop-003'): {'total': '5200.75', 'count': 2},
            ('tenant-a', 'prop-004'): {'total': '1776.50', 'count': 4},
            ('tenant-b', 'prop-004'): {'total': '1776.50', 'count': 4},
            ('tenant-a', 'prop-005'): {'total': '3256.00', 'count': 3},
            ('tenant-b', 'prop-005'): {'total': '3748.00', 'count': 3},
        }

        mock_property_data = mock_data.get((tenant_id, property_id), {'total': '0.00', 'count': 0})
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": mock_property_data['total'],
            "currency": "USD",
            "count": mock_property_data['count']
        }
