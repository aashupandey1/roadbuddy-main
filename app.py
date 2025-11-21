import os
import re
import logging
import secrets
import datetime
import random
import requests
from datetime import date
import io
import base64
import qrcode

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    jsonify, session
)
import mysql.connector
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------
# Configuration
# -----------------------
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'your_strong_secret_key_here')

# Uploads folder (served by Flask static)
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'mechanic_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# MySQL connection settings
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASS = os.getenv('MYSQL_PASS', 'Kunika')
MYSQL_DB = os.getenv('MYSQL_DB', 'roadbuddy')

logging.basicConfig(level=logging.INFO)

# -----------------------
# Database helpers (MySQL)
# -----------------------
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=False
    )
    print("✅ Connected to database:", os.getenv("DB_NAME"))
    return conn


def init_db():
    """Create tables/columns if they don't exist. Safe: uses IF NOT EXISTS / catches exceptions."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Existing tables you had
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                phone VARCHAR(32) UNIQUE,
                password_hash VARCHAR(255)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                dob DATE,
                phone VARCHAR(32),
                address TEXT,
                car_model VARCHAR(255),
                photo_url TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mechanics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                mechanic_id VARCHAR(255) UNIQUE,
                phone VARCHAR(32) UNIQUE,
                email VARCHAR(255),
                password_hash VARCHAR(255),
                specialization VARCHAR(255),
                service_area VARCHAR(255),
                hourly_rate DECIMAL(10,2),
                is_available TINYINT(1) DEFAULT 0,
                photo_url TEXT,
                is_approved TINYINT(1) DEFAULT 0
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mechanic_submissions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                role VARCHAR(32) NOT NULL,
                name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(32),
                aadhaar VARCHAR(64),
                shop VARCHAR(255),
                icon_url TEXT,
                dl_url TEXT,
                passport_url TEXT,
                signature_url TEXT,
                status VARCHAR(64) DEFAULT 'pending',
                submitted_at DATETIME,
                admin_notes TEXT
            );
        """)
        # Add lat/lng and is_active columns if missing (safe approach: try ALTER, ignore errors)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lat DOUBLE NULL;")
        except Exception:
            # some MySQL versions don't accept IF NOT EXISTS in ALTER; fallback:
            try:
                cur.execute("ALTER TABLE users ADD COLUMN lat DOUBLE NULL;")
            except Exception:
                pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lng DOUBLE NULL;")
        except Exception:
            try:
                cur.execute("ALTER TABLE users ADD COLUMN lng DOUBLE NULL;")
            except Exception:
                pass
        try:
            cur.execute("ALTER TABLE mechanics ADD COLUMN IF NOT EXISTS lat DOUBLE NULL;")
        except Exception:
            try:
                cur.execute("ALTER TABLE mechanics ADD COLUMN lat DOUBLE NULL;")
            except Exception:
                pass
        try:
            cur.execute("ALTER TABLE mechanics ADD COLUMN IF NOT EXISTS lng DOUBLE NULL;")
        except Exception:
            try:
                cur.execute("ALTER TABLE mechanics ADD COLUMN lng DOUBLE NULL;")
            except Exception:
                pass
        try:
            cur.execute("ALTER TABLE mechanics ADD COLUMN IF NOT EXISTS is_active TINYINT(1) DEFAULT 1;")
        except Exception:
            try:
                cur.execute("ALTER TABLE mechanics ADD COLUMN is_active TINYINT(1) DEFAULT 1;")
            except Exception:
                pass

        # bookings table for the new flow
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(255),
                phone VARCHAR(64),
                vehicle VARCHAR(255),
                address TEXT,
                problem VARCHAR(255),
                booking_status VARCHAR(64),
                request_time DATETIME,
                user_id INT,
                mechanic_id INT,
                otp VARCHAR(16),
                otp_verified TINYINT(1) DEFAULT 0,
                user_lat DOUBLE,
                user_lng DOUBLE,
                mechanic_lat DOUBLE,
                mechanic_lng DOUBLE,
                mechanic_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL
            ) ENGINE=InnoDB;
        """)

        
        # (inside init_db() where you create bookings table)
        cur.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        phone VARCHAR(64),
        vehicle VARCHAR(255),
        address TEXT,
        date DATE,
        time TIME,
        service_type VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
               """)

        conn.commit()
        logging.info("✅ Database tables/columns ensured.")
    except mysql.connector.Error:
        logging.exception("DB init error")
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

