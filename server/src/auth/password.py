import bcrypt
from src.config.Env import settings
import logging
logger = logging.getLogger(__name__)
class HashPassword:
    BCRYPT_ROUNDS = settings.BCRYPT_ROUNDS

    '''
    Used for Hashing Passwords
    '''
    @classmethod
    def hash_password(cls, password: str):
        try:
            password = password.encode('utf-8')
            hashed_bytes = bcrypt.hashpw(password, bcrypt.gensalt(rounds=cls.BCRYPT_ROUNDS))
            return hashed_bytes.decode('utf-8')
        except Exception as e:
            logger.error("Password Hashing Failed")
            raise e
    '''
    Used to check if the password is correct or not 
    '''
    @classmethod
    def check_password(cls, password:str, hashed_password:str)->bool:
        """
            Verifies a plain text password against a stored hashed password string.
        """
        try:
            password_byte = password.encode('utf-8')
            hashed_password_byte = hashed_password.encode('utf-8')

            if bcrypt.checkpw(password_byte, hashed_password_byte):
                return True
            return False

        except Exception as e:
            logger.error("Password Checking Failed")
            raise e