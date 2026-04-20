"""Magic-link auth routes."""

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.auth.magic_link.schemas import MagicLinkRequest, MagicLinkVerifyRequest
from app.auth.magic_link.service import (
    consume_magic_link,
    create_magic_link,
    resolve_user_for_magic_link,
)
from app.auth.routes import issue_token_pair, set_cookies_on_response
from app.auth.schemas import CookieTokenResponse
from app.core.database import Session
from app.household.models import Household
from app.household.service import attach_user_to_household, create_household_for_user

router = APIRouter(prefix="/auth/magic-link", tags=["auth"])


@router.post("/request", status_code=202)
async def request_magic_link(body: MagicLinkRequest) -> dict[str, str]:
    await create_magic_link(email=body.email, name=body.name)
    return {"message": "Check your email for a sign-in link"}


@router.post("/verify", response_model=CookieTokenResponse)
async def verify_magic_link(
    body: MagicLinkVerifyRequest,
    response: Response,
    session: Session,
) -> CookieTokenResponse:
    payload = await consume_magic_link(body.token)
    user, _ = await resolve_user_for_magic_link(session, payload)

    if payload.household_id is not None:
        result = await session.execute(
            select(Household).where(Household.id == payload.household_id)
        )
        household = result.scalar_one_or_none()
        if household is not None:
            await attach_user_to_household(
                session, user, household, member_public_id=payload.member_public_id
            )
    else:
        from app.household.service import get_household_for_user

        existing = await get_household_for_user(session, user)
        if existing is None:
            household = await create_household_for_user(session, user)
            from app.area.service import seed_default_areas

            await seed_default_areas(session, household.id)

    token_pair = await issue_token_pair(session, user)
    return set_cookies_on_response(response, token_pair)