# -----------------------
# Utility helpers
# -----------------------
def allowed_file(filename):
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_phone(raw: str):
    if not raw:
        return None
    s = re.sub(r'[^\d+]', '', raw.strip())
    if s.startswith('+91') and len(s) == 13:
        return s
    if len(s) == 10 and s.isdigit():
        return '+91' + s
    return s


def save_uploaded_file(fileobj, prefix='file'):
    """Save uploaded file to UPLOAD_FOLDER and return relative static URL."""
    if not fileobj or not getattr(fileobj, 'filename', ''):
        return None
    if not allowed_file(fileobj.filename):
        return None
    fname = secure_filename(fileobj.filename)
    ts = int(datetime.datetime.utcnow().timestamp())
    unique = f"{prefix}_{ts}_{secrets.token_hex(6)}_{fname}"
    dest = os.path.join(app.config['UPLOAD_FOLDER'], unique)
    fileobj.save(dest)
    return url_for('static', filename=f"mechanic_photos/{unique}")

# ---------------------------
# EMAIL SENDER FUNCTION
# ---------------------------
def send_email(to_email, subject, body_text, body_html=None):
    url = os.getenv("GAS_EMAIL_API")  # Your Google Script Endpoint

    if not url:
        print("❌ GAS_EMAIL_API missing in .env")
        return False

    data = {
        "email": to_email,
        "otp": body_text  # OTP or message
    }

    try:
        res = requests.post(url, json=data)
        print("📨 GAS Response:", res.text)
        return True
    except Exception as e:
        print("❌ GAS API Error:", e)
        return False



# -----------------------
# Haversine helper (distance km)
# -----------------------
def haversine(lat1, lon1, lat2, lon2):
    """Return distance in kilometers between two coordinates."""
    from math import radians, sin, cos, asin, sqrt
    try:
        lat1 = float(lat1); lon1 = float(lon1); lat2 = float(lat2); lon2 = float(lon2)
    except Exception:
        return None
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

# -----------------------
# Routes
# -----------------------
@app.route('/')
def index():
    return render_template('index.html')

