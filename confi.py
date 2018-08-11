from flask import Flask, request, session
from flask_mysqldb import MySQL
from flask_sqlalchemy import *
from flask_mail import Mail, Message
app = Flask(__name__)



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = 1
app.config['MAIL_USERNAME'] = 'biteth1979@gmail.com'
app.config['MAIL_PASSWORD'] = 'Flow!154skip'
app.config['SECRET_KEY'] = '\xa3sw\xba\xe8D;:vJL\xa3\xe9\xe4\xba\x1a\xe6\xb4\xdd\xd3r\x87\x958'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Flubber_blubber'
app.config['MYSQL_DB'] = 'flask_trip'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username = "root",
    password = "Flubber_blubber",
    hostname = "localhost",
    databasename = "flask_trip"
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


mail = Mail(app)
mysql = MySQL(app)
