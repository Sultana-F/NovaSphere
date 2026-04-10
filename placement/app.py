from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Role, LoginDetail, Student, JobPosting, Application
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    get_jti, JWTManager, set_access_cookies, unset_jwt_cookies, decode_token,get_jwt
)

from functools import wraps
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
load_dotenv()
from logicemail import  mail,send_email
import os
from datetime import datetime, timezone, timedelta
import re
import pandas as pd
from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet




app = Flask(__name__)
app.config['SECRET_KEY'] = 'MYSUPERKEYOFBCAfolderhelpingtosecuretheapp123!@#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://nims:Nims2019@localhost/nimsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'mysupersecretkeyforjwthelperingtosecuretheappofbcafolderplaceholdervalue123!@#'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # For simplicity in this dev environment

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS')
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER')

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Token revocation blacklist
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklist

#initialize mail,db
mail.init_app(app)
db.init_app(app)


# ─── Role → Dashboard mapping ───────────────────────────────────────────────

ROLE_DASHBOARD = {
    'principal': 'admin',        # existing admin_dashboard.html
    'hod':       'hod_dashboard',
    'tpo':       'tpo_dashboard',
    'student':   'student_dashboard',
}


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    from flask_jwt_extended import decode_token
    token = request.cookies.get('access_token_cookie')
    user = None
    if token:
        try:
            payload = decode_token(token)
            user = payload['sub']
        except Exception:
            pass
    return render_template('home.html', user=user)


@app.route('/user')
def loginpage():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('studentReg.html')






# ── Student Login ────────────────────────────────────────────────────────────
@app.route('/login/student', methods=['POST'])
def login_student():
    regno    = request.form.get('regno', '').strip()
    password = request.form.get('password', '').strip()

    if not regno or not password:
        flash('Please enter registration number and password.', 'danger')
        return redirect(url_for('loginpage'))

    # Look up by regno in Student table
    student = Student.query.filter_by(regno=regno).first()
    if not student:
        flash('Invalid registration number.', 'danger')
        return redirect(url_for('loginpage'))

    # Fetch the corresponding User record via email
    user = User.query.filter_by(email=student.email, role='student').first()
   #verify password
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash('Invalid registration number or password.', 'danger')
        return redirect(url_for('loginpage'))
    # Issue JWT and redirect to student dashboard
    access_token = create_access_token(
        identity=str(user.email),
        additional_claims={'role': 'student', 'regno': regno}
    )
    record_login_details(user)
    response = redirect(url_for('student_dashboard'))
    set_access_cookies(response, access_token)
    return response


# ── Admin / Staff Login ──────────────────────────────────────────────────────
@app.route('/login/admin', methods=['POST'])
def login_admin():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not email or not password:
        flash('Please enter email and password.', 'danger')
        return redirect(url_for('loginpage') + '?tab=admin')

    user = User.query.filter_by(email=email).first()
    # Verify user exists and password matches
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash('Invalid email or password.', 'danger')
        return redirect(url_for('loginpage') + '?tab=admin')
    if user.role == 'student':
        flash('Students must use the Student Login tab.', 'danger')
        return redirect(url_for('loginpage'))

    # Issue JWT with role claim
    access_token = create_access_token(
        identity=str(user.email),
        additional_claims={'role': user.role}
    )
    record_login_details(user)

    # Redirect to the appropriate role dashboard
    dashboard_route = ROLE_DASHBOARD.get(user.role, 'index')
    response = redirect(url_for(dashboard_route))
    set_access_cookies(response, access_token)
    return response