# -----------------------
# PROFILE — USER
# -----------------------
@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if not session.get('rb_logged_in'):
        flash('Please login first.', 'error')
        return redirect(url_for('index'))

    email = session.get('rb_user_email')
    if not email:
        flash('No user email found in session.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob = request.form.get('dob', '').strip() or None
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        car_model = request.form.get('car_model', '').strip()
        photo_file = request.files.get('photo')

        photo_url = None
        if photo_file and getattr(photo_file, 'filename', ''):
            photo_url = save_uploaded_file(photo_file, 'user_photo')

        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
            existing = cur.fetchone()
            if existing:
                cur.execute("""
                    UPDATE user_profiles
                    SET name=%s, dob=%s, phone=%s, address=%s, car_model=%s, photo_url=COALESCE(%s, photo_url)
                    WHERE email=%s
                """, (name, dob, phone, address, car_model, photo_url, email))
            else:
                cur.execute("""
                    INSERT INTO user_profiles (email, name, dob, phone, address, car_model, photo_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (email, name, dob, phone, address, car_model, photo_url))
            conn.commit()
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logging.exception("Error saving user profile")
        finally:
            if cur:
                try:
                    cur.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if photo_url:
            session['photo_url'] = photo_url

        flash('Profile saved successfully!', 'success')
        return redirect(url_for('index'))

    conn = None
    cur = None
    profile = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM user_profiles WHERE email = %s", (email,))
        profile = cur.fetchone()
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    if not profile:
        return render_template('user_profile.html', user=None)

    if request.args.get('edit') == 'true':
        return render_template('user_profile.html', user=profile)

    return render_template('user_profile_view.html', user=profile)

# -----------------------
# PROFILE — MECHANIC
# -----------------------
@app.route('/mechanic_profile', methods=['GET', 'POST'])
def mechanic_profile():
    if not session.get('rb_logged_in'):
        flash('Please login first.', 'error')
        return redirect(url_for('index'))

    if session.get('role') and session.get('role') != 'mechanic':
        return redirect(url_for('user_profile'))

    email = session.get('rb_user_email')
    if not email:
        flash('No email in session.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone_raw = request.form.get('phone', '').strip()
        phone = normalize_phone(phone_raw) or phone_raw
        aadhaar = request.form.get('aadhaar', '').strip()
        shop = request.form.get('shop', '').strip()

        dl_file = request.files.get('dl') or request.files.get('dl_image')
        passport_file = request.files.get('passport') or request.files.get('photo')
        signature_file = request.files.get('signature')

        dl_url = save_uploaded_file(dl_file, 'dl') if dl_file and getattr(dl_file, 'filename', '') else None
        passport_url = save_uploaded_file(passport_file, 'passport') if passport_file and getattr(passport_file, 'filename', '') else None
        signature_url = save_uploaded_file(signature_file, 'signature') if signature_file and getattr(signature_file, 'filename', '') else None

        submitted_at = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO mechanic_submissions
                (role, name, email, phone, aadhaar, shop, icon_url, dl_url, passport_url, signature_url, status, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                'mechanic', name, email, phone, aadhaar, shop,
                None, dl_url, passport_url, signature_url,
                'pending', submitted_at
            ))
            conn.commit()
        except Exception:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logging.exception("Error saving mechanic submission")
        finally:
            if cur:
                try:
                    cur.close()
                except Exception:
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if passport_url:
            session['photo_url'] = passport_url

        flash('Mechanic profile submitted for approval.', 'success')
        return redirect(url_for('mechanic_profile'))

    conn = None
    cur = None
    latest = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM mechanic_submissions WHERE email = %s ORDER BY submitted_at DESC LIMIT 1", (email,))
        latest = cur.fetchone()
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    return render_template('mechanic_profile.html', mech=latest)

# -----------------------
# OTP endpoints
# -----------------------
@app.route('/send_otp_email', methods=['POST'])
def send_otp_email():
    email = request.form.get('email')
    role = request.form.get('role', '').strip().lower()
    if not email:
        return jsonify({'success': False, 'message': 'Email is required.'}), 400

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    session['otp_email'] = email
    session['otp_expires'] = (datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).isoformat()
    session['role'] = role

    subject = "Your RoadBuddy OTP Code"
    body = f"Your OTP for RoadBuddy login is: {otp}\nValid for 5 minutes."
    send_email(email, subject, body)
    logging.info(f"OTP {otp} sent to {email} (role={role})")
    return jsonify({'success': True, 'message': 'OTP sent successfully!'})

@app.route('/verify_otp_email', methods=['POST'])
def verify_otp_email():
    entered_otp = request.form.get('otp')
    email = request.form.get('email') or session.get('otp_email')
    actual_otp = session.get('otp')
    expires = session.get('otp_expires')
    role = session.get('role', 'user')

    if not actual_otp or not expires:
        return jsonify({'success': False, 'message': 'No OTP session found.'}), 400

    try:
        expires_dt = datetime.datetime.fromisoformat(expires)
    except Exception:
        session.clear()
        return jsonify({'success': False, 'message': 'OTP expired or invalid.'}), 400

    if datetime.datetime.utcnow() > expires_dt:
        session.clear()
        return jsonify({'success': False, 'message': 'OTP expired.'}), 400

    if entered_otp != actual_otp:
        return jsonify({'success': False, 'message': 'Invalid OTP.'}), 400

    session['rb_logged_in'] = True
    session['rb_user_email'] = email
    session['role'] = role
    session.pop('otp', None)
    session.pop('otp_expires', None)
    session.pop('otp_email', None)

    redirect_url = url_for('index') if role == 'user' else url_for('mechanic_profile')
    return jsonify({'success': True, 'redirect': redirect_url})

# -----------------------
# Profile Redirect
# -----------------------
@app.route('/profile')
def profile_redirect():
    if not session.get('rb_logged_in'):
        flash("Please log in first.", "error")
        return redirect(url_for('index'))

    role = session.get('role')
    email = session.get('rb_user_email')

    if not role or not email:
        flash("Session expired or invalid. Please log in again.", "error")
        return redirect(url_for('index'))

    if role == 'user':
        return redirect(url_for('user_profile'))
    elif role == 'mechanic':
        return redirect(url_for('mechanic_profile'))
    else:
        return redirect(url_for('index'))

# -----------------------
# Logout
# -----------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# -----------------------
# EV CHARGERS MAP PAGE
# -----------------------
@app.route('/ev_chargers')
def ev_chargers():
    return render_template('ev_chargers.html')
# -----------------------
# EV STATIONS API (Option 1)
# -----------------------
@app.route('/api/ev_stations')
def get_ev_stations():
    from flask import request, jsonify
    import requests, logging

    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates'}), 400

    try:
        # ✅ Your personal OpenChargeMap API key
        api_key = "16218628-e4e1-4615-ad69-3cf9419c3c80"

        url = (
            "https://api.openchargemap.io/v3/poi/"
            f"?output=json&countrycode=IN&latitude={lat}&longitude={lon}"
            f"&distance=25&distanceunit=KM&maxresults=50"
            f"&key={api_key}"
        )

        headers = {
            "User-Agent": "RoadBuddyEV/1.0 (kunikagiri@example.com)"
        }

        response = requests.get(url, headers=headers, timeout=15)
        logging.info(f"OCM API status: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        if not data:
            return jsonify({'error': 'No nearby charging stations found'}), 404

        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({'error': 'OpenChargeMap API timeout'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 502
    except Exception as e:
        logging.exception("Error fetching EV station data")
        return jsonify({'error': str(e)}), 500


# New AJAX-friendly endpoint: create booking and notify mechanics within 5km
@app.route("/api/book_now", methods=["POST"])
def book_now():
    name = request.form.get("name")
    phone = request.form.get("phone")
    vehicle = request.form.get("vehicle")
    address = request.form.get("address")
    lat = request.form.get("lat")
    lng = request.form.get("lng")
    problem = request.form.get("service_type")

    if not all([name, phone, vehicle, address, lat, lng, problem]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    # TODO: Insert booking into DB
    # TODO: Notify mechanics

    return jsonify({
        "success": True,
        "message": "Booking saved",
        "booking_id": 12345,
        "notified": 3
    })


    # ✅ Find active mechanics within 5 km
    notified = 0
    try:
        cur.execute("""
            SELECT id, full_name, email, phone, lat, lng, is_active
            FROM mechanics
            WHERE email IS NOT NULL AND email != '' AND is_active = 1
        """)
        rows = cur.fetchall()

        for row in rows:
            try:
                mid, mname, memail, mphone, mlat, mlng, is_active = row
                if not mlat or not mlng or not user_lat or not user_lng:
                    continue

                dist = haversine(float(user_lat), float(user_lng), float(mlat), float(mlng))
                if dist is None or dist > 5:
                    continue

                # ✅ Email accept/decline links
                accept_link = url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='accept', _external=True)
                decline_link = url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='decline', _external=True)

                subject = f"RoadBuddy: New booking {dist:.1f} km near you"
                html = f"""
                <p>Hi {mname},</p>
                <p>A user nearby (<b>{dist:.1f} km</b>) needs help for <b>{problem}</b>.</p>
                <p><b>Location:</b> {address}</p>
                <p>
                    <a href="{accept_link}" style="color:green;font-weight:bold;">✅ Accept</a> |
                    <a href="{decline_link}" style="color:red;font-weight:bold;">❌ Decline</a>
                </p>
                <p>Booking ID: <b>{booking_id}</b></p>
                """

                send_email(memail, subject, f"New nearby booking.\nAccept: {accept_link}\nDecline: {decline_link}", html)
                notified += 1
            except Exception:
                logging.exception("Error notifying mechanic")

    except Exception:
        logging.exception("Error fetching mechanics for booking notifications")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return jsonify(success=True, booking_id=booking_id, notified=notified,
                   message=f"Booking created and {notified} nearby mechanics notified.")


# Endpoint used by mechanic email links to accept/decline
@app.route('/booking/<int:booking_id>/respond')
def booking_response(booking_id):
    """
    Mechanic clicks accept/decline link; query args: mechanic_id, action=accept|decline
    On accept: sets mechanic_id, generates OTP, sets status to 'accepted' and emails user with mechanic details + OTP.
    """
    mechanic_id = request.args.get('mechanic_id')
    action = request.args.get('action', 'decline')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        booking = cur.fetchone()
        if not booking:
            return render_template('mechanic_response.html', message='Booking not found.')
        if action == 'decline':
            return render_template('mechanic_response.html', message='You declined the booking.')
        # action == accept
        if booking.get('booking_status') and booking.get('booking_status') != 'requested':
            return render_template('mechanic_response.html', message=f'Cannot accept booking. Current status: {booking.get("booking_status")}')
        # fetch mechanic details
        cur.execute("SELECT id, full_name, phone, email FROM mechanics WHERE id = %s", (mechanic_id,))
        mech = cur.fetchone()
        mech_name = mech[1] if mech else None
        mech_phone = mech[2] if mech else None
        mech_email = mech[3] if mech else None

        otp = str(random.randint(100000, 999999))
        cur.execute("""
            UPDATE bookings
            SET mechanic_id=%s, mechanic_email=%s, booking_status=%s, otp=%s, accepted_at=CURRENT_TIMESTAMP
            WHERE id=%s
        """, (mechanic_id, mech_email, 'accepted', otp, booking_id))
        conn.commit()

        # email user about accepted booking (try find user email from bookings or users table)
        user_email = None
        # try users profile first
        try:
            # if your bookings have user_id, fetch users.email
            if booking.get('user_id'):
                cur.execute("SELECT email FROM users WHERE id = %s", (booking.get('user_id'),))
                ue = cur.fetchone()
                if ue:
                    user_email = ue[0]
        except Exception:
            pass
        # alternative: if your app stores user email in user_profiles or session, we can't access here — we try booking record (if you included email in booking form, adjust as needed)
        # send user email with mechanic details and OTP (if we have user email)
        if user_email:
            subject = "Your RoadBuddy Booking is Accepted"
            html = f"""
            <p>Your booking (ID: {booking_id}) has been accepted by {mech_name or 'a mechanic'}.</p>
            <p>Mechanic name: {mech_name or ''}<br/>Phone: {mech_phone or ''}</p>
            <p>OTP to start/verify service: <strong>{otp}</strong></p>
            <p>You can track mechanic live at: { url_for('track_booking', booking_id=booking_id, _external=True) }</p>
            """
            try:
                send_email(user_email, subject, f"Mechanic accepted. OTP: {otp}", html)
            except Exception:
                logging.exception("Failed to send booking accepted email to user")
        # return mechanic a small confirmation page (they saw the OTP here)
        return render_template('mechanic_response.html', message=f'You accepted the booking. OTP: {otp}. Booking id: {booking_id}')
    except Exception:
        logging.exception("Error handling booking response")
        return render_template('mechanic_response.html', message='An error occurred while processing your response.')
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

# Mechanic posts location updates here
@app.route('/booking/<int:booking_id>/location', methods=['POST'])
def update_location(booking_id):
    lat = request.form.get('lat') or (request.json and request.json.get('lat'))
    lng = request.form.get('lng') or (request.json and request.json.get('lng'))
    if not lat or not lng:
        return jsonify(success=False, message='Missing lat/lng'), 400
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE bookings SET mechanic_lat=%s, mechanic_lng=%s WHERE id=%s", (lat, lng, booking_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(success=True)
    except Exception:
        logging.exception("location update failed")
        return jsonify(success=False, message='DB update failed'), 500
    

# -----------------------
# Helper: notify mechanics
# -----------------------
def notify_mechanics_about_booking(booking_id, title, html_body, short_text=None, conn=None):
    notified = 0
    own_conn = False
    try:
        if conn is None:
            conn = get_db_connection()
            own_conn = True

        cur = conn.cursor()
        cur.execute("""
            SELECT id, email 
            FROM mechanics
            WHERE email IS NOT NULL AND email != '' AND is_active = 1
        """)
        rows = cur.fetchall()

        SERVER_HOST = os.getenv("SERVER_HOST")  # example: 192.168.1.47:5000

        for row in rows:
            mid = row[0]
            memail = row[1]

            # Build accept/reject URLs
            if SERVER_HOST:
                base = SERVER_HOST if SERVER_HOST.startswith("http") else f"http://{SERVER_HOST}"
                accept_link = base + url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='accept')
                decline_link = base + url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='decline')
            else:
                accept_link = url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='accept', _external=True)
                decline_link = url_for('booking_response', booking_id=booking_id, mechanic_id=mid, action='decline', _external=True)

            body = html_body.replace("{accept_link}", accept_link).replace("{decline_link}", decline_link)
            plain = short_text or f"Accept: {accept_link}\nDecline: {decline_link}"

            send_email(memail, title, plain, body)
            notified += 1

        return notified

    except Exception:
        logging.exception("Notify error")
        return 0

    finally:
        if own_conn and conn:
            conn.close()



# -----------------------
# Book Mechanic Page
# -----------------------
@app.route('/book_mechanic')
def book_mechanic():
    return render_template('book_mechanic.html')



# -----------------------
# Emergency Booking (WORKING)
# -----------------------
@app.route('/process_booking', methods=['POST'])
def process_booking():

    fullname = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    vehicle = request.form.get('vehicle', '').strip()
    address = request.form.get('address', '').strip()
    problem = request.form.get('service_type', '').strip()

    if not (fullname and phone and vehicle and address and problem):
        flash("Please fill all fields!", "error")
        return redirect(url_for('book_mechanic'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Save booking
        cur.execute("""
            INSERT INTO bookings (fullname, phone, vehicle, address, problem, booking_status, request_time)
            VALUES (%s, %s, %s, %s, %s, 'requested', NOW())
        """, (fullname, phone, vehicle, address, problem))
        conn.commit()

        booking_id = cur.lastrowid

        # Email sent to mechanics
        subject = f"RoadBuddy: Emergency Booking #{booking_id}"
        html_body = f"""
            <p>New emergency booking:</p>
            <p><b>Problem:</b> {problem}</p>
            <p><b>Address:</b> {address}</p>
            <p><b>User:</b> {fullname} — {phone}</p>
            <p>
                <a href="{{accept_link}}">Accept</a> |
                <a href="{{decline_link}}">Decline</a>
            </p>
        """

        notify_mechanics_about_booking(booking_id, subject, html_body)

        return redirect(url_for('emergency_success', booking_id=booking_id))

    except Exception:
        logging.exception("Emergency booking error")
        flash("Server error!", "error")
        return redirect(url_for('book_mechanic'))

    finally:
        cur.close()
        conn.close()



# -----------------------
# Emergency Success Page
# -----------------------
@app.route('/emergency_success/<int:booking_id>')
def emergency_success(booking_id):
    return render_template('emergency_success.html', booking_id=booking_id)

# -----------------------
# SCHEDULE BOOKING
# -----------------------
@app.route("/book_schedule", methods=["GET", "POST"])
def book_schedule():
    from datetime import date as _date

    if request.method == "GET":
        today = _date.today().strftime("%Y-%m-%d")
        return render_template("book_schedule.html", current_date=today)

    try:
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        vehicle = request.form.get("vehicle", "").strip()
        address = request.form.get("address", "").strip()
        sched_date = request.form.get("date", "").strip()
        sched_time = request.form.get("time", "").strip()
        service_type = request.form.get("service_type", "").strip()

        if not (name and phone and vehicle and address and sched_date and sched_time and service_type):
            flash("All fields required!", "error")
            return redirect(url_for("book_schedule"))

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO scheduled_bookings 
            (name, phone, vehicle, address, date, time, service_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, phone, vehicle, address, sched_date, sched_time, service_type))
        conn.commit()

        booking_id = cur.lastrowid

        subject = f"RoadBuddy: New Scheduled Booking #{booking_id}"

        html_body = f"""
        <p>A user scheduled a service on <b>{sched_date} {sched_time}</b>.</p>
        <p>Location: {address}</p>
        <p>User: {name} — {phone}</p>
        <p>
            <a href="{{accept_link}}" style="color:green;font-weight:bold;">Accept</a> |
            <a href="{{decline_link}}" style="color:red;font-weight:bold;">Decline</a>
        </p>
        """

        notify_mechanics_about_booking(booking_id, subject, html_body, conn=conn)

        return redirect(url_for("schedule_success", booking_id=booking_id))

    except:
        logging.exception("Schedule booking error")
        flash("Server error!", "error")
        return redirect(url_for("book_schedule"))

    finally:
        cur.close()
        conn.close()


@app.route('/schedule_success/<int:booking_id>')
def schedule_success(booking_id):
    return render_template('schedule_success.html', booking_id=booking_id)



# -----------------------
# ADDITION START — Mechanic OTP Verification + End Service + QR Payment
# (added without modifying any existing logic above)
# -----------------------

@app.route('/booking/<int:booking_id>/verify_otp', methods=['POST'])
def verify_booking_otp(booking_id):
    """
    Mechanic verifies OTP before starting/ending service.
    Accepts form POST (application/x-www-form-urlencoded) or JSON body.
    """
    otp = request.form.get("otp") or (request.json and request.json.get("otp"))
    if not otp:
        return jsonify(success=False, message="OTP is required"), 400

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT otp FROM bookings WHERE id=%s", (booking_id,))
        record = cur.fetchone()
        if not record:
            return jsonify(success=False, message="Booking not found"), 404

        if str(record.get("otp")).strip() == str(otp).strip():
            cur.execute("UPDATE bookings SET otp_verified=1 WHERE id=%s", (booking_id,))
            conn.commit()
            return jsonify(success=True, message="OTP verified successfully.")
        else:
            return jsonify(success=False, message="Invalid OTP entered."), 400
    except Exception:
        logging.exception("verify_booking_otp error")
        return jsonify(success=False, message="Server error"), 500
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


@app.route('/booking/<int:booking_id>/end_service', methods=['POST'])
def end_service(booking_id):
    """
    After OTP verified, this endpoint marks booking completed and returns an HTML snippet with UPI QR.
    It checks otp_verified flag — returns 403 if not verified.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT otp_verified, mechanic_email FROM bookings WHERE id=%s", (booking_id,))
        row = cur.fetchone()
        if not row:
            return jsonify(success=False, message="Booking not found"), 404
        if not row.get("otp_verified"):
            return jsonify(success=False, message="OTP not verified yet"), 403

        # Generate UPI QR code (you can change upi_id and amount logic)
        upi_id = "mechanic@upi"
        amount = 500  # static for now
        upi_uri = f"upi://pay?pa={upi_id}&pn=RoadBuddyMechanic&am={amount}&cu=INR"
        qr_img = qrcode.make(upi_uri)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        # mark booking completed
        cur.execute("UPDATE bookings SET booking_status='completed', completed_at=NOW() WHERE id=%s", (booking_id,))
        conn.commit()

        html = f"""
        <div style="text-align:center;font-family:Arial,Helvetica,sans-serif;">
            <h2>✅ Service Completed</h2>
            <p>Scan this QR to pay the mechanic (UPI ID: <b>{upi_id}</b>, Amount: ₹{amount}):</p>
            <img src="data:image/png;base64,{qr_base64}" width="220" alt="Payment QR"><br/>
            <p style="font-size:0.9rem;color:#666;">If you prefer, share the UPI ID with your UPI app and pay manually.</p>
        </div>
        """
        return html
    except Exception:
        logging.exception("end_service error")
        return jsonify(success=False, message="Server error"), 500
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass


# -----------------------
# correct geolocation address
# -----------------------

@app.route("/api/reverse_geocode")
def reverse_geocode():
    import requests

    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return jsonify({"error": "Missing coordinates"}), 400

    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "RoadBuddy-App"}

    try:
        response = requests.get(url, headers=headers)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
 # -----------------------
# Admin Panel
# -----------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # ---- Fetch counts for top cards ----
    cur.execute("SELECT COUNT(*) AS total FROM users")
    total_users = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM mechanics")
    total_mechanics = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM mechanics WHERE is_approved = 1")
    approved_mechanics = cur.fetchone()['total']

    # ✅ Count pending submissions from mechanic_submissions table
    cur.execute("SELECT COUNT(*) AS total FROM mechanic_submissions WHERE status = 'pending'")
    pending_submissions = cur.fetchone()['total']

    # Combine pending counts if you also want to include unapproved mechanics
    cur.execute("SELECT COUNT(*) AS total FROM mechanics WHERE is_approved = 0")
    pending_mechanics = cur.fetchone()['total'] + pending_submissions

    cur.execute("SELECT COUNT(*) AS total FROM bookings")
    total_bookings = cur.fetchone()['total']

    # ✅ Safely check if 'payments' table exists
    try:
        cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM payments")
        total_earnings = cur.fetchone()['total']
    except Exception:
        total_earnings = 0

    # ---- Fetch mechanics waiting for approval ----
    cur.execute("""
        SELECT id, name AS full_name, phone, aadhaar AS specialization, shop AS service_area,
               status, submitted_at, passport_url
        FROM mechanic_submissions
        WHERE status = 'pending'
        ORDER BY submitted_at DESC
    """)
    pending_mechanic_submissions = cur.fetchall()

    cur.execute("""
        SELECT id, full_name, phone, specialization, service_area, is_approved
        FROM mechanics
        WHERE is_approved = 0
    """)
    pending_mechanics_list = cur.fetchall()

    # Merge pending from both sources for unified display
    all_pending_mechanics = pending_mechanics_list + pending_mechanic_submissions

    # ---- Chart data ----
    cur.execute("""
        SELECT MONTHNAME(created_at) AS month, COUNT(*) AS count
        FROM bookings GROUP BY MONTH(created_at)
    """)
    bookings_data = cur.fetchall()

    try:
        cur.execute("""
            SELECT MONTHNAME(created_at) AS month, SUM(amount) AS total
            FROM payments GROUP BY MONTH(created_at)
        """)
        earnings_data = cur.fetchall()
    except Exception:
        earnings_data = []

    cur.execute("SELECT service_area AS area, COUNT(*) AS count FROM mechanics GROUP BY service_area")
    area_data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_mechanics=total_mechanics,
        approved_mechanics=approved_mechanics,
        pending_mechanics=pending_mechanics,
        total_bookings=total_bookings,
        total_earnings=total_earnings,
        bookings_data=bookings_data,
        earnings_data=earnings_data,
        area_data=area_data,
        pending_mechanics_list=all_pending_mechanics
    )


