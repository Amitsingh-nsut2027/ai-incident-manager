"""The SQLAlchemy Declarative Base.

Every ORM model (User, Incident, Log, Report) inherits from `Base`. SQLAlchemy
uses this shared base to keep a registry of all tables, which is how it can
later create them all at once and resolve relationships between them.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
