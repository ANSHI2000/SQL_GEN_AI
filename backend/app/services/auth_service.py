import bcrypt
from passlib.context import CryptContext

# Try bcrypt first (new), fallback to passlib (old hashes)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    """Verify a password against its hash (supports both bcrypt and passlib formats)"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Try bcrypt first (new format)
    try:
        if bcrypt.checkpw(password_bytes, hashed_bytes):
            return True
    except Exception:
        pass
    
    # Fallback to passlib (old format)
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception:
        pass
    
    return False