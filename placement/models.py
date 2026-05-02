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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,)
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
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Core Data
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    regno = db.Column(db.VARCHAR(12), nullable=False, unique=True)
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
    skills = db.Column(db.Text)
    resume = db.Column(db.String(255))
        
    # Metadata
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Backref to User
    user = db.relationship('User', back_populates='student_profile') # Establishes a one-to-one relationship with the User model

    @property
    def profile_completion(self):
        """Calculates percentage of profile completed based on non-null fields."""
        fields = [
            self.gender, self.dob, self.batch, self.cgpa, 
            self.address, self.tenth_percent, self.twelfth_percent, 
            self.skills, self.resume
        ]
        completed = len([f for f in fields if f is not None and f != ""])
        return int((completed / len(fields)) * 100)

    @property
    def next_step(self):
        """Suggests the next action for the student."""
        if not self.skills:
            return "Add your technical skills to stand out."
        if not self.resume:
            return "Upload your resume for applications."
        if self.profile_completion < 100:
            return "Complete your profile details."
        return "Apply for your first job!"

# ─── Job Posting Model ───────────────────────────────────────────────────────

class JobPosting(db.Model):
    __tablename__ = 'job_post'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    eligibility_criteria = db.Column(db.Text)
    salary_package = db.Column(db.String(50))
    location = db.Column(db.String(100))
    deadline = db.Column(db.DateTime, nullable=False)
    form_link = db.Column(db.String(500)) # Primary Form link (e.g. Google Form)
    secondary_form_link = db.Column(db.String(500)) # Secondary Form link
    status = db.Column(db.Enum('open', 'closed', 'cancelled'), default='open')  # Job posting status
    min_cgpa = db.Column(db.Float, default=0.0)  # Minimum CGPA requirement
    max_backlogs = db.Column(db.Integer, default=0)  # Maximum allowed backlogs
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id')) # TPO ID


# ─── Application Model ───────────────────────────────────────────────────────

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_post.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.Enum('pending', 'shortlisted', 'interviewed', 'rejected', 'selected'), default='pending')
    secondary_data = db.Column(db.Text) # To store ID/Details from external form
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = db.relationship('JobPosting', back_populates='applications')
    student = db.relationship('Student', backref='job_applications') # Backref to access all applications of a student



class ValidateStudent(db.Model):
    __tablename__ = 'validatestudent'
    id = db.Column(db.Integer, primary_key=True)
    regno = db.Column(db.VARCHAR(12), nullable=True, unique=True)
    phone = db.Column(db.String(15), nullable=False)

# ─── Announcement Model (Notice Board) ───────────────────────────────────────

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum('general', 'urgent', 'drive', 'results'), default='general')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id')) # TPO/Admin ID

    # Relationship to User for posted_by
    author = db.relationship('User', backref='announcements')

# Update JobPosting model to include the back_populates
JobPosting.applications = db.relationship('Application', back_populates='job', cascade="all, delete-orphan")

# ─── Approved Staff Model ──────────────────────────────────────────────────────
class ApprovedStaff(db.Model):
    __tablename__ = 'approved_staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), nullable=False) # 'tpo' or 'hod'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('User', backref=db.backref('approved_staff_profile', uselist=False, cascade='all, delete-orphan'))

