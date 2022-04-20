""" Expose PV data """

import logging
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Security
from fastapi_auth0 import Auth0User
from nowcasting_datamodel.models import PVYield
from nowcasting_datamodel.read.read_pv import get_latest_pv_yield, get_pv_systems
from sqlalchemy.orm.session import Session

from database import get_session_pv
from auth_utils import auth

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/pv_latest", response_model=List[PVYield], dependencies=[Depends(auth.implicit_scheme)])
def get_latest_pv_data(session: Session = Depends(get_session_pv), user: Auth0User = Security(auth.get_user)) -> List[PVYield]:
    """Get Latest PV data from specific pv sites

    Only provide PV data received within the last 1 hour
    """

    logger.debug(f'Getting PV latest data for {user}')

    # get latest pv data
    pv_systems_sql = get_pv_systems(session=session)
    pv_yields_sql = get_latest_pv_yield(session=session, pv_systems=pv_systems_sql)

    # remove any data older than 1 hours
    now_minus_1_hours = datetime.utcnow() - timedelta(hours=1)
    pv_yields_sql = [
        pv_yield_sql
        for pv_yield_sql in pv_yields_sql
        if pv_yield_sql.datetime_utc >= now_minus_1_hours
    ]

    # convert to pydantic
    pv_yields = [PVYield.from_orm(pv_yield_sql) for pv_yield_sql in pv_yields_sql]

    return pv_yields
