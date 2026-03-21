"""
Database model initialization and utility functions
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


# Re-export for convenience
__all__ = ["Base"]
