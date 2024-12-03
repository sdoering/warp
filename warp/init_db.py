import os
import logging
from flask import current_app
from warp.db import DB, Users, ACCOUNT_TYPE_ADMIN
from werkzeug.security import generate_password_hash

# Set up logging
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Starting database initialization")

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
        # Check if admin exists using raw query
        admin_exists = Users.select().where(Users.login == admin_user).exists()
        
        if admin_exists:
            logger.info(f"Found existing admin user: {admin_user}")
            Users.update({
                Users.password: admin_hash,
                Users.account_type: ACCOUNT_TYPE_ADMIN
            }).where(Users.login == admin_user).execute()
            logger.info(f"Successfully updated existing admin user '{admin_user}'")
        else:
            logger.info(f"No existing admin user found, creating new user: {admin_user}")
            Users.insert({
                Users.login: admin_user,
                Users.password: admin_hash,
                Users.name: 'Admin',
                Users.account_type: ACCOUNT_TYPE_ADMIN
            }).execute()
            logger.info(f"Successfully created new admin user '{admin_user}'")
            
    except Exception as e:
        logger.error(f"Error managing admin user: {e}")
        raise

if __name__ == '__main__':
    init_db()
