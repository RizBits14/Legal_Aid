from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
from flask import Flask, redirect, render_template, request, session, url_for, flash, send_file
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from authlib.integrations.flask_client import OAuth
import json
from dotenv import load_dotenv
import io
from PIL import Image  # Add Pillow for image processing

load_dotenv()

print(os.getenv('MYSQL_HOST'))

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
app.config['MYSQL_CONNECT_TIMEOUT'] = 60
app.config['MYSQL_READ_DEFAULT_TIMEOUT'] = 60
app.config['MYSQL_WRITE_TIMEOUT'] = 60

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

def compress_image(image_data, max_size_kb=500):
    """Compress an image to reduce its size."""
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # Calculate target size
        target_size = max_size_kb * 1024
        
        # Start with quality 90
        quality = 90
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality)
        
        # Reduce quality until we get below target size or reach minimum quality
        while output.tell() > target_size and quality > 30:
            output = io.BytesIO()
            quality -= 10
            img.save(output, format='JPEG', quality=quality)
        
        return output.getvalue()
    except Exception as e:
        print(f"Image compression error: {str(e)}")
        return image_data  # Return original if compression fails

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

def check_connection():
    try:
        # Try to ping the connection to see if it's alive
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return True
    except:
        # If connection is lost, attempt to reconnect
        try:
            mysql.connection.ping(True)
            return True
        except:
            return False

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
        # Basic information
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        # Professional information
        license_number = request.form.get('license')
        specialization = request.form.get('specialization')
        experience = request.form.get('experience')
        consultation_fee = request.form.get('consultation_fee', 150)
        
        # Office information
        office_address = request.form.get('office_address', 'Office address to be updated.')
        available_hours = request.form.get('available_hours', 'Mon-Fri: 9AM-6PM')
        languages = request.form.get('languages', 'English')
        
        # Professional background
        bio = request.form.get('bio', 'Experienced legal professional dedicated to providing excellent service and achieving the best outcomes for clients.')
        education = request.form.get('education', 'Legal education details will be updated by the lawyer.')
        bar_association = request.form.get('bar_association', 'State Bar Association')
        
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
            
        try:
            # Ensure MySQL connection is active
            if not check_connection():
                flash("Database connection error. Please try again.", "error")
                return render_template('lawyer_signup.html')
                
            # Check if email already exists first
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM Users WHERE email = %s", [email])
            if cur.fetchone():
                cur.close()
                flash("Email already registered", "error")
                return render_template('lawyer_signup.html')
            
            # Check if license number already exists
            cur.execute("SELECT * FROM LawyerDetails WHERE LicenseNumber = %s", [license_number])
            if cur.fetchone():
                cur.close()
                flash("License number already registered", "error")
                return render_template('lawyer_signup.html')
            
            # Save license file
            license_filename = secure_filename(license_file.filename)
            license_path = os.path.join(LICENSE_FOLDER, license_filename)
            license_file.save(license_path)
            
            # Save photo file instead of storing as binary
            photo_filename = secure_filename(photo_file.filename)
            photo_path = os.path.join(PHOTO_FOLDER, photo_filename)
            
            # Compress and save the photo
            img = Image.open(photo_file)
            img.thumbnail((500, 500))  # Resize to max dimensions
            img.save(photo_path, quality=85, optimize=True)
            
            # Ensure connection is still active before the first insert
            if not check_connection():
                flash("Database connection error. Please try again.", "error")
                return render_template('lawyer_signup.html')
                
            # Insert lawyer user in a separate transaction
            cur.execute(
                "INSERT INTO Users (FirstName, LastName, Email, Password, Phone, UserType) VALUES (%s, %s, %s, %s, %s, 'Lawyer')",
                (name.split()[0], name.split()[-1], email, generate_password_hash(password), phone)
            )
            user_id = cur.lastrowid
            mysql.connection.commit() 
            
            # Ensure connection is still active before the second insert
            if not check_connection():
                flash("Database connection error during registration. Your user account was created, but please contact support.", "error")
                return render_template('lawyer_signup.html')
                
            # Create practice areas JSON from specialization
            practice_areas = f'["{specialization}"]'
            
            # Start a new transaction for lawyer details with enhanced fields
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO LawyerDetails (
                    UserId, LicenseNumber, LicenseProof, Photo, Specialization, YearsOfExperience,
                    Bio, Education, BarAssociation, OfficeAddress, ConsultationFee, Languages,
                    PracticeAreas, AvailableHours
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, license_number, license_filename, photo_filename, specialization, experience,
                bio, education, bar_association, office_address, consultation_fee, languages,
                practice_areas, available_hours
            ))
            mysql.connection.commit()
            cur.close()
            
            flash("Registration submitted successfully! We'll review your application and contact you soon.", "success")
            return redirect(url_for('lawyer_signin'))
                
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Registration failed. Please try again. Error: {str(e)}", "error")
            return render_template('lawyer_signup.html')
                
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
    
    # Get all lawyers
    cur.execute("""
        SELECT u.id, u.FirstName, u.LastName, u.Email, u.Phone,
               ld.UserId, ld.LicenseNumber, ld.LicenseProof, ld.Specialization, 
               ld.YearsOfExperience, ld.VerificationStatus
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
    
    # Get count of pending verifications for notification badge
    cur.execute("""
        SELECT COUNT(*) as pending_count
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Pending'
    """)
    pending_count = cur.fetchone()['pending_count']
    
    # Get count of new contact messages for notification badge
    cur.execute("SELECT COUNT(*) as new_messages FROM ContactMessages WHERE status = 'New'")
    new_messages_count = cur.fetchone()['new_messages']
    
    cur.close()
    
    return render_template('admin_dashboard.html', 
                         pending_lawyers=pending_lawyers,
                         pending_count=pending_count,
                         new_messages_count=new_messages_count)

# Add these new routes to your index.py file

@app.route('/admin/manage-users')
@admin_required
def admin_manage_users():
    cur = mysql.connection.cursor()
    
    # Get all lawyers
    cur.execute("""
        SELECT u.id, u.FirstName, u.LastName, u.Email, u.Phone, u.CreatedAt,
               ld.LicenseNumber, ld.Specialization, ld.YearsOfExperience, ld.VerificationStatus
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer'
        ORDER BY u.CreatedAt DESC
    """)
    lawyers = cur.fetchall()
    
    # Get all clients
    cur.execute("""
        SELECT u.id, u.FirstName, u.LastName, u.Email, u.Phone, u.CreatedAt,
               cd.City, cd.State
        FROM Users u 
        JOIN ClientDetails cd ON u.id = cd.UserId 
        WHERE u.UserType = 'Client'
        ORDER BY u.CreatedAt DESC
    """)
    clients = cur.fetchall()
    
    # Get notification counts
    cur.execute("""
        SELECT COUNT(*) as pending_count
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Pending'
    """)
    pending_count = cur.fetchone()['pending_count']
    
    cur.execute("SELECT COUNT(*) as new_messages FROM ContactMessages WHERE status = 'New'")
    new_messages_count = cur.fetchone()['new_messages']
    
    cur.close()
    
    return render_template('admin_manage_users.html', 
                         lawyers=lawyers, 
                         clients=clients,
                         pending_count=pending_count,
                         new_messages_count=new_messages_count)

@app.route('/admin/notification-counts')
@admin_required
def get_notification_counts():
    """API endpoint to get current notification counts"""
    cur = mysql.connection.cursor()
    
    # Get pending lawyer verifications count
    cur.execute("""
        SELECT COUNT(*) as pending_count
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Pending'
    """)
    pending_count = cur.fetchone()['pending_count']
    
    # Get new contact messages count
    cur.execute("SELECT COUNT(*) as new_messages FROM ContactMessages WHERE status = 'New'")
    new_messages_count = cur.fetchone()['new_messages']
    
    cur.close()
    
    return {
        'pending_count': pending_count,
        'new_messages_count': new_messages_count,
        'total_notifications': pending_count + new_messages_count
    }

@app.route('/admin/delete-lawyer', methods=['POST'])
@admin_required
def delete_lawyer():
    lawyer_id = request.form.get('lawyer_id')
    
    if not lawyer_id:
        flash('Invalid lawyer ID', 'error')
        return redirect(url_for('admin_manage_users'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Get lawyer details for cleanup
        cur.execute("SELECT Photo, LicenseProof FROM LawyerDetails WHERE UserId = %s", [lawyer_id])
        lawyer_files = cur.fetchone()
        
        # Delete from LawyerDetails first (due to foreign key constraint)
        cur.execute("DELETE FROM LawyerDetails WHERE UserId = %s", [lawyer_id])
        
        # Delete from Users table
        cur.execute("DELETE FROM Users WHERE id = %s AND UserType = 'Lawyer'", [lawyer_id])
        
        mysql.connection.commit()
        
        # Clean up files if they exist
        if lawyer_files:
            try:
                if lawyer_files['Photo']:
                    photo_path = os.path.join(PHOTO_FOLDER, lawyer_files['Photo'])
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                
                if lawyer_files['LicenseProof']:
                    license_path = os.path.join(LICENSE_FOLDER, lawyer_files['LicenseProof'])
                    if os.path.exists(license_path):
                        os.remove(license_path)
            except Exception as file_error:
                app.logger.error(f"Error deleting files: {str(file_error)}")
        
        cur.close()
        flash('Lawyer deleted successfully', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting lawyer: {str(e)}', 'error')
    
    return redirect(url_for('admin_manage_users'))

@app.route('/admin/delete-client', methods=['POST'])
@admin_required
def delete_client():
    client_id = request.form.get('client_id')
    
    if not client_id:
        flash('Invalid client ID', 'error')
        return redirect(url_for('admin_manage_users'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Get client photo for cleanup
        cur.execute("SELECT Photo FROM ClientDetails WHERE UserId = %s", [client_id])
        client_files = cur.fetchone()
        
        # Delete from ClientDetails first (due to foreign key constraint)
        cur.execute("DELETE FROM ClientDetails WHERE UserId = %s", [client_id])
        
        # Delete from Users table
        cur.execute("DELETE FROM Users WHERE id = %s AND UserType = 'Client'", [client_id])
        
        mysql.connection.commit()
        
        # Clean up photo file if it exists
        if client_files and client_files['Photo']:
            try:
                photo_path = os.path.join(PHOTO_FOLDER, client_files['Photo'])
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as file_error:
                app.logger.error(f"Error deleting photo: {str(file_error)}")
        
        cur.close()
        flash('Client deleted successfully', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting client: {str(e)}', 'error')
    
    return redirect(url_for('admin_manage_users'))

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

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Basic validation
        if not name or not email or not message:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('contact'))
        
        try:
            # Store in database first
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO ContactMessages (name, email, phone, subject, message, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (name, email, phone, subject, message))
            mysql.connection.commit()
            cur.close()
            
            # Try to send email
            try:
                msg = Message(
                    subject=f"New Contact Form Submission - {subject}",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[app.config['MAIL_USERNAME']],  # Send to admin email
                    body=f"""
                    Name: {name}
                    Email: {email}
                    Phone: {phone}
                    Subject: {subject}
                    
                    Message:
                    {message}
                    """
                )
                mail.send(msg)
            except Exception as mail_error:
                app.logger.error(f"Email sending failed: {str(mail_error)}")
                # Don't return here, continue to show success message since data was saved
            
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as db_error:
            flash('An error occurred while saving your message. Please try again later.', 'error')
            app.logger.error(f"Database error: {str(db_error)}")
            return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/admin/contact-messages')
@admin_required
def admin_contact_messages():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM ContactMessages 
        ORDER BY 
            CASE status
                WHEN 'New' THEN 1
                WHEN 'Pending' THEN 2
                WHEN 'Solved' THEN 3
                WHEN 'Rejected' THEN 4
            END,
            created_at DESC
    """)
    messages = cur.fetchall()
    
    # Get notification counts
    cur.execute("""
        SELECT COUNT(*) as pending_count
        FROM Users u 
        JOIN LawyerDetails ld ON u.id = ld.UserId 
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Pending'
    """)
    pending_count = cur.fetchone()['pending_count']
    
    cur.execute("SELECT COUNT(*) as new_messages FROM ContactMessages WHERE status = 'New'")
    new_messages_count = cur.fetchone()['new_messages']
    
    cur.close()
    
    return render_template('admin_contact_messages.html', 
                         messages=messages,
                         pending_count=pending_count,
                         new_messages_count=new_messages_count)

