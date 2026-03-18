from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('principal','hod','student','tpo'), nullable=False, default='employee')
    phone = db.Column(db.String(15))
    avatar = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)
    reset_password_token = db.Column(db.String(255))
    reset_password_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    login_audit = db.relationship('LoginDetail', backref='user', lazy=True)


class Role(db.Model):
    __tablename__='roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

class LoginDetail(db.Model):
    __tablename__ = 'login_details'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    mspassword = db.Column(db.String(255), default='20027d8807812a0a483933752ac69085')
    accessToken = db.Column(db.String(300))
    apiToken = db.Column(db.String(250))
    authKey = db.Column(db.String(200))
    forgot_pass_token = db.Column(db.String(250))
    change_password_firsttime = db.Column(db.String(20))
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    modified_by = db.Column(db.Integer)
    modified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Student(db.Model):
    __tablename__='student'
    id=db.Column(db.Integer,nullable=False,primary_key=True)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),nullable=False)
    phone=db.Column(db.String(15),nullable=False)
    regno=db.Column(db.Integer,nullable=False)
    department=db.Column(db.String(4),nullable=False)
    sem=db.Column(db.Integer,nullable=False)
