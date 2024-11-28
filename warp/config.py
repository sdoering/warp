import json
import os

__all__ = ['initConfig']

class DefaultSettings(object):

    LANGUAGE_FILE="i18n/en.js"

    # after how many days force user to re-login (note that it is not a session timeout)
    SESSION_LIFETIME = 1

    # for how many weeks in advance users can book a seat
    # (after the current week)
    WEEKS_IN_ADVANCE = 1

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # maximum size of uploaded map file
    MAX_MAP_SIZE = 2 * 1024 * 1024

    MAX_REPORT_ROWS = 5000

    DATABASE_INIT_SCRIPT = "sql/schema.sql"

    # number of connection retries to DB on initialization
    DATABASE_INIT_RETRIES = 10
    # delay between retries
    DATABASE_INIT_RETRIES_DELAY = 2

    # SQLite specific settings
    SQLITE_TIMEOUT = 30  # Timeout in seconds for SQLite operations
    SQLITE_BUSY_TIMEOUT = 5000  # Busy timeout in milliseconds
    
    # Modify this to handle both PostgreSQL and SQLite init scripts
    DATABASE_INIT_SCRIPT = "sql/schema_sqlite.sql"  # or keep as is if using same schema

    # LDAP defaults
    LDAP_AUTH_TYPE = "SIMPLE"
    LDAP_STARTTLS = True
    LDAP_VALIDATE_CERT = False
    LDAP_USER_NAME_ATTRIBUTE = "cn"
    LDAP_USER_SEARCH_FILTER_TEMPLATE = "(objectClass=person)"
    LDAP_GROUP_SEARCH_FILTER_TEMPLATE = "(&(memberUid={login})(cn={group}))"
    LDAP_GROUP_MAP = [ [None,None] ]
    LDAP_GROUP_STRICT_MAPPING = False
    LDAP_EXCLUDED_USERS = []

    ### LDAP variables to be configured
    # AUTH_LDAP = True
    # LDAP_SERVER_URL = "ldap://server:port"
    # LDAP_USER_TEMPLATE = "uid={login},ou=users,dc=example,dc=org"
    # LDAP_USER_SEARCH_BASE
    # LDAP_GROUP_SEARCH_BASE = "ou=groups,dc=example,dc=org"
    # LDAP_TLS_VERSION (optional)
    # LDAP_TLS_CIPHERS (optional)

    # these settings are available, but should not have default value
    # set them up in DevelopmentSettings or via environment
    # SECRET_KEY
    # DATABASE
    # DATABASE_ARGS

    # mellon settings
    # AUTH_MELLON
    # MELLON_ENDPOINT
    # MELLON_DEFAULT_GROUP

class DevelopmentSettings(DefaultSettings):

    # Comment out or remove PostgreSQL connection
    # DATABASE = "postgresql://postgres:postgres_password@127.0.0.1:5432/postgres"

    # Use SQLite instead
    DATABASE = "sqlite:///warp.db"
    DATABASE_ARGS = {
        "pragmas": {
            "foreign_keys": "ON",
            "journal_mode": "WAL",  # Better concurrency support
            "cache_size": -32000,   # 32MB cache
            "synchronous": "NORMAL" # Good balance between safety and performance
        }
    }

    DATABASE_INIT_SCRIPT = [
        "sql/clean_db.sql",
        "sql/schema.sql",
        "sql/sample_data.sql"
    ]

    SECRET_KEY = b'change_me'


class ProductionSettings(DefaultSettings):

    # use mellon (Apache SAML module) for authentication
    #AUTH_MELLON = False
    #MELLON_ENDPOINT = "/sp"
    #MELLON_DEFAULT_GROUP = "everybody"

    # this is intentionally empty, as in production
    # DATABASE and SECRET_KEY should be passed via ENV
    # as WARP_SECRET_KEY and WARP_DATABASE
    pass

def readEnvironmentSettings(app):

    PREFIX="WARP_"

    res = {}
    for key,val in os.environ.items():
        if key.startswith(PREFIX):
            try:
                val = json.loads(val.lower())       # try to parse any valid json type
            except json.decoder.JSONDecodeError:
                pass                                # fallback to string (no change)
            res[key.removeprefix(PREFIX)] = val

    app.config.update(res)

def get_database_args(app):
    """Get database arguments based on database type"""
    db_url = app.config['DATABASE']
    db_args = app.config.get('DATABASE_ARGS', {})

    if db_url.startswith('sqlite:'):
        # Ensure SQLite-specific settings are properly set
        pragmas = db_args.get('pragmas', {})
        if 'foreign_keys' not in pragmas:
            pragmas['foreign_keys'] = 'ON'
        if 'journal_mode' not in pragmas:
            pragmas['journal_mode'] = 'WAL'
        db_args['pragmas'] = pragmas
        
        # Add timeout settings
        db_args['timeout'] = app.config.get('SQLITE_TIMEOUT', 30)
        db_args['busy_timeout'] = app.config.get('SQLITE_BUSY_TIMEOUT', 5000)

    return db_args

def initConfig(app):
    if app.env != 'production':
        app.config.from_object(DevelopmentSettings)
    else:
        app.config.from_object(ProductionSettings)

    readEnvironmentSettings(app)

    if app.config.get('SECRET_KEY',None) is None:
        raise Exception('SECRET_KEY must be defined or passed via WARP_SECRET_KEY environment variable')
    if app.config.get('DATABASE',None) is None:
        raise Exception('DATABASE must be defined or passed via WARP_DATABASE environment variable')

    # Add database arguments processing
    app.config['DATABASE_ARGS'] = get_database_args(app)

# def initConfig(app):

#     if app.env != 'production':
#         app.config.from_object(DevelopmentSettings)
#     else:
#         app.config.from_object(ProductionSettings)

#     readEnvironmentSettings(app)

#     if app.config.get('SECRET_KEY',None) is None:
#         raise Exception('SECRET_KEY must be defined or passed via WARP_SECRET_KEY environment variable')
#     if app.config.get('DATABASE',None) is None:
#         raise Exception('DATABASE must be defined or passed via WARP_DATABASE environment variable')