# ── Auth helper decorator ────────────────────────────────────────────────────
def login_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request, get_jwt
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if roles and claims.get('role') not in roles:
                    flash('You are not authorized to access that page.', 'danger')
                    return redirect(url_for('loginpage'))
            except Exception:
                flash('Please log in to continue.', 'danger')
                return redirect(url_for('loginpage'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def record_login_details(user):
    jti = get_jti(create_access_token(identity=str(user.email)))
    try:
        audit = LoginDetail(
            user_id=user.id,
            username=user.email,
            password=user.password,
            accessToken=str(jti),
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error recording login details: {e}")
    return jti







#reset password with token based email
@app.route('/reset_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot password.html')
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate a password reset token (JWT with short expiry)
            reset_token = create_access_token(
                identity=str(user.email),
                additional_claims={'role': user.role},
                expires_delta=timedelta(minutes=30)  # Token valid for 30 minutes
            )
            reset_link = url_for('reset_password', token=reset_token, _external=True) #
            send_email(
                subject='Password Reset Request',
                recipients=[user.email],
                body=f'Click the link to reset your password: {reset_link}'
            )
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('No account found with that email address.', 'danger')
        return redirect(url_for('loginpage') + '?tab=admin')
    return render_template('forgot password.html')


#on click rest link, verify token and allow password reset
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        payload = decode_token(token)
        email = payload['sub']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Invalid or expired token.', 'danger')
            return redirect(url_for('loginpage') + '?tab=admin')
    except Exception as e:
        print(f"Token decode error: {e}")
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('loginpage') + '?tab=admin')
    if request.method == 'GET':
        return render_template('reset_password.html', token=token)

    if request.method == 'POST':
        new_password = request.form.get('newpassword', '').strip()
        if new_password:
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8') 
            db.session.commit()
            flash('Your password has been reset successfully. Please log in.', 'success')
            return redirect(url_for('loginpage') + '?tab=admin')
        else:
            flash('Please enter a new password.', 'danger')

    return render_template('reset_password.html', token=token)
# Note: The reset_password.html template should include a form that submits the new password to the same URL (including the token).

#student registration
@app.route('/register/student', methods=['POST'])
def register_student():    
    name= request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone=request.form.get('phone', '').strip()
    regno=request.form.get('regno','').strip()
    department=request.form.get('department','').strip()
    sem=request.form.get('sem','').strip()
    gender=request.form.get('gender','').strip()
    dob=request.form.get('dob','').strip()
    batch=request.form.get('batch','').strip()
    cgpa=request.form.get('cgpa','').strip()
    backlogs=request.form.get('backlogs','').strip()
    address=request.form.get('address','').strip()
    tenth_percent=request.form.get('tenth_percent','').strip()
    twelfth_percent=request.form.get('twelfth_percent','').strip()
    password = request.form.get('password', '').strip() # Get password from form input
    
    
    #validate registration number format  using regex where U is fixed, 16 is year of admission, NB is department code, 23 is batch year, S  is fixed and 0120 is unique number
    #validate the batch year based on the batch entered by student taking in consideration the last two digits for eg if batch is 2022-25 then it will take 25 and compare with regno[3:5] which is 23 in this case and it will show error because batch year and regno year should match
    batch_year_pattern = r'^\d{4}-\d{2}$'
    if not re.fullmatch(batch_year_pattern, batch):
        flash('Invalid batch format. Please follow the format: 2022-25', 'danger')
    #validate batch year matches regno year
    batch_year = batch.split('-')[1]  # Get the last two digits of the batch year
    regno_year = regno[5:7]           # Get the year part from the registration number
    if batch_year != regno_year:    
        flash('Batch year does not match registration number year.', 'danger')
        return redirect(url_for('register'))
    
    regno_pattern = r'^U16NB\d{2}[S]\d{4}$'
    if not re.fullmatch(regno_pattern, regno):
        flash('Invalid registration number format. Please follow the format: U16NB23S0120', 'danger')
        return redirect(url_for('register'))
   
    #validate phone number format   
    phone_pattern = r'^\d{10}$'
    if not re.fullmatch(phone_pattern, phone):
        flash('Invalid phone number format. Please enter a 10-digit phone number.', 'danger')
        return redirect(url_for('register'))

    try:
        # 1. First create the User record for authentication
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            full_name=name,
            email=email,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            role='student',
            phone=phone
        )
        db.session.add(new_user)
        db.session.flush() # Flush to generate new_user.id for the foreign key

        # 2. Create the Student record linked to the new user
        new_student = Student(
            student_id=new_user.id, # Foreign key to User
            name=name,
            email=email,
            phone=phone,
            regno=regno,
            department=department,
            sem=int(sem),
            gender=gender,
            dob=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
            batch=batch,
            cgpa=float(cgpa) if cgpa else 0.0,
            backlogs=int(backlogs) if backlogs else 0,
            address=address,
            tenth_percent=float(tenth_percent) if tenth_percent else None,
            twelfth_percent=float(twelfth_percent) if twelfth_percent else None
        )
        db.session.add(new_student)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('loginpage'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating student record: {e}', 'danger')
        return redirect(url_for('register'))






# ─── Logout ──────────────────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    response = redirect(url_for('home'))
    unset_jwt_cookies(response)
    return response


# ─── Dashboards ──────────────────────────────────────────────────────────────

@app.route('/admin_dashboard')
@login_required(roles=['principal'])
def admin():
    return render_template('admin_dashboard.html')


@app.route('/student_dashboard')
@login_required(roles=['student'])
def student_dashboard():
    claims  = get_jwt()
    regno   = claims.get('regno')
    student = Student.query.filter_by(regno=regno).first()
    
    # Fetch stats for overview cards
    applications = Application.query.filter_by(student_id=student.id).all()
    stats = {
        'total_applied': len(applications),
        'shortlisted': len([a for a in applications if a.status == 'shortlisted']),
        'interviews': len([a for a in applications if a.status == 'interviewed']),
        'rejected': len([a for a in applications if a.status == 'rejected'])
    }
    
    # Store applied job IDs for UI status updates
    applied_job_ids = [a.job_id for a in applications]
    
    # Fetch active job postings
    jobs = JobPosting.query.order_by(JobPosting.deadline.desc()).all()
    deadlines = []
    skills = []
    
    return render_template('student_dashboard.html', 
                         student=student,
                         stats=stats,
                         applications=applications,
                         jobs=jobs,
                         applied_job_ids=applied_job_ids,
                         deadlines=deadlines,
                         skills=skills)


@app.route('/apply_job/<int:job_id>', methods=['POST'])
@login_required(roles=['student'])
def apply_job(job_id):
    claims = get_jwt()
    regno = claims.get('regno')
    student = Student.query.filter_by(regno=regno).first()

    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Check if already applied
    existing = Application.query.filter_by(job_id=job_id, student_id=student.id).first()
    if existing:
        flash('You have already applied for this position.', 'warning')
        return redirect(url_for('student_dashboard'))
    
    try:
        new_app = Application(job_id=job_id, student_id=student.id)
        db.session.add(new_app)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error applying for job: {str(e)}', 'danger')

    return redirect(url_for('student_dashboard'))



@app.route('/hod_dashboard')
@login_required(roles=['hod'])
def hod_dashboard():
    from flask_jwt_extended import get_jwt_identity
    email = get_jwt_identity()
    user  = User.query.filter_by(email=email).first()
    return render_template('hod_dashboard.html', user=user)


@app.route('/tpo_dashboard')
@login_required(roles=['tpo'])
def tpo_dashboard():
    from flask_jwt_extended import get_jwt_identity
    email = get_jwt_identity()
    user  = User.query.filter_by(email=email).first()
    jobs  = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    return render_template('tpo_dashboard.html', user=user, jobs=jobs)


@app.route('/track_registrations')
@login_required(roles=['tpo'])
def track_registrations():
    from flask_jwt_extended import get_jwt_identity
    email = get_jwt_identity()
    user  = User.query.filter_by(email=email).first()
    jobs  = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    return render_template('track_registrations.html', user=user, jobs=jobs)


@app.route('/post_job', methods=['POST'])
@login_required(roles=['tpo'])
def post_job():
    from flask_jwt_extended import get_jwt_identity
    email = get_jwt_identity()
    user  = User.query.filter_by(email=email).first()

    company_name = request.form.get('company_name')
    job_role = request.form.get('job_role')
    job_description = request.form.get('job_description')
    eligibility_criteria = request.form.get('eligibility_criteria')
    salary_package = request.form.get('salary_package')
    location = request.form.get('location')
    deadline_str = request.form.get('deadline')
    form_link = request.form.get('form_link')

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        new_job = JobPosting(
            company_name=company_name,
            job_role=job_role,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            salary_package=salary_package,
            location=location,
            deadline=deadline,
            form_link=form_link,
            posted_by=user.id
        )
        db.session.add(new_job)
        db.session.commit()
        flash('Job posting published successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error publishing job: {str(e)}', 'danger')

    return redirect(url_for('tpo_dashboard'))


@app.route('/job_applicants/<int:job_id>')
@login_required(roles=['tpo'])
def job_applicants(job_id):
    job = JobPosting.query.get_or_404(job_id)
    # Fetch applications with joined students
    applications = Application.query.filter_by(job_id=job_id).all()
    return render_template('job_applicants.html', job=job, applications=applications)


@app.route('/update_application_status/<int:app_id>', methods=['POST'])
@login_required(roles=['tpo'])
def update_application_status(app_id):
    application = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'shortlisted', 'interviewed', 'rejected', 'selected']:
        application.status = new_status
        db.session.commit()
        flash(f'Status updated to {new_status}!', 'success')
    else:
        flash('Invalid status provided.', 'danger')
        
    return redirect(url_for('job_applicants', job_id=application.job_id))


@app.route('/update_job_form/<int:job_id>', methods=['GET', 'POST'])
@login_required(roles=['tpo'])
def update_job_form(job_id):
    job = JobPosting.query.get_or_404(job_id)
    
    if request.method == 'GET':
        # Return job details for the edit modal
        return {
            'id': job.id,
            'company_name': job.company_name,
            'job_role': job.job_role,
            'job_description': job.job_description,
            'eligibility_criteria': job.eligibility_criteria,
            'salary_package': job.salary_package,
            'location': job.location,
            'deadline': job.deadline.strftime('%Y-%m-%dT%H:%M'),
            'form_link': job.form_link
        }

    # Extract all fields from the form
    company_name = request.form.get('company_name')
    job_role = request.form.get('job_role')
    job_description = request.form.get('job_description')
    eligibility_criteria = request.form.get('eligibility_criteria')
    department = request.form.get('department')
    location = request.form.get('location')
    deadline_str = request.form.get('deadline')
    form_link = request.form.get('form_link')
    
    try:
        job.company_name = company_name
        job.job_role = job_role
        job.job_description = job_description
        job.eligibility_criteria = eligibility_criteria
        job.department = department
        job.location = location
        if deadline_str:
            job.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        job.form_link = form_link
        
        db.session.commit()
        flash(f'Placement drive for {job.company_name} updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating drive: {str(e)}', 'danger')
        
    return redirect(url_for('tpo_dashboard'))


@app.route('/download_applicants_excel/<int:job_id>')
@login_required(roles=['tpo'])
def download_applicants_excel(job_id):
    job = JobPosting.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    
    data = []
    for app in applications:
        data.append({
            'Student Name': app.student.name,
            'Reg No': app.student.regno,
            'Email': app.student.email,
            'Phone': app.student.phone,
            'Dept': app.student.department,
            'Sem': app.student.sem,
            'CGPA': app.student.cgpa,
            'Status': app.status.capitalize(),
            'Applied Date': app.applied_at.strftime('%Y-%m-%d %H:%M')
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Applicants')
    
    output.seek(0)
    filename = f"Applicants_{job.company_name}_{job.job_role}.xlsx".replace(' ', '_')
    
    return send_file(output, 
                     download_name=filename, 
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/download_applicants_pdf/<int:job_id>')
@login_required(roles=['tpo'])
def download_applicants_pdf(job_id):
    job = JobPosting.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>Applicant Report - {job.company_name}</b>", styles['Title'])
    subtitle = Paragraph(f"Role: {job.job_role} | Date: {datetime.now().strftime('%d %b, %Y')}", styles['Heading2'])
    elements.extend([title, subtitle, Spacer(1, 20)])
    
    # Table Header
    data = [['Student Name', 'Reg No', 'Email', 'Dept/Sem', 'CGPA', 'Status']]
    
    # Table Data
    for app in applications:
        data.append([
            app.student.name,
            app.student.regno,
            app.student.email,
            f"{app.student.department}/{app.student.sem}",
            str(app.student.cgpa),
            app.status.capitalize()
        ])
    
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    filename = f"Applicants_{job.company_name}_{job.job_role}.pdf".replace(' ', '_')
    
    return send_file(buffer, 
                     download_name=filename, 
                     as_attachment=True,
                     mimetype='application/pdf')


@app.route('/change_password', methods=['POST'])
@jwt_required()
def change_password():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not bcrypt.check_password_hash(user.password, current_password):
        flash('Current password incorrect.', 'danger')
    elif new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
    else:
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('Password updated successfully!', 'success')
        
    # Redirect back to the referrer or dashboard
    return redirect(request.referrer or url_for('home'))


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

    # app.run(host='0.0.0.0', port=5000, debug=True) # for mobile access