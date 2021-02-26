import bcrypt


def encode_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def check_password(input_password: str, db_password: bytes) -> bool:
    return bcrypt.checkpw(input_password.encode(), db_password)


def validate_password(password: str):
    return len(password) > 8
