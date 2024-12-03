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
        # Get admin credentials from environment or config
        admin_user = os.environ.get('WARP_ADMIN_USER') or current_app.config.get('WARP_ADMIN_USER', 'wurstbrot')
        admin_password = os.environ.get('WARP_ADMIN_PASSWORD') or current_app.config.get('WARP_ADMIN_PASSWORD', 'mitSenf')
        
        print(f"Setting up admin user: {admin_user}")
        
        # Always create or update the admin user
        admin_hash = generate_password_hash(admin_password)
        
        try:
            admin = User.get(User.login == admin_user)
            admin.password = admin_hash
            admin.account_type = 10  # Admin type
            admin.save()
            print(f"Updated existing admin user '{admin_user}'")
        except User.DoesNotExist:
            User.create(
                login=admin_user,
                password=admin_hash,
                name='Admin',
                account_type=10
            )
            print(f"Created new admin user '{admin_user}'")

if __name__ == '__main__':
    init_db()
