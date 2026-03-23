from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


# ─── Auth Model (Used for login across roles) ──────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('principal', 'hod', 'student', 'tpo'), nullable=False)
    phone = db.Column(db.String(15))
    avatar = db.Column(db.String(255))
    
    # Session Management
    last_login = db.Column(db.DateTime)
    reset_password_token = db.Column(db.String(255))
    reset_password_expires = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to the detailed student record
    student_profile = db.relationship('Student', back_populates='user', uselist=False, cascade="all, delete-orphan")


# ─── Role Model (Used as a lookup) ──────────────────────────────────────────

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)


# ─── Login Audit Details ─────────────────────────────────────────────────────

class LoginDetail(db.Model):
    __tablename__ = 'login_details'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    accessToken = db.Column(db.String(300))
    apiToken = db.Column(db.String(250))
    authKey = db.Column(db.String(200))
    forgot_pass_token = db.Column(db.String(250))
    change_password_firsttime = db.Column(db.String(20))
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    modified_by = db.Column(db.Integer)
    modified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ─── Detailed Student Model ──────────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Core Data
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    regno = db.Column(db.Integer, nullable=False, unique=True)
    department = db.Column(db.String(50), nullable=False)
    sem = db.Column(db.Integer, nullable=False)
    
    # Additional Profile Details
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    batch = db.Column(db.String(10))     # e.g., '2022-25'
    cgpa = db.Column(db.Float, default=0.0)
    backlogs = db.Column(db.Integer, default=0)
    
    # Professional & Personal Info
    address = db.Column(db.Text)
    tenth_percent = db.Column(db.Float)
    twelfth_percent = db.Column(db.Float)
    skills = db.Column(db.Text)          # Comma separated or text block
    resume = db.Column(db.String(255))   # File path or URL
    
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Backref to User
    user = db.relationship('User', back_populates='student_profile')
