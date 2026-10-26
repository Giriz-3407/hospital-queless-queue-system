from flask_cors import CORS
from app.database.connection import mongo_manager

cors = CORS()

__all__ = ["cors", "mongo_manager"]
