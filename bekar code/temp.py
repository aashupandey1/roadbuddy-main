from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============================================================
# 1️⃣ CONFIGURATION AND INITIALIZATION
# ============================================================

app = Flask(__name__)
app.secret_key = 'your_strong_secret_key_here'

# Upload folder for mechanic photos
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'mechanic_photos')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database file path
DATABASE = os.path.join(app.root_path, 'roadbuddy.db')


# ============================================================
# 2️⃣ DATABASE + UTILS
# ============================================================

def get_db_connection():
    """Return a safe connection with timeout and row factory."""
    conn = sqlite3.connect(DATABASE, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create or update required tables safely."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1️⃣ Appointments Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                message TEXT
            );
        """)

        # 2️⃣ Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        """)

        # 3️⃣ Mechanics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mechanics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                mechanic_id TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                specialization TEXT,
                service_area TEXT,
                hourly_rate REAL,
                is_available INTEGER DEFAULT 0,
                photo_url TEXT,
                is_approved INTEGER DEFAULT 0
            );
        """)

        # ✅ Ensure new columns exist in old DBs
        columns_to_add = [
            ("email", "TEXT UNIQUE"),
            ("is_approved", "INTEGER DEFAULT 0")
        ]
        for col, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE mechanics ADD COLUMN {col} {col_type};")
            except sqlite3.OperationalError:
                pass  # already exists

        conn.commit()


def send_approval_notification(phone_number=None, email=None, mechanic_id=None, subject=None, body=None):
    """Simulate sending an approval notification (SMS/Email)."""
    import logging
    logging.basicConfig(level=logging.INFO)
    if not body:
        body = f"Congratulations! Your RoadBuddy Mechanic ID ({mechanic_id or 'N/A'}) has been approved."
    logging.info(f"[SIMULATED NOTIFICATION] To: {email or phone_number}\n{body}")
    return True


def send_email(to_email, subject, body_text, body_html=None):
    """Send email via SMTP if configured, otherwise simulate."""
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT') or 587)
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASS = os.getenv('SMTP_PASS')
    FROM_EMAIL = SMTP_USER or 'no-reply@roadbuddy.local'

    html = body_html or f"<pre>{body_text}</pre>"
    try:
        if SMTP_HOST and SMTP_USER and SMTP_PASS:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            msg.attach(MIMEText(body_text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(FROM_EMAIL, to_email, msg.as_string())
            print(f"Email sent to {to_email}")
            return True
    except Exception as e:
        print("send_email error:", e)

    print("----- EMAIL (SIMULATED) -----")
    print("To:", to_email)
    print("Subject:", subject)
    print(body_text)
    print("-----------------------------")
    return True


# ============================================================
# 3️⃣ ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    return redirect(url_for('index'))


# ---------------- USER REGISTRATION ----------------
@app.route('/user_register')
def user_register():
    return render_template('user_register.html')


@app.route('/user_login')
def user_login():
    return render_template('user_login.html')


@app.route('/process_registration', methods=['POST'])
def process_registration():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')

    if not all([name, email, phone, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('user_register'))

    hashed_password = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (full_name, email, phone, password_hash) VALUES (?, ?, ?, ?)",
                (name, email, phone, hashed_password)
            )
            conn.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('user_login'))
    except sqlite3.IntegrityError:
        flash('This email or phone number is already registered.', 'error')
        return redirect(url_for('user_register'))
    except Exception:
        flash('Unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('user_register'))


@app.route('/process_user_login', methods=['POST'])
def process_user_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('user_login'))

    login_column = 'phone' if username.startswith('+91') else 'email' if '@' in username else None
    if not login_column:
        flash('Invalid username format. Use +91 phone or email.', 'error')
        return redirect(url_for('user_login'))

    with get_db_connection() as conn:
        user = conn.execute(f"SELECT * FROM users WHERE {login_column} = ?", (username,)).fetchone()

    if user and check_password_hash(user['password_hash'], password):
        flash('Login successful! Welcome back.', 'success')
        return redirect(url_for('index'))
    else:
        flash('Invalid credentials. Try again.', 'error')
        return redirect(url_for('user_login'))


# ---------------- MECHANIC REGISTRATION ----------------
@app.route('/mechanic_register')
def mechanic_register():
    return render_template('mechanic_register.html')


@app.route('/mechanic_login')
def mechanic_login():
    return render_template('mechanic_login.html')


@app.route('/process_mechanic_register', methods=['POST'])
def process_mechanic_register():
    try:
        name = request.form.get('name')
        mechanic_id = request.form.get('mechanic_id')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        specialization = request.form.get('specialization')
        service_area = request.form.get('service_area')
        hourly_rate = float(request.form.get('hourly_rate') or 0)
        file = request.files.get('live_photo')

        if not all([name, mechanic_id, phone, email, password, specialization, service_area, hourly_rate]) or not file:
            flash('All fields including photo are required.', 'error')
            return redirect(url_for('mechanic_register'))

        hashed_password = generate_password_hash(password)
        filename = secure_filename(mechanic_id + '_' + phone + '.jpg')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        photo_url = url_for('static', filename='mechanic_photos/' + filename)

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO mechanics 
                (full_name, mechanic_id, phone, email, password_hash, specialization, service_area, hourly_rate, photo_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, mechanic_id, phone, email, hashed_password, specialization, service_area, hourly_rate, photo_url))
            conn.commit()

        flash('Registration successful! Your account is pending admin review.', 'success')
        return redirect(url_for('mechanic_login'))

    except sqlite3.IntegrityError:
        flash('Mechanic ID, email or phone already registered.', 'error')
        return redirect(url_for('mechanic_register'))
    except Exception as e:
        print("Error:", e)
        flash('Unexpected error. Try again.', 'error')
        return redirect(url_for('mechanic_register'))


@app.route('/process_mechanic_login', methods=['POST'])
def process_mechanic_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('mechanic_login'))

    login_column = 'phone' if username.startswith('+91') else 'mechanic_id'

    with get_db_connection() as conn:
        mechanic = conn.execute(f"SELECT * FROM mechanics WHERE {login_column} = ?", (username,)).fetchone()

    if mechanic and check_password_hash(mechanic['password_hash'], password):
        if mechanic['is_approved'] == 1:
            flash('Mechanic login successful!', 'success')
            return redirect(url_for('mechanic_dashboard'))
        elif mechanic['is_approved'] == 0:
            flash('Your account is pending admin approval.', 'error')
        else:
            flash('Your registration was rejected.', 'error')
    else:
        flash('Invalid credentials.', 'error')

    return redirect(url_for('mechanic_login'))


@app.route('/mechanic/dashboard')
def mechanic_dashboard():
    return render_template('mechanic_dashboard.html')


# ============================================================
# 🧑‍💼 ADMIN ROUTES
# ============================================================

@app.route('/admin/dashboard')
def admin_dashboard():
    with get_db_connection() as conn:
        pending_mechanics = conn.execute("SELECT * FROM mechanics WHERE is_approved = 0").fetchall()
    return render_template('admin_dashboard.html', mechanics=pending_mechanics)


@app.route('/admin/approve/<int:mechanic_id>', methods=['POST'])
def admin_approve(mechanic_id):
    with get_db_connection() as conn:
        mechanic = conn.execute(
            "SELECT id, phone, full_name, mechanic_id, email FROM mechanics WHERE id = ?",
            (mechanic_id,)
        ).fetchone()
        if not mechanic:
            flash("Mechanic not found.", 'error')
            return redirect(url_for('admin_dashboard'))
        conn.execute("UPDATE mechanics SET is_available = 1, is_approved = 1 WHERE id = ?", (mechanic_id,))
        conn.commit()

    subject = "Congratulations! Your RoadBuddy Account is Approved"
    body = (f"Dear {mechanic['full_name']},\n\n"
            f"Your Mechanic ID ({mechanic['mechanic_id']}) has been approved.\n"
            "You can now log in using your credentials.\n\nThanks,\nRoadBuddy Team")

    try:
        if mechanic['email']:
            send_email(mechanic['email'], subject, body)
        else:
            send_approval_notification(mechanic['phone'], mechanic['mechanic_id'])
    except Exception as e:
        print("Notification error:", e)

    flash(f"Mechanic ID {mechanic['mechanic_id']} approved and notified.", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reject/<int:mechanic_id>', methods=['POST'])
def admin_reject(mechanic_id):
    with get_db_connection() as conn:
        mechanic = conn.execute(
            "SELECT id, phone, full_name, mechanic_id, email FROM mechanics WHERE id = ?",
            (mechanic_id,)
        ).fetchone()
        if not mechanic:
            flash("Mechanic not found.", 'error')
            return redirect(url_for('admin_dashboard'))
        conn.execute("UPDATE mechanics SET is_approved = -1 WHERE id = ?", (mechanic_id,))
        conn.commit()

    subject = "Update: Your RoadBuddy Registration Status"
    body = (f"Dear {mechanic['full_name']},\n\n"
            "We regret to inform you that your registration was not approved at this time.\n\nRegards,\nRoadBuddy Team")

    try:
        if mechanic['email']:
            send_email(mechanic['email'], subject, body)
        else:
            send_approval_notification(mechanic['phone'], "Registration Rejected")
    except Exception as e:
        print("Notification error:", e)

    flash(f"Mechanic ID {mechanic['mechanic_id']} rejected and notified.", 'warning')
    return redirect(url_for('admin_dashboard'))


# ============================================================
# 4️⃣ RUN APPLICATION
# ============================================================

if __name__ == '_main_':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        try:
            init_db()
        except Exception as e:
            print("DB init error:", e)
    app.run(debug=True)

# ============================================================
# fake payment system 
# ============================================================

# ============================================================
# 💳 FAKE PAYMENT SYSTEM (Demo Mode)
# ============================================================

@app.route('/get-service', methods=['GET', 'POST'])
def get_service():
    if request.method == 'POST':
        name = request.form.get('name')
        service_type = request.form.get('service_type')
        vehicle = request.form.get('vehicle')
        date = request.form.get('date')
        time = request.form.get('time')
        amount = request.form.get('amount')

        # In a real system, you would save this data in DB
        flash(f"Proceeding to payment for {service_type} service — ₹{amount}", "info")
        return redirect(url_for('fake_payment', name=name, amount=amount, service=service_type))

    return render_template('get_service.html')


@app.route('/fake_payment', methods=['GET', 'POST'])
def fake_payment():
    name = request.args.get('name', '')
    amount = request.args.get('amount', '')
    service = request.args.get('service', '')

    if request.method == 'POST':
        flash(f"✅ Payment of ₹{amount} for {service} by {name} successful!", "success")
        return redirect(url_for('payment_receipt', name=name, amount=amount, service=service))

    return render_template('fake_payment.html', name=name, amount=amount, service=service)


@app.route('/payment_receipt')
def payment_receipt():
    import datetime
    name = request.args.get('name', '')
    amount = request.args.get('amount', '')
    service = request.args.get('service', '')
    date = datetime.datetime.now().strftime("%d-%m-%Y %I:%M %p")
    return render_template('payment_receipt.html', name=name, amount=amount, service=service, date=date)