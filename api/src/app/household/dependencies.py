"""Household dependencies — resolves the one household for the current user."""

from typing import Annotated

from fastapi import Depends

from app.auth.dependencies import CurrentUser
from app.core.database import Session
from app.core.exceptions import AuthorizationError
from app.household.models import Household
from app.household.service import get_household_for_user


async def get_current_household(user: CurrentUser, session: Session) -> Household:
    household = await get_household_for_user(session, user)
    if household is None:
        raise AuthorizationError("User has no household")
    return household


CurrentHousehold = Annotated[Household, Depends(get_current_household)]
