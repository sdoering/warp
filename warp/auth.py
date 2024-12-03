import flask
import logging
import scrypt
import base64
from warp.db import *
from . import utils

logger = logging.getLogger(__name__)
bp = flask.Blueprint('auth', __name__)

# NOTE:
# In this module I don't use decorators (route and before_app_request) to register
# functions in blueprint I register them after the function definition
# this exposes a raw function ,so it can be registered in alternative auth modules.
#
# BTW: both route and before_app_request are just registering a function, they return
#      unwrapped function reference however this may change in the future, so let's keep it clean


def login():

    # clear session to force re-login
    # we should not do it via logout as in case of SSO
    # we will logout from SSO, and we just want to issue
    # an extra request to SSO
    flask.session.clear()

    if flask.request.method == 'POST':
        username = flask.request.form.get('login')
        password = flask.request.form.get('password')
        
        logger.info(f"Login attempt for user: {username}")
        
        c = Users.select().where((Users.login == username) & (Users.account_type != ACCOUNT_TYPE_GROUP))
        
        logger.debug(f"Found {len(c)} matching users")
        
        if len(c) == 1:
            logger.debug(f"User found, stored password hash: {c[0]['password']}")
            
            if c[0]['password'] is None:
                logger.warning(f"User {u} has no password set")
                flask.flash("Wrong username or password")
                return flask.render_template('login.html')
            
            try:
                # Parse stored hash format: scrypt:N:r:p$salt$hash
                hash_parts = c[0]['password'].split('$')
                if len(hash_parts) != 3:
                    raise ValueError("Invalid hash format")
                
                params = hash_parts[0].split(':')
                if len(params) != 4 or params[0] != 'scrypt':
                    raise ValueError("Invalid hash parameters")
                
                N = int(params[1])
                r = int(params[2])
                p = int(params[3])
                salt = hash_parts[1].encode()
                stored_hash = base64.b64decode(hash_parts[2])
                
                # Calculate hash of provided password
                calculated_hash = scrypt.hash(password.encode('utf-8'), base64.b64decode(salt), N, r, p)
                
                logger.debug(f"Salt (base64): {salt.decode()}")
                logger.debug(f"Stored hash (hex): {stored_hash.hex()}")
                logger.debug(f"Calculated hash (hex): {calculated_hash.hex()}")
                
                # Compare raw hash bytes
                is_valid = calculated_hash == stored_hash
                
                logger.debug(f"Hash verification completed")
                logger.debug(f"Password verification result: {is_valid}")
            except Exception as e:
                logger.error(f"Password verification error: {e}")
                is_valid = False
            
            if is_valid:
                account_type = c[0]['account_type']
                if account_type == ACCOUNT_TYPE_BLOCKED:
                    flask.flash("Your account is blocked.")
                else:
                    flask.session['login'] = c[0]['login']
                    flask.session['login_time'] = utils.now()
                    return flask.redirect(flask.url_for('view.index'))

        else:
            flask.flash("Wrong username or password")

    return flask.render_template('login.html')

bp.route('/login', methods=['GET', 'POST'])(login)

def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for('auth.login'))

bp.route('/logout')(logout)

def session():

    if flask.request.blueprint == 'auth':
        return

    if flask.request.endpoint == 'static':
        return

    login = flask.session.get('login')

    if login is None:
        return flask.redirect(
            flask.url_for('auth.login'))

    latestValidSessionTime = utils.now() - 24*3600*flask.current_app.config['SESSION_LIFETIME']
    lastLoginTime = flask.session.get('login_time')

    if lastLoginTime is None or lastLoginTime < latestValidSessionTime:
        return flask.redirect(
            flask.url_for('auth.login'))

    # check if user still exists and if it is not blocked
    c = Users.select(Users.account_type).where(Users.login == login)

    if len(c) != 1 or c[0]['account_type'] >= ACCOUNT_TYPE_BLOCKED:
        return flask.redirect(
            flask.url_for('auth.login'))

    flask.g.isAdmin = c[0]['account_type'] == ACCOUNT_TYPE_ADMIN
    flask.g.login = login


bp.before_app_request(session)
