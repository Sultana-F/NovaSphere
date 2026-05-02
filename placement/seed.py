# populating data into db
import pandas as pd
from app import app, bcrypt
from models import (
    ValidateStudent, db, User, Role, LoginDetail, Student, JobPosting, Application
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


# seed data into validatestudent table by taking excel file as input present in the same directory in static folder
def seed_validatestudent_from_excel(file_path='static/uploads/studentdataBCA.xlsx'):
    with app.app_context():
        try:
            # engine='openpyxl' is usually required for .xlsx files
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names: remove leading/trailing spaces and convert to lowercase
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            if 'regno' not in df.columns or 'phone' not in df.columns:
                print(f"Error: Excel file must have 'phone' and 'regno' columns. Found: {list(df.columns)}")
                return

            print("Seeding ValidateStudent from Excel...")
            for index, row in df.iterrows():
                # Handle potential float conversions from Excel (e.g. 123.0 -> "123")
                regno = str(int(row['regno'])) if isinstance(row['regno'], (int, float)) else str(row['regno'])
                phone = str(int(row['phone'])) if isinstance(row['phone'], (int, float)) else str(row['phone'])

                existing_entry = ValidateStudent.query.filter_by(regno=regno).first()
                if not existing_entry:
                    new_entry = ValidateStudent(regno=regno,phone=phone)
                    db.session.add(new_entry)
                    print(f" [+] Added ValidateStudent: RegNo {regno}, Phone {phone}")
                else:
                    print(f" [.] ValidateStudent already exists: RegNo {regno}")
            db.session.commit()
            print("ValidateStudent table seeded successfully from Excel!")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding ValidateStudent from Excel: {e}")


# Import historical placement data from Excel files for analytics
# Expected columns: SLNO, STUDENT NAME, COMPANY PLACED, COURSE, BATCH
def seed_historical_placements(file_path='static/uploads/historical_placements.xlsx'):
    """
    Import historical placement data from Excel to populate analytics charts.
    Creates Student records and Application records with 'selected' status.
    """
    with app.app_context():
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Clean column names: remove leading/trailing spaces and convert to lowercase
            df.columns = [str(c).strip().lower() for c in df.columns]
            
# Expected columns: slno/sl no, student name, company placed, course, batch
            # Normalize column names: handle variations like 'sl no' -> 'slno'
            df.columns = [str(c).strip().lower().replace(' ', ' ') for c in df.columns]
            
            # Map variations
            col_mapping = {
                'sl no': 'slno',
                'slno': 'slno',
                'sl no.': 'slno'
            }
            df.columns = [col_mapping.get(c, c) for c in df.columns]
            
            required_cols = ['slno', 'student name', 'company placed', 'course', 'batch']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                print(f"Error: Excel file missing columns: {missing_cols}")
                print(f"Expected columns: {required_cols}")
                print(f"Found columns: {list(df.columns)}")
                return

            print("Seeding historical placement data...")
            placements_added = 0
            jobs_created = set()

            for index, row in df.iterrows():
                try:
                    student_name = str(row['student name']).strip() if pd.notna(row['student name']) else ''
                    company_placed = str(row['company placed']).strip() if pd.notna(row['company placed']) else ''
                    course = str(row['course']).strip() if pd.notna(row['course']) else ''
                    batch = str(row['batch']).strip() if pd.notna(row['batch']) else ''
                    
                    if not student_name or not company_placed or not course or not batch:
                        print(f" [.] Skipping row {index + 2}: Missing required data")
                        continue

                    # Generate a unique email for the student
                    email = f"{student_name.lower().replace(' ', '.')}_{batch}@student.nims.edu"
                    
# Generate regno based on batch format (e.g., "2022-25" -> "U16NB25S0001")
                    # Format: U + 2-digit year (last 2) + NB + 2-digit batch year + S + 4-digit number
                    batch_year = batch.split('-')[0][2:] if '-' in batch else batch[-2:]
                    batch_end = batch.split('-')[1] if '-' in batch else '21'
                    regno = f"U{batch_year}NB{batch_end}S{placements_added + 1:04d}"

                    # Check if student already exists
                    existing_student = Student.query.filter_by(email=email).first()
                    if not existing_student:
                        # Create User first
                        new_user = User(
                            full_name=student_name,
                            email=email,
                            password=hash_pw(f'Student@{batch_year}'),
                            role='student',
                            phone='9999999999'
                        )
                        db.session.add(new_user)
                        db.session.flush()

                        # Create Student Profile
                        student = Student(
                            student_id=new_user.id,
                            name=student_name,
                            email=email,
                            phone='9999999999',
                            regno=regno,
                            department=course,
                            sem=8,  # Final semester for placed students
                            batch=batch,
                            cgpa=7.0,  # Default CGPA
                            backlogs=0,
                            address='N/A',
                            tenth_percent=80.0,
                            twelfth_percent=80.0
                        )
                        db.session.add(student)
                    else:
                        student = existing_student

                    # Create or get JobPosting for the company
                    job = JobPosting.query.filter_by(company_name=company_placed).first()
                    if not job:
                        job = JobPosting(
                            company_name=company_placed,
                            job_role='TBD',
                            job_description=f'Placed at {company_placed} via campus placement',
                            eligibility_criteria='N/A',
                            salary_package='N/A',
                            location='N/A',
                            deadline=datetime(2020, 1, 1),
                            form_link='',
                            status='closed',
                            min_cgpa=0.0,
                            max_backlogs=0
                        )
                        db.session.add(job)
                        db.session.flush()
                        jobs_created.add(company_placed)

                    # Create Application with 'selected' status
                    existing_app = Application.query.filter_by(
                        job_id=job.id, 
                        student_id=student.id
                    ).first()
                    
                    if not existing_app:
                        application = Application(
                            job_id=job.id,
                            student_id=student.id,
                            status='selected'
                        )
                        db.session.add(application)
                        placements_added += 1
                        print(f" [+] Added: {student_name} -> {company_placed} (Batch: {batch})")
                    else:
                        print(f" [.] Application already exists: {student_name} -> {company_placed}")

                except Exception as row_error:
                    print(f" [.] Error processing row {index + 2}: {row_error}")
                    continue

            db.session.commit()
            print(f"Historical placement data seeded successfully!")
            print(f"Total placements added: {placements_added}")
            print(f"New companies added: {len(jobs_created)}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding historical placements: {e}")


if __name__ == '__main__':
    import sys
    reset_flag = '--reset' in sys.argv
    seed_data(reset=reset_flag)
    seed_validatestudent_from_excel()
    
    # Optionally import historical data if file exists
    import os
    historical_file = 'static/uploads/placementsdetails.xlsx'
    if os.path.exists(historical_file):
        seed_historical_placements(historical_file)
    else:
        print(f"Note: Historical placement file not found at {historical_file}")
        print("To enable analytics, place your Excel file with columns:")
        print("  - SLNO")
        print("  - STUDENT NAME")
        print("  - COMPANY PLACED")
        print("  - COURSE")
        print("  - BATCH")
