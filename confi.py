from flask import Flask, request, session
from flask_mysqldb import MySQL
from flask_sqlalchemy import *
from flask_mail import Mail, Message
import os
app = Flask(__name__)



app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = 1
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['SECRET_KEY'] = ''
# app.config['SECRET_KEY'] = os.urandom(36)

# upload_folder = "C:/Users/gztau/Documents/Atom_Flask/group_uploads"
# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
#
# app.config['UPLOAD_FOLDER'] = upload_folder
# app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = ''
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username = "root",
    password = "",
    hostname = "localhost",
    databasename = ""
)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


mail = Mail(app)
mysql = MySQL(app)
