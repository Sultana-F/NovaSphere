from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Role, LoginDetail, Student
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    get_jti, JWTManager, set_access_cookies, unset_jwt_cookies
)
from functools import wraps



app = Flask(__name__)
app.config['SECRET_KEY'] = 'MYSUPERKEYOFBCAfolderhelpingtosecuretheapp123!@#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://nims:Nims2019@localhost/nimsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'mysupersecretkeyforjwthelperingtosecuretheappofbcafolderplaceholdervalue123!@#'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # For simplicity in this dev environment


jwt = JWTManager(app)

# Token revocation blacklist
blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklist


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
def index():
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
    if not user or user.password != password:
        flash('Invalid credentials. Please try again.', 'danger')
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
    if not user or user.password != password:
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
            username=user.full_name,
            password=user.password,
            accessToken=str(jti),
        )
        db.session.add(audit)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error recording login details: {e}")
    return jti


# ─── Logout ──────────────────────────────────────────────────────────────────

@app.route('/logout')
def logout():
    response = redirect(url_for('index'))
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
    from flask_jwt_extended import get_jwt
    claims  = get_jwt()
    regno   = claims.get('regno')
    student = Student.query.filter_by(regno=regno).first()
    return render_template('student_dashboard.html', student=student)


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
    return render_template('tpo_dashboard.html', user=user)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)