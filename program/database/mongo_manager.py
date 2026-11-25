# program/database_manager.py

from pymongo import MongoClient
import logging

class MongoDBManager:
    def __init__(self, uri="mongodb://mongodb:27017", db_name="steam_api_data"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.logger = logging.getLogger(__name__)
    
    def insert(self, collection, data):
        """Insert single or multiple documents"""
        col = self.db[collection]

        if isinstance(data, list):
            result = col.insert_many(data)
            self.logger.info(f"Inserted {len(result.inserted_ids)} to {collection}")
        
        else:
            result = col.insert_one(data)
            self.logger.info(f"Inserted 1 doc to {collection}")
        
        return result
    
    def export(self, data, collection, row_extractor=None):
        """
        Export data to collection
        
        Args:
            data: Raw dict/list from API
            collection: MongoDB collection name
            row_extractor: Optional lambda to transform before insert
                          If None, inserts as-is
        """
        rows = row_extractor(data) if row_extractor else data
        return self.insert(collection, rows)
    
    def close(self):
        self.client.close()