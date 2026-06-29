"""Import all models here so SQLAlchemy's registry knows about every table.

Importing this package (`import app.models`) guarantees all model classes are
registered on `Base.metadata` before we call `create_all()` or resolve
relationships by class name.
"""

from app.models.incident import Incident
from app.models.log import Log
from app.models.report import Report
from app.models.user import User

__all__ = ["User", "Incident", "Log", "Report"]
