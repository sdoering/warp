import os
import logging
from warp import db
from warp.model import *
from warp.password_utils import generate_password_hash

# Set up logging
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Starting database initialization")
    # Create tables if they don't exist
    logger.info("Creating database tables")
    tables = [Blob, User, Group, Zone, ZoneAssign, Seat, SeatAssign, Book]
    db.database.create_tables(tables, safe=True)  # safe=True means it won't recreate existing tables
    logger.info(f"Created {len(tables)} tables successfully")

    # Check if we should skip admin user management
    skip_admin_setup = os.environ.get('WARP_SKIP_ADMIN_SETUP', '').lower() in ('true', '1', 'yes')
    
    if skip_admin_setup:
        logger.info("Skipping admin user setup as WARP_SKIP_ADMIN_SETUP is set")
        return

    # Get admin credentials from environment or config
    admin_user = os.environ.get('WARP_ADMIN_USER') or current_app.config.get('WARP_ADMIN_USER', 'wurstbrot')
    admin_password = os.environ.get('WARP_ADMIN_PASSWORD') or current_app.config.get('WARP_ADMIN_PASSWORD', 'mitSenf')
    
    logger.info(f"Setting up admin user: {admin_user}")
    logger.debug(f"Admin user source: {'environment' if os.environ.get('WARP_ADMIN_USER') else 'config'}")
        
        # Always create or update the admin user
        admin_hash = generate_password_hash(admin_password)
        
        try:
            admin = User.get(User.login == admin_user)
            logger.info(f"Found existing admin user: {admin_user}")
            admin.password = admin_hash
            admin.account_type = 10  # Admin type
            admin.save()
            logger.info(f"Successfully updated existing admin user '{admin_user}'")
        except User.DoesNotExist:
            logger.info(f"No existing admin user found, creating new user: {admin_user}")
            User.create(
                login=admin_user,
                password=admin_hash,
                name='Admin',
                account_type=10
            )
            logger.info(f"Successfully created new admin user '{admin_user}'")

if __name__ == '__main__':
    init_db()
