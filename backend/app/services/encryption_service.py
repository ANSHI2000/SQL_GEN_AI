from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

# Generate or load encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    # Save to .env file automatically
    with open('.env', 'a') as f:
        f.write(f'\nENCRYPTION_KEY={ENCRYPTION_KEY}\n')
    print(f"✅ Generated new encryption key and saved to .env file")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_password(password: str) -> str:
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return cipher_suite.decrypt(encrypted_password.encode()).decode()