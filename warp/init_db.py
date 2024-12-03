from warp import db
from warp.model import *
from warp.password_utils import generate_password_hash

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
            password=generate_password_hash('noneshallpass'),
            name='Admin',
            account_type=10
        )

if __name__ == '__main__':
    init_db()