@app.route('/admin/update-message-status', methods=['POST'])
@admin_required
def update_message_status():
    message_id = request.form.get('message_id')
    new_status = request.form.get('status')
    
    if not message_id or not new_status:
        flash('Invalid request', 'error')
        return redirect(url_for('admin_contact_messages'))
    
    if new_status not in ['New', 'Pending', 'Solved', 'Rejected']:
        flash('Invalid status', 'error')
        return redirect(url_for('admin_contact_messages'))
    
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE ContactMessages 
        SET status = %s 
        WHERE id = %s
    """, (new_status, message_id))
    mysql.connection.commit()
    cur.close()
    
    flash(f'Message status updated to {new_status}', 'success')
    return redirect(url_for('admin_contact_messages'))

@app.route('/lawyers')
def lawyer_page():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id, CONCAT(u.FirstName, ' ', u.LastName) as name, 
               u.FirstName, u.LastName, u.Email, u.Phone,
               ld.Specialization, ld.YearsOfExperience as experience,
               ld.Photo, ld.LicenseNumber, ld.Bio, ld.Education,
               ld.OfficeAddress, ld.ConsultationFee, ld.Languages,
               ld.PracticeAreas, ld.Achievements, ld.AvailableHours,
               ld.Rating, ld.TotalReviews, ld.BarAssociation
        FROM Users u
        JOIN LawyerDetails ld ON u.id = ld.UserId
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved'
        ORDER BY ld.Rating DESC, ld.YearsOfExperience DESC
    """)
    lawyers = cur.fetchall()
    cur.close()
    
    return render_template('lawyer_page.html', lawyers=lawyers)

