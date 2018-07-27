from sqlalchemy.sql import func
from config import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(40))
    lastName = db.Column(db.String(40))
    email = db.Column(db.String(50))
    username = db.Column(db.String(30))
    registerDate = db.Column(db.DateTime(timezone=True), server_default=func.now())
    e_verified = db.Column(db.SMALLINT, default=0, nullable=False)

class Group(db.Model):
    __tablename__ = "groups"
    groupId = db.Column(db.Integer, primary_key=True)
    groupName = db.Column(db.String(40))
    location = db.Column(db.String(40))
    startDate = db.Column(db.Date())
    endDate = db.Column(db.Date())
    admin = db.Column(db.String(30))
    password = db.Column(db.String(100))
    description = db.Column(db.Text)
    createDate = db.Column(db.DateTime(timezone=True), server_default=func.now())

class User_Group(db.Model):
    __tablename__ = "users_groups"
    idNum = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id"))
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))

class Lodging_Pin(db.Model):
    __tablename__ = "rentalPins"
    lodgeNum = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))
    lodgeName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    rooms = db.Column(db.SMALLINT)
    description = db.Column(db.Text)
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Rest_Pin(db.Model):
    __tablename__ = "restPins"
    restNum = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))
    restName = db.Column(db.String(40))
    description = db.Column(db.Text)
    link = db.Column(db.String(512))
    types = db.Column(db.Enum('Restaurant', 'Nightclub'))
    creator = db.Column(db.String(40))

class Transpo_Pin(db.Model):
    __tablename__ = "transpoPins"
    transpoNum = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))
    transpoName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    types = db.Column(db.Enum('Flight', 'Train', 'Bus', 'Car', 'Other'))
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Activity_Pin(db.Model):
    __tablename__ = "activityPins"
    transpoNum = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))
    activityName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    types = db.Column(db.Enum('Indoor', 'Outdoor'))
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Chat(db.Model):
    __tablename__ = "chats"
    chatNum = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.groupId"))
    username = db.Column(db.String(30))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
