#populating data into db

from app import app
from models import (
    db, User, Role, LoginDetail, Student
)
from datetime import datetime, timezone


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
            # Note: The database 'nimsdb' must already exist in MySQL
            db.create_all()
            print("Database tables verified/created.")
        except Exception as e:
            print(f"Error initializing database: {e}")
            print("Make sure the database 'nimsdb' exists in your MySQL server.")
            return

        # Seed Roles
        # Valid roles must match the Enum defined in models.py
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

        # Seed Users
        # 'role' values must match Enum: 'principal', 'hod', 'student', 'tpo'
        # 'username' is stored in LoginDetail; User uses full_name + email
        users = [
            {
                'full_name': 'Admin Principal',
                'email': 'Rohan@gmail.com',
                'username': 'Rohan verma',
                'password': 'Rohan@56',
                'role': 'principal'
            },
            {
                'full_name': 'HOD User',
                'email': 'Jai@gmail.com',
                'username': 'jai Shankar',
                'password': 'jai@123',
                'role': 'hod'
            },
            {
                'full_name': 'Student One',
                'email': 'student1@nims.edu',
                'username': 'student1',
                'password': 'studentpassword1',
                'role': 'student',
                'regno': 20221001,
                'department': 'BCA',
                'sem': 1,
                'phone': '9000000001'
            },
            {
                'full_name': 'Student Two',
                'email': 'student2@nims.edu',
                'username': 'student2',
                'password': 'studentpassword2',
                'role': 'student',
                'regno': 20221002,
                'department': 'BCA',
                'sem': 2,
                'phone': '9000000002'
            },
            {
                'full_name': 'TPO Officer',
                'email':'sudhakar67@gamil.com',
                'username': 'Sudhakar',
                'password': 'Su65@12',
                'role': 'tpo'
            },
        ]

        print("Seeding users and login details...")
        for user_data in users:
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                new_user = User(
                    full_name=user_data['full_name'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=user_data['role']
                )
                db.session.add(new_user)
                db.session.flush()  # flush to get new_user.id before commit

                # Seed the corresponding LoginDetail record
                login_detail = LoginDetail(
                    user_id=new_user.id,
                    username=user_data['username'],
                    password=user_data['password'],
                )
                db.session.add(login_detail)

                # For student-role users, also create a Student record
                if user_data['role'] == 'student':
                    existing_student = Student.query.filter_by(email=user_data['email']).first()
                    if not existing_student:
                        student_record = Student(
                            name=user_data['full_name'],
                            email=user_data['email'],
                            phone=user_data.get('phone', '0000000000'),
                            regno=user_data['regno'],
                            department=user_data.get('department', 'BCA'),
                            sem=user_data.get('sem', 1)
                        )
                        db.session.add(student_record)
                        print(f"     [+] Linked Student record for regno: {user_data['regno']}")

                print(f" [+] Added user: {user_data['username']} ({user_data['role']})")
            else:
                print(f" [.] User already exists: {user_data['email']}")

        try:
            db.session.commit()
            print("Database seeded successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing seed data: {e}")


if __name__ == '__main__':
    import sys
    reset_flag = '--reset' in sys.argv
    seed_data(reset=reset_flag)