@app.route('/lawyer-details/<int:lawyer_id>')
def lawyer_details(lawyer_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.id, CONCAT(u.FirstName, ' ', u.LastName) as name, 
               u.FirstName, u.LastName, u.Email, u.Phone,
               ld.Specialization, ld.YearsOfExperience as experience,
               ld.Photo, ld.LicenseNumber, ld.Bio, ld.Education,
               ld.OfficeAddress, ld.ConsultationFee, ld.Languages,
               ld.PracticeAreas, ld.Achievements, ld.AvailableHours,
               ld.Rating, ld.TotalReviews, ld.BarAssociation
        FROM Users u
        JOIN LawyerDetails ld ON u.id = ld.UserId
        WHERE u.id = %s AND u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved'
    """, [lawyer_id])
    lawyer = cur.fetchone()
    
    if not lawyer:
        return {'error': 'Lawyer not found'}, 404
    
    # Get recent reviews for this lawyer
    cur.execute("""
        SELECT lr.Rating, lr.ReviewText, lr.CreatedAt,
               CONCAT(u.FirstName, ' ', SUBSTRING(u.LastName, 1, 1), '.') as reviewer_name
        FROM LawyerReviews lr
        JOIN Users u ON lr.ClientId = u.id
        WHERE lr.LawyerId = %s AND lr.IsVerified = TRUE
        ORDER BY lr.CreatedAt DESC
        LIMIT 5
    """, [lawyer_id])
    reviews = cur.fetchall()
    
    cur.close()
    
    # Parse JSON fields
    import json
    try:
        lawyer['PracticeAreas'] = json.loads(lawyer['PracticeAreas']) if lawyer['PracticeAreas'] else []
        lawyer['Achievements'] = json.loads(lawyer['Achievements']) if lawyer['Achievements'] else []
    except:
        lawyer['PracticeAreas'] = []
        lawyer['Achievements'] = []
    
    return {
        'lawyer': lawyer,
        'reviews': reviews
    }

@app.route('/lawyer-photo/<int:lawyer_id>')
def lawyer_photo(lawyer_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT Photo FROM LawyerDetails WHERE UserId = %s", [lawyer_id])
    result = cur.fetchone()
    cur.close()
    
    if result and result['Photo']:
        photo = result['Photo']
        # Check if it's a file path or binary data
        if isinstance(photo, str):
            # It's a filename
            photo_path = os.path.join(PHOTO_FOLDER, photo)
            if os.path.exists(photo_path):
                return send_file(photo_path)
        else:
            # It's binary data
            photo_data = io.BytesIO(photo)
            return send_file(photo_data, mimetype='image/jpeg')
    
    return '', 404

@app.route('/lawyer-license/<int:lawyer_id>')
def lawyer_license(lawyer_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT LicenseProof FROM LawyerDetails WHERE UserId = %s", [lawyer_id])
    result = cur.fetchone()
    cur.close()
    
    if result and result['LicenseProof']:
        license_path = os.path.join(LICENSE_FOLDER, result['LicenseProof'])
        if os.path.exists(license_path):
            return send_file(license_path)
    
    return '', 404

@app.route('/book-consultation', methods=['POST'])
@login_required
def book_consultation():
    if session.get('user_type') != 'Client':
        return {'error': 'Only clients can book consultations'}, 403
    
    lawyer_id = request.json.get('lawyer_id')
    consultation_date = request.json.get('consultation_date')
    consultation_type = request.json.get('consultation_type', 'Video Call')
    notes = request.json.get('notes', '')
    
    if not lawyer_id or not consultation_date:
        return {'error': 'Missing required fields'}, 400
    
    try:
        cur = mysql.connection.cursor()
        
        # Get lawyer details for fee
        cur.execute("""
            SELECT ld.ConsultationFee, CONCAT(u.FirstName, ' ', u.LastName) as lawyer_name
            FROM LawyerDetails ld
            JOIN Users u ON ld.UserId = u.id
            WHERE u.id = %s AND ld.VerificationStatus = 'Approved'
        """, [lawyer_id])
        lawyer_info = cur.fetchone()
        
        if not lawyer_info:
            return {'error': 'Lawyer not found'}, 404
        
        # Insert consultation booking
        cur.execute("""
            INSERT INTO Consultations (LawyerId, ClientId, ConsultationDate, 
                                     ConsultationType, Notes, Fee)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (lawyer_id, session['user_id'], consultation_date, 
              consultation_type, notes, lawyer_info['ConsultationFee']))
        
        consultation_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()
        
        # Here you could add email notification logic
        
        return {
            'success': True,
            'consultation_id': consultation_id,
            'message': f'Consultation booked with {lawyer_info["lawyer_name"]}',
            'fee': float(lawyer_info['ConsultationFee'])
        }
        
    except Exception as e:
        mysql.connection.rollback()
        return {'error': f'Booking failed: {str(e)}'}, 500
    
