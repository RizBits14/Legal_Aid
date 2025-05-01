from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from authlib.integrations.flask_client import OAuth
import json

app = Flask(__name__)
app.secret_key = 'Kage0012'
s = URLSafeTimedSerializer(app.secret_key)

# OAuth Configuration
oauth = OAuth(app)

# Google OAuth
google = oauth.register(
    name='google',
    client_id='YOUR_GOOGLE_CLIENT_ID',
    client_secret='YOUR_GOOGLE_CLIENT_SECRET',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'dattebayo12086@gmail.com'
app.config['MAIL_PASSWORD'] = 'qkmt eqqb fvvy oijr' #App Pass

mail = Mail(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'Legal_Aid'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
LICENSE_FOLDER = os.path.join(UPLOAD_FOLDER, 'licenses')
PHOTO_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Session Configuration
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

mysql = MySQL(app)

# Create upload directories if they don't exist
os.makedirs(LICENSE_FOLDER, exist_ok=True)
os.makedirs(PHOTO_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('client_signin'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'Admin':
            return redirect(url_for('admin_signin'))
        return f(*args, **kwargs)
    return decorated_function

def lawyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'Lawyer':
            return redirect(url_for('lawyer_signin'))
        return f(*args, **kwargs)
    return decorated_function

def create_connection():
    return mysql.connection

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/client-signup', methods=['GET', 'POST'])
def client_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        
        # Handle photo upload
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('client_signup.html')
            
        photo_file = request.files['photo']
        if photo_file.filename == '':
            flash('No photo selected', 'error')
            return render_template('client_signup.html')
            
        if not allowed_file(photo_file.filename):
            flash('Invalid file type. Please upload PNG, JPG, or JPEG files only.', 'error')
            return render_template('client_signup.html')
        
        cur = mysql.connection.cursor()
        
        # Check if email already exists
        cur.execute("SELECT * FROM Users WHERE email = %s", [email])
        if cur.fetchone():
            flash("Email already registered", "error")
            return render_template('client_signup.html')
        
        # Save photo
        filename = secure_filename(photo_file.filename)
        photo_path = os.path.join(PHOTO_FOLDER, filename)
        photo_file.save(photo_path)
        
        # Insert new client into Users table
        cur.execute(
            "INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType) VALUES (%s, %s, %s, %s, %s, 'Client')",
            (name.split()[0], name.split()[-1], email, generate_password_hash(password), phone)
        )
        user_id = cur.lastrowid
        
        # Insert client details
        cur.execute(
            "INSERT INTO ClientDetails (UserId, Address, City, State, Photo) VALUES (%s, %s, %s, %s, %s)",
            (user_id, address, city, state, photo_path)
        )
        mysql.connection.commit()
        cur.close()
        
        flash("Registration successful! Please sign in.", "success")
        return redirect(url_for('client_signin'))
                
    return render_template('client_signup.html')

@app.route('/lawyer-signup', methods=['GET', 'POST'])
def lawyer_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        license_number = request.form.get('license')
        specialization = request.form.get('specialization')
        experience = request.form.get('experience')
        
        # Handle license proof upload
        if 'license_proof' not in request.files:
            flash('No license proof uploaded', 'error')
            return render_template('lawyer_signup.html')
            
        license_file = request.files['license_proof']
        if license_file.filename == '':
            flash('No license proof selected', 'error')
            return render_template('lawyer_signup.html')
            
        if not allowed_file(license_file.filename):
            flash('Invalid file type. Please upload PDF, PNG, JPG, or JPEG files only.', 'error')
            return render_template('lawyer_signup.html')
            
        # Handle photo upload
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return render_template('lawyer_signup.html')
            
        photo_file = request.files['photo']
        if photo_file.filename == '':
            flash('No photo selected', 'error')
            return render_template('lawyer_signup.html')
            
        if not allowed_file(photo_file.filename):
            flash('Invalid file type. Please upload PNG, JPG, or JPEG files only.', 'error')
            return render_template('lawyer_signup.html')
            
        cur = mysql.connection.cursor()
        
        # Check if email already exists
        cur.execute("SELECT * FROM Users WHERE email = %s", [email])
        if cur.fetchone():
            flash("Email already registered", "error")
            return render_template('lawyer_signup.html')
        
        # Check if license number already exists
        cur.execute("SELECT * FROM LawyerDetails WHERE LicenseNumber = %s", [license_number])
        if cur.fetchone():
            flash("License number already registered", "error")
            return render_template('lawyer_signup.html')
        
        # Save files
        license_filename = secure_filename(license_file.filename)
        license_path = os.path.join(LICENSE_FOLDER, license_filename)
        license_file.save(license_path)
        
        photo_filename = secure_filename(photo_file.filename)
        photo_path = os.path.join(PHOTO_FOLDER, photo_filename)
        photo_file.save(photo_path)
        
        # Insert lawyer user
        cur.execute(
            "INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType) VALUES (%s, %s, %s, %s, %s, 'Lawyer')",
            (name.split()[0], name.split()[-1], email, generate_password_hash(password), phone)
        )
        user_id = cur.lastrowid
        
        # Insert lawyer details
        cur.execute(
            "INSERT INTO LawyerDetails (UserId, LicenseNumber, LicenseProof, Photo, Specialization, YearsOfExperience) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, license_number, license_path, photo_path, specialization, experience)
        )
        mysql.connection.commit()
        cur.close()
        
        flash("Registration submitted! We'll review your application and contact you soon.", "success")
        return redirect(url_for('lawyer_signin'))
                
    return render_template('lawyer_signup.html')

# Authentication routes
@app.route('/client/signin', methods=['GET', 'POST'])
def client_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE Email = %s AND UserType = 'Client'", [email])
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['Password'], password):
            session['user_id'] = user['id']
            session['user_type'] = 'Client'
            flash('Welcome back!', 'success')
            return redirect(url_for('client_dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('client_signin.html')

@app.route('/lawyer/signin', methods=['GET', 'POST'])
def lawyer_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT u.*, ld.VerificationStatus 
            FROM Users u 
            JOIN LawyerDetails ld ON u.id = ld.UserId 
            WHERE u.Email = %s AND u.UserType = 'Lawyer'
        """, [email])
        lawyer = cur.fetchone()
        cur.close()
        
        if lawyer and check_password_hash(lawyer['Password'], password):
            if lawyer['VerificationStatus'] == 'Approved':
                session['user_id'] = lawyer['id']
                session['user_type'] = 'Lawyer'
                flash('Welcome back!', 'success')
                return redirect(url_for('lawyer_dashboard'))
            else:
                return render_template('lawyer_signin.html', 
                                     verification_status=lawyer['VerificationStatus'])
        
        flash('Invalid email or password', 'error')
    return render_template('lawyer_signin.html')

@app.route('/admin/signin', methods=['GET', 'POST'])
def admin_signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Users WHERE Email = %s AND UserType = 'Admin'", [email])
        admin = cur.fetchone()
        cur.close()
        
        if admin and check_password_hash(admin['Password'], password):
            session['user_id'] = admin['id']
            session['user_type'] = 'Admin'
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('admin_signin.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.*, ld.* 
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer'
        ORDER BY 
            CASE ld.VerificationStatus
                WHEN 'Pending' THEN 1
                WHEN 'Rejected' THEN 2
                WHEN 'Approved' THEN 3
            END
    """)
    pending_lawyers = cur.fetchall()
    cur.close()
    
    return render_template('admin_dashboard.html', pending_lawyers=pending_lawyers)

@app.route('/admin/verify-lawyer', methods=['POST'])
@admin_required
def verify_lawyer():
    lawyer_id = request.form.get('lawyer_id')
    action = request.form.get('action')
    
    if action not in ['approve', 'reject']:
        flash('Invalid action', 'error')
        return redirect(url_for('admin_dashboard'))
    
    status = 'Approved' if action == 'approve' else 'Rejected'
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE LawyerDetails 
        SET VerificationStatus = %s, 
            VerifiedBy = %s,
            VerificationDate = CURRENT_TIMESTAMP
        WHERE UserId = %s
    """, [status, session['user_id'], lawyer_id])
    mysql.connection.commit()
    cur.close()
    
    flash(f'Lawyer has been {status.lower()}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/client/dashboard')
@login_required
def client_dashboard():
    return render_template('client_dashboard.html')

@app.route('/lawyer/dashboard')
@lawyer_required
def lawyer_dashboard():
    return render_template('lawyer_dashboard.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

# Social Login Routes
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()

    first_name = user_info.get('given_name', 'Unknown')
    last_name = user_info.get('family_name', '')
    email = user_info.get('email')

    conn = create_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Users WHERE Email = %s", (email,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO Users (FirstName, LastName, Email, UserType) VALUES (%s, %s, %s, 'Client')",
            (first_name, last_name, email)
        )
        conn.commit()
        user_id = cur.lastrowid
    else:
        user_id = user['id']

    cur.close()
    conn.close()

    session['user_id'] = user_id
    session['user_type'] = 'Client'
    flash('Welcome via Google!', 'success')
    return redirect(url_for('client_dashboard'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True) 
