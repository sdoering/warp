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
    zone_group = db.Column(db.String, index=True)
    name = db.Column(db.String)
    iid = db.Column(db.Integer)
    
    # Relationships
    assignments = db.relationship('ZoneAssign', backref='zone', lazy='dynamic')
    seats = db.relationship('Seat', backref='zone', lazy='dynamic')

class ZoneAssign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zid = db.Column(db.Integer, db.ForeignKey('zone.id'), index=True)
    login = db.Column(db.String, index=True)
    zone_role = db.Column(db.Integer)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zid = db.Column(db.Integer, db.ForeignKey('zone.id'), index=True)
    name = db.Column(db.String)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    enabled = db.Column(db.Boolean, default=True)
    
    # Relationships
    assignments = db.relationship('SeatAssign', backref='seat', lazy='dynamic')
    bookings = db.relationship('Book', backref='seat', lazy='dynamic')

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