@app.route('/submit-review', methods=['POST'])
@login_required
def submit_review():
    if session.get('user_type') != 'Client':
        return {'error': 'Only clients can submit reviews'}, 403
    
    lawyer_id = request.json.get('lawyer_id')
    rating = request.json.get('rating')
    review_text = request.json.get('review_text', '')
    
    if not lawyer_id or not rating or rating < 1 or rating > 5:
        return {'error': 'Invalid review data'}, 400
    
    try:
        cur = mysql.connection.cursor()
        
        # Check if client has had a consultation with this lawyer
        cur.execute("""
            SELECT COUNT(*) as consultation_count
            FROM Consultations
            WHERE LawyerId = %s AND ClientId = %s AND Status = 'Completed'
        """, (lawyer_id, session['user_id']))
        
        consultation_count = cur.fetchone()['consultation_count']
        
        if consultation_count == 0:
            return {'error': 'You can only review lawyers you have consulted with'}, 403
        
        # Insert or update review
        cur.execute("""
            INSERT INTO LawyerReviews (LawyerId, ClientId, Rating, ReviewText, IsVerified)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            Rating = VALUES(Rating),
            ReviewText = VALUES(ReviewText),
            CreatedAt = CURRENT_TIMESTAMP
        """, (lawyer_id, session['user_id'], rating, review_text, True))
        
        # Update lawyer's average rating
        cur.execute("""
            UPDATE LawyerDetails ld
            SET Rating = (
                SELECT AVG(lr.Rating)
                FROM LawyerReviews lr
                WHERE lr.LawyerId = %s AND lr.IsVerified = TRUE
            ),
            TotalReviews = (
                SELECT COUNT(*)
                FROM LawyerReviews lr
                WHERE lr.LawyerId = %s AND lr.IsVerified = TRUE
            )
            WHERE ld.UserId = %s
        """, (lawyer_id, lawyer_id, lawyer_id))
        
        mysql.connection.commit()
        cur.close()
        
        return {'success': True, 'message': 'Review submitted successfully'}
        
    except Exception as e:
        mysql.connection.rollback()
        return {'error': f'Review submission failed: {str(e)}'}, 500

