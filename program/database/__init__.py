"""
Database module for Steam API Explorer.
Handles all database connections and operations.
"""

from .mongo_manager import MongoDBManager

__all__ = ["MongoDBManager"]
