"""Batch public_id lookups — avoids N+1 queries in response builders.

Every response builder that turns FK `id`s into `public_id`s for the wire format
should go through :func:`batch_public_ids` once per foreign table instead of
issuing a per-row SELECT.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def batch_public_ids(
    session: AsyncSession,
    model: Any,
    ids: set[int],
) -> dict[int, str]:
    """Return `{id: public_id}` for the given ids. Empty input → empty dict (no query)."""
    if not ids:
        return {}
    result = await session.execute(
        select(model.id, model.public_id).where(model.id.in_(ids))
    )
    return {row[0]: row[1] for row in result}
