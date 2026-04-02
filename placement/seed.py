# populating data into db

from app import app, bcrypt
from models import (
    db, User, Role, LoginDetail, Student
)
from datetime import datetime, timezone, date

def hash_pw(plain: str) -> str:
    """Hash the password using bcrypt and decode to string for storage."""
    return bcrypt.generate_password_hash(plain).decode("utf-8")

def utcnow():
    return datetime.now(timezone.utc)

def seed_data(reset=False):
    with app.app_context():
        print("Starting database seeding...")

        try:
            if reset:
                print("Dropping all existing tables...")
                db.drop_all()

            # Create database tables if they don't exist
            db.create_all()
            print("Database tables verified/created.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            return

        # 1. Seed Roles
        roles_to_seed = ['principal', 'hod', 'student', 'tpo']
        print("Seeding roles...")
        for role_name in roles_to_seed:
            existing_role = Role.query.filter_by(name=role_name).first()
            if not existing_role:
                db.session.add(Role(name=role_name))
                print(f" [+] Added role: {role_name}")
            else:
                print(f" [.] Role already exists: {role_name}")
        db.session.commit()

        # 2. Realistic User Data
        # Format: (full_name, email, password, role, phone, avatar)
        users_data = [
            # Principal
            ('Dr. Rohan Verma', 'rohanv@gmail.com', 'Rverma123', 'principal', '9876543210', None),
            # HODs
            ('Dr. Jai Shankar', 'shankarh@gmail.com', 'Jsha@34', 'hod', '9870001112', None),
            ('Prof. Meera Nair', 'nairh@gmail.com', 'Nmeer@54', 'hod', '9870001113', None),
            # TPO
            ('Mr. Sudhakar Rao', 'sudhakart@gmail.com', 'Srao@78', 'tpo', '9871234567', None),
        ]

        # Students Data with Extended Profile Info
        students_data = [
            {
                'full_name': 'Amit Kumar', 
                'email': 'amit.kumar@student.nims.edu', 
                'password': 'Student@123', 
                'phone': '9111222333',
                'regno': 20221001,
                'department': 'CS',
                'sem': 6,
                'gender': 'Male',
                'dob': date(2003, 5, 15),
                'batch': '2022-25',
                'cgpa': 8.5,
                'backlogs': 0,
                'address': 'Patna, Bihar',
                'tenth_percent': 90.0,
                'twelfth_percent': 85.5,
                'skills': 'Python, SQL, HTML, CSS'
            },
            {
                'full_name': 'Faiz', 
                'email': 'mdfaizan2526201@gmail.com', 
                'password': 'Student@123', 
                'phone': '9222333444',
                'regno': 20221002,
                'department': 'BCA',
                'sem': 4,
                'gender': 'male',
                'dob': date(2004, 8, 20),
                'batch': '2023-26',
                'cgpa': 9.1,
                'backlogs': 0,
                'address': 'Siwan, Bihar',
                'tenth_percent': 92.5,
                'twelfth_percent': 88.0,
                'skills': 'Java, JS, React'
            },
            {
                'full_name': 'preethi pandey', 
                'email': 'preethip.2026@gmail.com', 
                'password': 'Student@123', 
                'phone': '9333444555',
                'regno': 20221003,
                'department': 'IT',
                'sem': 8,
                'gender': 'Female',
                'dob': date(2002, 11, 10),
                'batch': '2021-24',
                'cgpa': 7.8,
                'backlogs': 1,
                'address': 'Gaya, Bihar',
                'tenth_percent': 85.0,
                'twelfth_percent': 80.0,
                'skills': 'PHP, Laravel, MySQL'
            }
        ]

        print("Seeding users...")
        # Add Staff/Admin users
        for full_name, email, password, role, phone, avatar in users_data:
            existing_user = User.query.filter_by(email=email).first()
            if not existing_user:
                new_user = User(
                    full_name=full_name,
                    email=email,
                    password=hash_pw(password),
                    role=role,
                    phone=phone,
                    avatar=avatar
                )
                db.session.add(new_user)
                print(f" [+] Added user: {email} ({role})")
            else:
                 print(f" [.] User already exists: {email}")

        # Add Students
        for s_data in students_data:
            existing_user = User.query.filter_by(email=s_data['email']).first()
            if not existing_user:
                new_user = User(
                    full_name=s_data['full_name'],
                    email=s_data['email'],
                    password=hash_pw(s_data['password']),
                    role='student',
                    phone=s_data['phone']
                )
                db.session.add(new_user)
                db.session.flush() # flush to get user id

                # Create Student Profile
                student_profile = Student(
                    student_id=new_user.id,
                    name=s_data['full_name'],
                    email=s_data['email'],
                    phone=s_data['phone'],
                    regno=s_data['regno'],
                    department=s_data['department'],
                    sem=s_data['sem'],
                    gender=s_data.get('gender'),
                    dob=s_data.get('dob'),
                    batch=s_data.get('batch'),
                    cgpa=s_data.get('cgpa'),
                    backlogs=s_data.get('backlogs'),
                    address=s_data.get('address'),
                    tenth_percent=s_data.get('tenth_percent'),
                    twelfth_percent=s_data.get('twelfth_percent'),
                    skills=s_data.get('skills')
                )
                db.session.add(student_profile)
                print(f" [+] Added student: {s_data['email']} (RegNo: {s_data['regno']})")
            else:
                print(f" [.] Student already exists: {s_data['email']}")

        try:
            db.session.commit()
            print("Database seeded successfully!")
            print("Note: LoginDetail table remains empty. It will be populated upon user login.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing seed data: {e}")

if __name__ == '__main__':
    import sys
    reset_flag = '--reset' in sys.argv
    seed_data(reset=reset_flag)
