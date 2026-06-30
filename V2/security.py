# security.py
import keyring
import hashlib
import os
from cryptography.fernet import Fernet


# ✅ Store credentials in system keychain (not in code!)
def save_credentials(email, password):
    keyring.set_password("StratoMail", email, password)


def load_credentials(email):
    return keyring.get_password("StratoMail", email)


def delete_credentials(email):
    keyring.delete_password("StratoMail", email)


# ✅ Encrypt local config
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)
    return key


def load_key():
    if not os.path.exists("secret.key"):
        return generate_key()
    with open("secret.key", "rb") as f:
        return f.read()


def encrypt(data: str) -> bytes:
    f = Fernet(load_key())
    return f.encrypt(data.encode())


def decrypt(data: bytes) -> str:
    f = Fernet(load_key())
    return f.decrypt(data).decode()