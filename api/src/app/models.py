"""Aggregate model imports for Alembic auto-discovery."""

from app.area.models import Area  # noqa: F401
from app.auth.models import RefreshToken, User  # noqa: F401
from app.household.models import Household, HouseholdMember, HouseholdMembership  # noqa: F401
from app.project.models import Project  # noqa: F401
from app.task.models import Task, TaskComment  # noqa: F401
