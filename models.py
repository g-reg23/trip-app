from sqlalchemy.sql import func
from time import time
from confi import db
import jwt
from confi import app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(40))
    lastName = db.Column(db.String(40))
    email = db.Column(db.String(50))
    username = db.Column(db.String(30))
    password = db.Column(db.String(100))
    registerDate = db.Column(db.DateTime(timezone=True), server_default=func.now())
    e_verified = db.Column(db.SMALLINT, default=0, nullable=False)

    def getProfile(user):
        return User.query.filter(User.username==user).first()

    def getProfileById(userId):
        return User.query.filter(User.id==userId).first()


    def getEmailVerificationToken(self, expires_in=604800):
        return jwt.encode({'verifyEmail':self.id, 'exp': time() + expires_in}, 'wUCu3q6jjqoI3Mh5kwD7dCp4wSju-OURchpKHXLv9oY87ROs', algorithm='HS256').decode('utf-8')

    @staticmethod
    def verifyEmailToken(token):
        try:
            idOne = jwt.decode(token, 'wUCu3q6jjqoI3Mh5kwD7dCp4wSju-OURchpKHXLv9oY87ROs', algorithms=['HS256'])['verifyEmail']
        except:
            return
        return User.query.get(idOne)

    def getNewPassToken(self, expires_in=600):
        return jwt.encode({'newPass':self.id, 'exp': time() + expires_in}, 'EzVyo9hoxqWeHRjFDGpw17P5CENp8Dmt6XWdAEsO0CYhFtKX', algorithm='HS256').decode('utf-8')

    @staticmethod
    def verifyNewPassToken(token):
        try:
            idTwo = jwt.decode(token, 'EzVyo9hoxqWeHRjFDGpw17P5CENp8Dmt6XWdAEsO0CYhFtKX', algorithms=['HS256'])['newPass']
        except:
            return
        return User.query.get(idTwo)

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
    users = []

    def getGroupInfo(groupId):
        return Group.query.filter(Group.id==groupId).first()


    def addOnlineUser(self, user):
        self.users.append(user)

    def removeOnlineUser(self, user):
        self.users.remove(user)

    @staticmethod
    def deleteGroup(group):
        db.session.delete(group)
        db.session.commit()
        userGroup = User_Group.query.filter(User_Group.groupId==group.id).all()
        for i in userGroup:
            db.session.delete(i)
            db.commit()
        return

class User_Group(db.Model):
    __tablename__ = "users_groups"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    status = db.Column(db.Enum('Pending', 'Accepted'))
    type = db.Column(db.Enum('Admin', 'Member'))
    groupName = db.Column(db.String(40))

    def getUserGroups(userId):
        return User_Group.query.filter(User_Group.userId==userId).all()
    def getMembers(groupId):
        return User_Group.query.filter(User_Group.groupId==groupId).all()

class Pending_Member(db.Model):
    __tablename__ = "pending_members"
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    type = db.Column(db.Enum('Request', 'Invite'))

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

    @staticmethod
    def getChatHist(groupNum):
        return Chat.query.filter(Chat.groupId==groupNum).all()

class Calendar_Note(db.Model):
    __tablename__ = 'calendarNotes'
    id = db.Column(db.Integer, primary_key=True)
    groupId = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"))
    name = db.Column(db.String(30))
    date = db.Column(db.String(40))
    username = db.Column(db.String(30))

    def getNotes(groupId):
        return Calendar_Note.query.filter(Calendar_Note.groupId==groupId)
