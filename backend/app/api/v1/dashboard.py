from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

#---------------------------------------------
# Dashboard endpoints with month/year query parameters
#---------------------------------------------

@router.get("/dashboard/properties")
async def list_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Lists only the properties belonging to the current user's tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    from app.core.database_pool import DatabasePool
    from sqlalchemy import text

    db_pool = DatabasePool()
    await db_pool.initialize()

    if not db_pool.session_factory:
        raise HTTPException(status_code=503, detail="Database unavailable")

    async with db_pool.get_session() as session:
        result = await session.execute(
            text("SELECT id, name, timezone FROM properties WHERE tenant_id = :tenant_id ORDER BY id"),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()

    return {
        "properties": [
            {"id": row.id, "name": row.name, "timezone": row.timezone} for row in rows
        ]
    }

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    #---------------------------------------------
    #accept month/year query params 
    #---------------------------------------------
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    now = datetime.now(timezone.utc)
    resolved_month = month or now.month
    resolved_year = year or now.year
    if not 1 <= resolved_month <= 12:
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")

    revenue_data = await get_revenue_summary(property_id, tenant_id, resolved_month, resolved_year)
    total_revenue = Decimal(str(revenue_data['total'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return {
        "property_id": revenue_data['property_id'],
        #---------------------------------------------
        #return month/year in response
        #---------------------------------------------
        "month": resolved_month,
        "year": resolved_year,
        "total_revenue": float(total_revenue),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
