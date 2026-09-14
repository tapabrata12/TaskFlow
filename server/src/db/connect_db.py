from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure
from src.config.Env import settings
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MongoDB:
    _client = None
    _db = None

    @classmethod
    def connect_to_db(cls):
        pass

    @classmethod
    def create_connection(cls):
        URL = settings.MONGODB_URL
        if not URL:
            raise ConfigurationError("MONGO String not found!")

        MONGO_MAX_POOL_SIZE = settings.MONGO_MAX_POOL_SIZE
        if not MONGO_MAX_POOL_SIZE:
            raise ConfigurationError("MONGO_MAX_POOL_SIZE not found!")

        MONGO_MIN_POOL_SIZE = settings.MONGO_MIN_POOL_SIZE
        if not MONGO_MIN_POOL_SIZE:
            raise ConfigurationError("MONGO_MIN_POOL_SIZE not found!")
        MONGO_TIMEOUT_MS = settings.MONGO_TIMEOUT_MS
        if not MONGO_TIMEOUT_MS:
            raise ConfigurationError("MONGO_TIMEOUT_MS not found!")

        DATABASE_NAME = settings.DATABASE_NAME
        if not DATABASE_NAME:
            raise ConfigurationError("DATABASE_NAME not found!")
        try:

            cls._client = MongoClient(URL, maxPoolSize= MONGO_MAX_POOL_SIZE, minPoolSize= MONGO_MIN_POOL_SIZE, serverSelectionTimeoutMS = MONGO_TIMEOUT_MS)
            cls._db = cls._client[DATABASE_NAME]

            logger.info("Successfully connected to MongoDB server ✅")
            return cls._client

        except (ConnectionFailure, ConfigurationError) as e:
            logger.critical(f"Failed to connect to MongoDB server ❌")
            cls._client = None
            cls._db = None
            raise e


    @classmethod
    def get_db(cls):
        if cls._db:
            return cls._db
        try:
            cls.connect_to_db()
            return cls._db
        except (ConnectionFailure, ConfigurationError) as e:
            logger.critical(f"Failed to connect to MongoDB server ❌")
            cls._db = None
            cls._client = None
            raise e

    @classmethod
    def close_connection(cls):
        try:
            if cls._client:
                cls._client.close()
                cls._client = None
                cls._db = None
            logger.info("MongoDB connection closed")
        except (ConfigurationError, ConnectionFailure) as e:
            logger.critical(f"Failed to close MongoDB connection ✅")
            raise e