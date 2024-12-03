import flask
from flask import g

from warp.db import (
    db, Zone, ZoneAssign, User,
    ZONE_ROLE_ADMIN, ZONE_ROLE_USER, ZONE_ROLE_VIEWER,
    ACCOUNT_TYPE_GROUP
)
from . import utils
from . import blob_storage

bp = flask.Blueprint('view', __name__)

@bp.context_processor
def headerDataInit():
    headerDataL = []

    zoneCursor = db.session.query(Zone.id, Zone.name)\
        .join(ZoneAssign, Zone.id == ZoneAssign.zid)\
        .filter(ZoneAssign.login == g.login)\
        .order_by(Zone.name)\
        .all()

    for z in zoneCursor:
        headerDataL.append(
            {"text": z.name, "endpoint": "view.zone", "view_args": {"zid": str(z.id)}})

    if headerDataL:
        headerDataL.insert(0,{"text": "Bookings", "endpoint": "view.bookings", "view_args": {"report":""} })

    headerDataR = [
        {"text": "Report", "endpoint": "view.bookings", "view_args": {"report": "report"} },
        {"text": "Users", "endpoint": "view.users", "view_args": {} },
        {"text": "Groups", "endpoint": "view.groups", "view_args": {} },
        {"text": "Zones", "endpoint": "view.zones", "view_args": {} }
    ]

    #generate urls and selected
    for hdata in [headerDataL,headerDataR]:

        for h in hdata:

            h['url'] = flask.url_for(h['endpoint'],**h['view_args'])
            a = flask.request.endpoint == h['endpoint']
            b = flask.request.view_args == h['view_args']
            h['active'] = flask.request.endpoint == h['endpoint'] and flask.request.view_args == h['view_args']


    return { "headerDataL": headerDataL,
             "headerDataR": headerDataR,
             'hasLogout': 'auth.logout' in flask.current_app.view_functions
    }

@bp.route("/")
def index():
    return flask.render_template('index.html')

@bp.route("/bookings/<string:report>")
@bp.route("/bookings", defaults={"report": "" })
def bookings(report):

    if report == "report" and not flask.g.isAdmin:
        flask.abort(403)

    return flask.render_template('bookings.html',
        report = (report == "report"),
        maxReportRows = flask.current_app.config['MAX_REPORT_ROWS'])

@bp.route("/zone/<zid>")
def zone(zid):

    zoneRole = db.session.query(ZoneAssign.zone_role)\
        .filter(ZoneAssign.zid == zid, ZoneAssign.login == g.login)\
        .scalar()

    if zoneRole is None:
        flask.abort(403)

    nextWeek = utils.getNextWeek()
    defaultSelectedDates = {
        "slider": [9*3600, 17*3600]
    }

    for d in nextWeek[1:]:
        if not d['isWeekend']:
            defaultSelectedDates['cb'] = [d['timestamp']]
            break

    if zoneRole <= ZONE_ROLE_ADMIN:
        zoneRole = {'isZoneAdmin': True}
    elif zoneRole <= ZONE_ROLE_USER:
        zoneRole = {}
    elif zoneRole <= ZONE_ROLE_VIEWER:
        zoneRole = {'isZoneViewer': True}
    else:
        raise Exception('Undefined role')


    return flask.render_template('zone.html',
        **zoneRole,
        zid = zid,
        nextWeek=nextWeek,
        defaultSelectedDates=defaultSelectedDates)

@bp.route("/zone/image/<zid>")
def zoneImage(zid):

    if not flask.g.isAdmin:

        zoneRole = UserToZoneRoles.select(UserToZoneRoles.zone_role) \
                                .where( (UserToZoneRoles.zid == zid) & (UserToZoneRoles.login == flask.g.login) ) \
                                .scalar()
        if zoneRole is None:
            flask.abort(403)

    blobIdQuery = db.session.query(Zone.iid.label('id')).filter(Zone.id == zid)

    return blob_storage.createBlobResponse(blobIdQuery=blobIdQuery)


@bp.route("/users")
def users():

    if not flask.g.isAdmin:
        flask.abort(403)

    return flask.render_template('users.html')

@bp.route("/groups")
def groups():

    if not flask.g.isAdmin:
        flask.abort(403)

    return flask.render_template('groups.html')

@bp.route("/zones")
def zones():

    if not flask.g.isAdmin:
        flask.abort(403)

    return flask.render_template('zones.html')


@bp.route("/groups/assign/<group_login>")
def groupAssign(group_login):

    if not flask.g.isAdmin:
        flask.abort(403)

    groupName = db.session.query(User.name)\
        .filter(User.login == group_login, User.account_type >= ACCOUNT_TYPE_GROUP)\
        .scalar()

    if groupName is None:
        flask.abort(404)

    returnURL = flask.request.args.get('return',flask.url_for('view.groups'))

    return flask.render_template('group_assign.html',
                    groupLogin = group_login,
                    groupName = groupName,
                    returnURL = returnURL)


@bp.route("/zones/assign/<zid>")
def zoneAssign(zid):

    if not flask.g.isAdmin:
        flask.abort(403)

    zoneName = db.session.query(Zone.name)\
        .filter(Zone.id == zid)\
        .scalar()

    if zoneName is None:
        flask.abort(404)

    returnURL = flask.request.args.get('return',flask.url_for('view.zones'))

    return flask.render_template('zone_assign.html',
                    zoneName = zoneName,
                    zid = zid,
                    returnURL = returnURL)

@bp.route("/zones/modify/<zid>")
def zoneModify(zid):

    if not flask.g.isAdmin:
        flask.abort(403)

    returnURL = flask.request.args.get('return',flask.url_for('view.zones'))

    return flask.render_template('zone_modify.html',
                    zid = zid,
                    returnURL = returnURL)

@bp.route("/up")
def health():
    return '', 200