@app.route('/find-lawyer')
def find_lawyer():
    cur = mysql.connection.cursor()
    
    # Get all approved lawyers with comprehensive details
    cur.execute("""
        SELECT u.id, CONCAT(u.FirstName, ' ', u.LastName) as name, 
               u.FirstName, u.LastName, u.Email, u.Phone,
               ld.Specialization, ld.YearsOfExperience, ld.Photo, 
               ld.LicenseNumber, ld.Bio, ld.Education, ld.BarAssociation,
               ld.OfficeAddress, ld.ConsultationFee, ld.Languages,
               ld.PracticeAreas, ld.Achievements, ld.AvailableHours,
               ld.Rating, ld.TotalReviews, ld.PreferredContactMethod
        FROM Users u
        JOIN LawyerDetails ld ON u.id = ld.UserId
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved'
        ORDER BY ld.Rating DESC, ld.YearsOfExperience DESC
    """)
    lawyers = cur.fetchall()
    cur.close()
    
    return render_template('find_lawyer.html', lawyers=lawyers)

# Enhanced route to get lawyer details for the modal (AJAX endpoint)
@app.route('/api/lawyer-details/<int:lawyer_id>')
def api_lawyer_details(lawyer_id):
    cur = mysql.connection.cursor()
    
    # Get comprehensive lawyer details
    cur.execute("""
        SELECT u.id, CONCAT(u.FirstName, ' ', u.LastName) as name, 
               u.FirstName, u.LastName, u.Email, u.Phone,
               ld.Specialization, ld.YearsOfExperience, ld.Photo, 
               ld.LicenseNumber, ld.Bio, ld.Education, ld.BarAssociation,
               ld.OfficeAddress, ld.ConsultationFee, ld.Languages,
               ld.PracticeAreas, ld.Achievements, ld.AvailableHours,
               ld.Rating, ld.TotalReviews, ld.PreferredContactMethod
        FROM Users u
        JOIN LawyerDetails ld ON u.id = ld.UserId
        WHERE u.id = %s AND u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved'
    """, [lawyer_id])
    lawyer = cur.fetchone()
    
    if not lawyer:
        return {'error': 'Lawyer not found'}, 404
    
    # Get recent reviews for this lawyer
    cur.execute("""
        SELECT lr.Rating, lr.ReviewText, lr.CreatedAt,
               CONCAT(u.FirstName, ' ', SUBSTRING(u.LastName, 1, 1), '.') as reviewer_name
        FROM LawyerReviews lr
        JOIN Users u ON lr.ClientId = u.id
        WHERE lr.LawyerId = %s AND lr.IsVerified = TRUE
        ORDER BY lr.CreatedAt DESC
        LIMIT 5
    """, [lawyer_id])
    reviews = cur.fetchall()
    
    cur.close()
    
    # Parse JSON fields safely
    import json
    try:
        if lawyer['PracticeAreas']:
            lawyer['PracticeAreas'] = json.loads(lawyer['PracticeAreas'])
        else:
            lawyer['PracticeAreas'] = [lawyer['Specialization']]
            
        if lawyer['Achievements']:
            lawyer['Achievements'] = json.loads(lawyer['Achievements'])
        else:
            lawyer['Achievements'] = []
    except (json.JSONDecodeError, TypeError):
        lawyer['PracticeAreas'] = [lawyer['Specialization']]
        lawyer['Achievements'] = []
    
    return {
        'success': True,
        'lawyer': lawyer,
        'reviews': reviews
    }