# ✅ APPROVE mechanic submission
@app.route("/admin/approve_submission/<int:submission_id>", methods=["POST"])
def admin_approve_submission(submission_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # Get submission data
        cur.execute("SELECT * FROM mechanic_submissions WHERE id = %s", (submission_id,))
        submission = cur.fetchone()

        if not submission:
            flash("Submission not found.", "danger")
            return redirect(url_for("admin_dashboard"))

        # Insert into mechanics table
        cur.execute("""
            INSERT INTO mechanics (full_name, phone, email, photo_url, specialization, service_area, is_approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            submission["name"],
            submission["phone"],
            submission["email"],
            submission.get("passport_url"),
            submission.get("aadhaar"),
            submission.get("shop"),
            1
        ))

        # Mark submission as approved
        cur.execute("UPDATE mechanic_submissions SET status = 'approved' WHERE id = %s", (submission_id,))
        conn.commit()

        flash("✅ Mechanic submission approved successfully!", "success")
    except Exception as e:
        conn.rollback()
        print("Error approving submission:", e)
        flash("❌ Error approving submission.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))


# ✅ REJECT mechanic submission
@app.route("/admin/reject_submission/<int:submission_id>", methods=["POST"])
def admin_reject_submission(submission_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE mechanic_submissions SET status = 'rejected' WHERE id = %s", (submission_id,))
        conn.commit()
        flash("❌ Mechanic submission rejected successfully!", "warning")
    except Exception as e:
        conn.rollback()
        print("Error rejecting submission:", e)
        flash("⚠️ Error rejecting submission.", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))


# ✅ Admin Mechanics Page
@app.route('/admin/mechanics')
def admin_mechanics():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM mechanics")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM mechanics WHERE is_approved = 1")
    approved = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM mechanics WHERE is_approved = 0")
    pending = cur.fetchone()['total']

    cur.execute("SELECT * FROM mechanics ORDER BY id DESC")
    all_mechanics = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin_mechanics.html',
        total=total,
        approved=approved,
        pending=pending,
        all_mechanics=all_mechanics
    )


@app.route('/admin/bookings')
def admin_bookings():
    return render_template('admin_bookings.html')


@app.route('/admin/reports')
def admin_reports():
    return render_template('admin_reports.html')


@app.route('/admin/settings')
def admin_settings():
    return render_template('admin_settings.html')


# -----------------------
# Real Admin profile
# -----------------------

@app.route('/admin/profile')
def admin_profile():
    # assuming you have an 'admin' table
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT name, email, image FROM admin WHERE id = 1")
    admin = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('admin_profile.html', admin=admin)





# -----------------------
# App Start
# -----------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')

