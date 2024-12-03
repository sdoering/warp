from flask import Blueprint, request, flash, session, redirect, url_for, render_template, g
from werkzeug.security import check_password_hash
import logging
from . import utils
from .db import User, ACCOUNT_TYPE_BLOCKED, ACCOUNT_TYPE_ADMIN, ACCOUNT_TYPE_GROUP

logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__)

# NOTE:
# In this module I don't use decorators (route and before_app_request) to register
# functions in blueprint I register them after the function definition
# this exposes a raw function ,so it can be registered in alternative auth modules.
#
# BTW: both route and before_app_request are just registering a function, they return
#      unwrapped function reference however this may change in the future, so let's keep it clean


def login():
    # Clear session to force re-login
    session.clear()

    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')
        
        logger.info(f"Login attempt for user: {username}")
        
        user = User.query.filter_by(login=username).first()
        
        if user and user.account_type != ACCOUNT_TYPE_GROUP:
            if user.password is None:
                logger.warning(f"User {username} has no password set")
                flash("Wrong username or password")
                return render_template('login.html')
            
            if check_password_hash(user.password, password):
                if user.account_type == ACCOUNT_TYPE_BLOCKED:
                    logger.warning(f"Blocked user attempted login: {username}")
                    flash("Your account is blocked.")
                else:
                    logger.info(f"Successful login: {username}")
                    session['login'] = username
                    session['login_time'] = utils.now()
                    return redirect(url_for('view.index'))
            else:
                logger.warning(f"Invalid password for user: {username}")
        
        flash("Wrong username or password")
        
    return render_template('login.html')

bp.route('/login', methods=['GET', 'POST'])(login)

def logout():
    session.clear()
    return redirect(url_for('auth.login'))

bp.route('/logout')(logout)

def check_session():
    if request.blueprint == 'auth':
        return

    if request.endpoint == 'static':
        return

    login = session.get('login')

    if login is None:
        return redirect(url_for('auth.login'))

    latest_valid_time = utils.now() - 24*3600*current_app.config['SESSION_LIFETIME']
    last_login_time = session.get('login_time')

    if last_login_time is None or last_login_time < latest_valid_time:
        return redirect(url_for('auth.login'))

    # Check if user still exists and is not blocked
    user = User.query.filter_by(login=login).first()

    if not user or user.account_type >= ACCOUNT_TYPE_BLOCKED:
        return redirect(url_for('auth.login'))

    g.isAdmin = user.account_type == ACCOUNT_TYPE_ADMIN
    g.login = login

bp.before_app_request(check_session)
