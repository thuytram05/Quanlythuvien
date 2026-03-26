from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary, os

app = Flask(__name__)
app.secret_key = '&(^&*^&*^U*HJBJKHJLHKJHK&*%^&5786985646858'
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Abc123@127.0.0.1:3307/qltvdb?charset=utf8mb4"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:13112005@localhost/qltvdb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8
app.config['UPLOAD_FOLDER'] = 'static/uploads/avatars'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
if not os.path.exists(upload_path):
    os.makedirs(upload_path)

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

cloudinary.config(cloud_name='dxxwcby8l',
api_key='792844686918347',
api_secret='T8ys_Z9zaKSqmKWa4K1RY6DXUJg')