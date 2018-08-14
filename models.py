from sqlalchemy.sql import func
from time import time
from confi import db
import jwt
from confi import app
import secrets

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(40))
    lastName = db.Column(db.String(40))
    email = db.Column(db.String(50))
    username = db.Column(db.String(30))
    password = db.Column(db.String(100))
    registerDate = db.Column(db.DateTime(timezone=True), server_default=func.now())
    e_verified = db.Column(db.SMALLINT, default=0, nullable=False)

    def getEmailVerificationToken(self, expires_in=604800):
        return jwt.encode({'verifyEmail':self.id}, 'wUCu3q6jjqoI3Mh5kwD7dCp4wSju-OURchpKHXLv9oY87ROs', algorithm='HS256').decode('utf-8')

    @staticmethod
    def verifyEmailToken(token):
        try:
            id = jwt.decode(token, 'wUCu3q6jjqoI3Mh5kwD7dCp4wSju-OURchpKHXLv9oY87ROs',
                            algorithms=['HS256'])['verifyEmail']
        except:
            return
        return User.query.get(id)


class Group(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
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
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    type = db.Column(db.Enum('Admin', 'Member'))
    groupName = db.Column(db.String(40))

class Lodging_Pin(db.Model):
    __tablename__ = "lodgingPins"
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    lodgeName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    rooms = db.Column(db.SMALLINT)
    description = db.Column(db.Text)
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Rest_Pin(db.Model):
    __tablename__ = "restPins"
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    restName = db.Column(db.String(40))
    description = db.Column(db.Text)
    link = db.Column(db.String(512))
    types = db.Column(db.Enum('Restaurant', 'Nightclub'))
    creator = db.Column(db.String(40))

class Transpo_Pin(db.Model):
    __tablename__ = "transpoPins"
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    transpoName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    types = db.Column(db.Enum('Flight', 'Train', 'Bus', 'Car', 'Other'))
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Activity_Pin(db.Model):
    __tablename__ = "activityPins"
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    activityName = db.Column(db.String(40))
    price = db.Column(db.Integer)
    description = db.Column(db.Text)
    types = db.Column(db.Enum('Indoor', 'Outdoor'))
    link = db.Column(db.String(512))
    creator = db.Column(db.String(40))

class Chat(db.Model):
    __tablename__ = "chats"
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    username = db.Column(db.String(30))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
