from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_mail import Mail, Message
from flask import Flask, redirect, render_template, request, session, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'Kage0012'
s = URLSafeTimedSerializer(app.secret_key)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'dattebayo12086@gmail.com'
app.config['MAIL_PASSWORD'] = 'qkmt eqqb fvvy oijr' #App Pass

mail = Mail(app)


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'legal_aid',
    'port': '3306'
}

def create_connection():
    return mysql.connector.connect(**db_config)

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
        
        try:
            conn = create_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT * FROM clients WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered", "error")
                return render_template('client_signup.html')
            
            # Insert new client
            cursor.execute(
                "INSERT INTO clients (name, email, password) VALUES (%s, %s, %s)",
                (name, email, password)
            )
            conn.commit()
            flash("Registration successful! Please sign in.", "success")
            return redirect(url_for('signin'))
            
        except Error as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template('client_signup.html')
            
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return render_template('client_signup.html')

@app.route('/lawyer-signup', methods=['GET', 'POST'])
def lawyer_signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        license_number = request.form.get('license')
        
        # Handle file upload
        if 'license_proof' not in request.files:
            flash('No file uploaded', 'error')
            return render_template('lawyer_signup.html')
            
        license_file = request.files['license_proof']
        if license_file.filename == '':
            flash('No file selected', 'error')
            return render_template('lawyer_signup.html')
            
        try:
            conn = create_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT * FROM lawyers WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered", "error")
                return render_template('lawyer_signup.html')
            
            # Save file and insert lawyer
            file_path = f"static/uploads/{license_file.filename}"
            license_file.save(file_path)
            
            cursor.execute(
                "INSERT INTO lawyers (name, email, password, license_number, license_proof) VALUES (%s, %s, %s, %s, %s)",
                (name, email, password, license_number, file_path)
            )
            conn.commit()
            
            flash("Registration submitted! We'll review your application and contact you soon.", "success")
            return redirect(url_for('signin'))
            
        except Error as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template('lawyer_signup.html')
            
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return render_template('lawyer_signup.html')

if __name__ == '__main__':
    app.run(debug=True) 
