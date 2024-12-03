import os
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

    # Check if we should skip admin user management
    skip_admin_setup = os.environ.get('WARP_SKIP_ADMIN_SETUP', '').lower() in ('true', '1', 'yes')
    
    if not skip_admin_setup:
        admin_user = os.environ.get('WARP_ADMIN_USER', 'admin')
        admin_password = os.environ.get('WARP_ADMIN_PASSWORD', 'changeme')
        
        try:
            admin = User.get(User.login == admin_user)
            # Update existing admin user if WARP_FORCE_ADMIN_UPDATE is set
            if os.environ.get('WARP_FORCE_ADMIN_UPDATE', '').lower() in ('true', '1', 'yes'):
                admin.password = generate_password_hash(admin_password)
                admin.account_type = 10  # Ensure admin privileges
                admin.save()
                print(f"Updated admin user '{admin_user}'")
        except User.DoesNotExist:
            # Create new admin user
            User.create(
                login=admin_user,
                password=generate_password_hash(admin_password),
                name='Admin',
                account_type=10
            )
            print(f"Created new admin user '{admin_user}'")

if __name__ == '__main__':
    init_db()
