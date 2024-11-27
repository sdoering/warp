from warp import db
from warp.model import *
from werkzeug.security import generate_password_hash

def init_db():
    # Create tables if they don't exist
    db.database.create_tables([
        Blob,
        User,
        Group,
        Zone,
        ZoneAssign,
        Seat,
        SeatAssign,
        Book
    ], safe=True)  # safe=True means it won't recreate existing tables

    # Check if admin user exists, if not create it
    try:
        User.get(User.login == 'admin')
    except User.DoesNotExist:
        User.create(
            login='admin',
            password='pbkdf2:sha256:260000$LdN4KNf6xzb0XlSu$810ca4acafd3b6955e6ebc39d2edafd582c8020ab87fd56e3cede1bfebb7df03',
            name='Admin',
            account_type=10
        )

if __name__ == '__main__':
    init_db()