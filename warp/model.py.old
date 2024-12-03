from peewee import *
from warp.db import DB

class BaseModel(Model):
    class Meta:
        database = DB

class Blob(BaseModel):
    id = AutoField()
    mimetype = CharField()
    data = BlobField()
    etag = CharField()

class User(BaseModel):
    login = CharField(primary_key=True)
    password = CharField(null=True)
    name = CharField()
    account_type = IntegerField()

class Group(BaseModel):
    group = CharField()
    login = CharField()

class Zone(BaseModel):
    id = AutoField()
    zone_group = CharField()
    name = CharField()
    iid = IntegerField()

class ZoneAssign(BaseModel):
    zid = ForeignKeyField(Zone, backref='assignments')
    login = CharField()
    zone_role = IntegerField()

class Seat(BaseModel):
    id = AutoField() 
    zid = ForeignKeyField(Zone, backref='seats')
    name = CharField()
    x = IntegerField()
    y = IntegerField()
    enabled = BooleanField(default=True)

class SeatAssign(BaseModel):
    sid = ForeignKeyField(Seat, backref='assignments')
    login = CharField()

class Book(BaseModel):
    id = AutoField()
    login = CharField()
    sid = ForeignKeyField(Seat, backref='bookings')
    fromts = IntegerField()
    tots = IntegerField()
