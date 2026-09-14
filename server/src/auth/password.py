import bcrypt
from src.config.Env import settings
class HashPassword:
    BCRYPT_ROUNDS = settings.BCRYPT_ROUNDS

    '''
    Used for Hashing Passwords
    '''
    @classmethod
    def hash_password(cls, password: str):
        password = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(cls.BCRYPT_ROUNDS))
        return hashed_password
    @classmethod
    def check_password(cls, password, hashed_password)->bool:
        if bcrypt.checkpw(password, hashed_password):
            return True
        return False