# Route for lawyer search with filters (AJAX endpoint)
@app.route('/api/search-lawyers')
def api_search_lawyers():
    # Get search parameters
    specialization = request.args.get('specialization', '')
    location = request.args.get('location', '')
    experience_range = request.args.get('experience', '')
    rating_min = request.args.get('rating', '')
    fee_range = request.args.get('fee_range', '')
    search_term = request.args.get('search', '')
    sort_by = request.args.get('sort', 'rating')
    
    # Build the base query
    query = """
        SELECT u.id, CONCAT(u.FirstName, ' ', u.LastName) as name, 
               u.FirstName, u.LastName, u.Email, u.Phone,
               ld.Specialization, ld.YearsOfExperience, ld.Photo, 
               ld.LicenseNumber, ld.Bio, ld.Education, ld.BarAssociation,
               ld.OfficeAddress, ld.ConsultationFee, ld.Languages,
               ld.PracticeAreas, ld.Achievements, ld.AvailableHours,
               ld.Rating, ld.TotalReviews, ld.PreferredContactMethod
        FROM Users u
        JOIN LawyerDetails ld ON u.id = ld.UserId
        WHERE u.UserType = 'Lawyer' AND ld.VerificationStatus = 'Approved'
    """
    
    params = []
    
    # Add filters to the query
    if specialization:
        query += " AND ld.Specialization = %s"
        params.append(specialization)
    
    if location:
        query += " AND (ld.OfficeAddress LIKE %s)"
        params.append(f"%{location}%")
    
    if experience_range:
        if experience_range == '1-5':
            query += " AND ld.YearsOfExperience BETWEEN 1 AND 5"
        elif experience_range == '5-10':
            query += " AND ld.YearsOfExperience BETWEEN 5 AND 10"
        elif experience_range == '10-15':
            query += " AND ld.YearsOfExperience BETWEEN 10 AND 15"
        elif experience_range == '15+':
            query += " AND ld.YearsOfExperience >= 15"
    
    if rating_min:
        min_rating = float(rating_min.replace('+', ''))
        query += " AND ld.Rating >= %s"
        params.append(min_rating)
    
    if fee_range:
        if fee_range == '0-150':
            query += " AND ld.ConsultationFee <= 150"
        elif fee_range == '150-250':
            query += " AND ld.ConsultationFee BETWEEN 150 AND 250"
        elif fee_range == '250-400':
            query += " AND ld.ConsultationFee BETWEEN 250 AND 400"
        elif fee_range == '400+':
            query += " AND ld.ConsultationFee >= 400"
    
    if search_term:
        query += " AND (CONCAT(u.FirstName, ' ', u.LastName) LIKE %s OR ld.Specialization LIKE %s OR ld.Bio LIKE %s)"
        search_param = f"%{search_term}%"
        params.extend([search_param, search_param, search_param])
    
    # Add sorting
    if sort_by == 'rating':
        query += " ORDER BY ld.Rating DESC, ld.TotalReviews DESC"
    elif sort_by == 'experience':
        query += " ORDER BY ld.YearsOfExperience DESC"
    elif sort_by == 'fee-low':
        query += " ORDER BY ld.ConsultationFee ASC"
    elif sort_by == 'fee-high':
        query += " ORDER BY ld.ConsultationFee DESC"
    elif sort_by == 'name':
        query += " ORDER BY u.FirstName ASC, u.LastName ASC"
    else:
        query += " ORDER BY ld.Rating DESC"
    
    cur = mysql.connection.cursor()
    cur.execute(query, params)
    lawyers = cur.fetchall()
    cur.close()
    
    # Parse JSON fields for each lawyer
    import json
    for lawyer in lawyers:
        try:
            if lawyer['PracticeAreas']:
                lawyer['PracticeAreas'] = json.loads(lawyer['PracticeAreas'])
            else:
                lawyer['PracticeAreas'] = [lawyer['Specialization']]
                
            if lawyer['Achievements']:
                lawyer['Achievements'] = json.loads(lawyer['Achievements'])
            else:
                lawyer['Achievements'] = []
        except (json.JSONDecodeError, TypeError):
            lawyer['PracticeAreas'] = [lawyer['Specialization']]
            lawyer['Achievements'] = []
    
    return {
        'success': True,
        'lawyers': lawyers,
        'count': len(lawyers)
    }


@app.route('/practice-areas')
def practice_areas():
    return render_template('practice_areas.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/family-law')
def family_law():
    return render_template('family_law.html')

@app.route('/criminal-law')
def criminal_law():
    return render_template('criminal_law.html')

@app.route('/corporate-law')
def corporate_law():
    return render_template('corporate_law.html')

if __name__ == '__main__':
    app.run(debug=True) 

