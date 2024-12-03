from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()

# Constants
ACCOUNT_TYPE_ADMIN = 10
ACCOUNT_TYPE_USER = 20
ACCOUNT_TYPE_BLOCKED = 90
ACCOUNT_TYPE_GROUP = 100

ZONE_ROLE_ADMIN = 10
ZONE_ROLE_USER = 20
ZONE_ROLE_VIEWER = 30

class User(db.Model):
    login = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=True)
    name = db.Column(db.String)
    account_type = db.Column(db.Integer)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String)
    login = db.Column(db.String)

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_group = db.Column(db.String)
    name = db.Column(db.String)
    iid = db.Column(db.Integer)

class ZoneAssign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zid = db.Column(db.Integer, db.ForeignKey('zone.id'))
    login = db.Column(db.String)
    zone_role = db.Column(db.Integer)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zid = db.Column(db.Integer, db.ForeignKey('zone.id'))
    name = db.Column(db.String)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    enabled = db.Column(db.Boolean, default=True)

class SeatAssign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('seat.id'))
    login = db.Column(db.String)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String)
    sid = db.Column(db.Integer, db.ForeignKey('seat.id'))
    fromts = db.Column(db.Integer)
    tots = db.Column(db.Integer)

class Blob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mimetype = db.Column(db.String)
    data = db.Column(db.LargeBinary)
    etag = db.Column(db.String)

def init_db(app):
    """Initialize database and ensure admin user exists if configured"""
    logger.info("Initializing database")
    
    db_path = app.config.get('DATABASE')
    logger.debug(f"Using database: {db_path}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        logger.info("Database tables created/verified")

        # Handle admin user if configured
        admin_user = app.config.get('ADMIN_USER')
        admin_pass = app.config.get('ADMIN_PASSWORD')
        
        if admin_user and admin_pass:
            logger.info(f"Configuring admin user: {admin_user}")
            
            user = User.query.filter_by(login=admin_user).first()
            if not user:
                logger.info("Creating new admin user")
                user = User(
                    login=admin_user,
                    password=generate_password_hash(admin_pass),
                    name='Admin',
                    account_type=ACCOUNT_TYPE_ADMIN
                )
                db.session.add(user)
            elif app.config.get('FORCE_ADMIN_UPDATE'):
                logger.info("Updating existing admin password")
                user.password = generate_password_hash(admin_pass)
            
            try:
                db.session.commit()
                logger.info("Admin user configuration successful")
            except Exception as e:
                logger.error(f"Failed to configure admin user: {e}")
                db.session.rollback()
                raise

def init(app):

    global DB

    connStr = app.config['DATABASE']
    connArgs = app.config['DATABASE_ARGS'] if 'DATABASE_ARGS' in app.config else {}

    # Handle SQLite connection parameters specially
    if connStr.startswith('sqlite'):
        # Remove busy_timeout from connArgs if it exists, as it's not supported
        connArgs.pop('busy_timeout', None)
        DB = playhouse.db_url.connect(connStr, autoconnect=False, thread_safe=True, **connArgs)
    else:
        DB = playhouse.db_url.connect(connStr, autoconnect=False, thread_safe=True, **connArgs)

    Blobs.bind(DB)
    Users.bind(DB)
    Groups.bind(DB)
    Seat.bind(DB)
    Zone.bind(DB)
    ZoneAssign.bind(DB)
    Book.bind(DB)
    SeatAssign.bind(DB)
    UserToZoneRoles.bind(DB)

    app.before_request(_connect)
    app.teardown_request(_disconnect)

    if 'DATABASE_INIT_SCRIPT' in app.config:

        commandParams = {"help": "Create and initialize database.", 'callback': with_appcontext(partial(initDB,True)) }
        cmd = click.Command('init-db', **commandParams)
        app.cli.add_command(cmd)

    if '--help' not in sys.argv[1:] and 'init-db' not in sys.argv[1:]:
        with app.app_context():
            initDB()

def update_admin_credentials():
    """Update admin credentials from environment variables if configured"""
    admin_user = os.environ.get('WARP_ADMIN_USER') or current_app.config.get('WARP_ADMIN_USER')
    admin_pass = os.environ.get('WARP_ADMIN_PASSWORD') or current_app.config.get('WARP_ADMIN_PASSWORD')
    
    if not admin_user or not admin_pass:
        logger.info("No admin credentials configured in environment")
        return
        
    logger.info(f"Updating credentials for admin user: {admin_user}")
    
    # Generate new password hash
    new_hash = generate_password_hash(admin_pass)
    logger.debug(f"Generated new password hash: {new_hash}")
    
    with DB.atomic():
        # First check if admin user exists
        exists = Users.select().where(
            (Users.login == admin_user) & 
            (Users.account_type == ACCOUNT_TYPE_ADMIN)
        ).exists()
        
        if not exists:
            logger.warning(f"Admin user {admin_user} not found in database")
            return
            
        updated = Users.update({
            Users.password: new_hash
        }).where(
            (Users.login == admin_user) & 
            (Users.account_type == ACCOUNT_TYPE_ADMIN)
        ).execute()
        
        if updated:
            logger.info("Admin credentials updated successfully")
        else:
            logger.error("Failed to update admin credentials")

def initDB(force = False):

    initScripts = current_app.config.get('DATABASE_INIT_SCRIPT')

    if not initScripts:
        print("DATABASE_INIT_SCRIPT not defined ")
        return

    if isinstance(initScripts,str):
        initScripts = [ initScripts ]

    retries = current_app.config['DATABASE_INIT_RETRIES']
    retDelay = current_app.config['DATABASE_INIT_RETRIES_DELAY']

    if retries < 1:
        retries = 1

    while True:

        try:

            with DB:
                # SQLite needs to explicitly enable foreign key support
                DB.execute_sql('PRAGMA foreign_keys = ON;')

                if not force:
                    try:
                        DB.execute_sql(f"CREATE TABLE {_INITIALIZED_TABLE}();")
                    except DatabaseError:
                        # database already initialized
                        return

                print(f'Initializing DB force={force}')

                for file in initScripts:
                    print(f'Executing SQL: {file}')

                    with current_app.open_resource(file) as f:
                        sql = f.read().decode('utf8')
                        # Split the SQL file into individual statements
                        statements = sql.split(';')
                        for statement in statements:
                            if statement.strip():
                                DB.execute_sql(statement + ';')

                # in case it is cleaned up in the above scripts (or force == True)
                DB.execute_sql(f"CREATE TABLE IF NOT EXISTS {_INITIALIZED_TABLE}();")
                
                # Initialize database with tables and admin user
                initialize_database()
                print('The database initialized.')
                update_admin_credentials()
                break

        except OperationalError:

            retries -= 1
            if retries == 0:
                print(f"ERROR: Cannot connect to the database.", file=sys.stderr, flush=True)
                raise

            print(f"Database connection error, waiting {retDelay} second(s).", file=sys.stderr, flush=True)
            sleep(retDelay)
            print(f'Retrying ({retries}).', file=sys.stderr, flush=True)
