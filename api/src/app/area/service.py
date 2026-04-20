"""Area service — seeds defaults on household creation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.area.models import Area

# Matches mobile/components/household/data.ts:76-82
DEFAULT_AREAS = [
    {"slug": "kids", "name": "Kids", "color": "#ff7eb9"},
    {"slug": "house", "name": "House", "color": "#7bd389"},
    {"slug": "money", "name": "Money", "color": "#f4b860"},
    {"slug": "trip", "name": "Travel", "color": "#6fb1fc"},
    {"slug": "health", "name": "Health", "color": "#c88cff"},
]


async def seed_default_areas(session: AsyncSession, household_id: int) -> None:
    for a in DEFAULT_AREAS:
        session.add(
            Area(household_id=household_id, name=a["name"], color=a["color"], slug=a["slug"])
        )
    await session.flush()
