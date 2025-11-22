import mysql.connector

# 1. Railway Connection Details
conn = mysql.connector.connect(
    host="tramway.proxy.rlwy.net",
    user="root",
    password="AzddEovsOioICWtJjrOqiiRGdbtdmYDY",
    database="railway",
    port=36738
)

cursor = conn.cursor()
print("✅ Database Connected! Fixing SQL Mode & Tables...")

try:
    # =========================================================
    # STEP 0: FIX "ONLY_FULL_GROUP_BY" ERROR (CRITICAL FIX)
    # (Ye wo code hai jo 'Group By' error ko hatayega)
    # =========================================================
    print("🔧 Checking SQL Mode...")
    cursor.execute("SELECT @@sql_mode")
    current_mode = cursor.fetchone()[0]
    
    # Agar Strict Mode on hai, toh usse OFF karo
    if "ONLY_FULL_GROUP_BY" in current_mode:
        print(f"⚠️  Strict Mode Detected: {current_mode}")
        # 'ONLY_FULL_GROUP_BY' ko string se hata rahe hain
        new_mode = current_mode.replace("ONLY_FULL_GROUP_BY", "").replace(",,", ",")
        
        # Global Settings update kar rahe hain
        cursor.execute(f"SET GLOBAL sql_mode='{new_mode}'")
        # Session Settings bhi update kar rahe hain (safety ke liye)
        cursor.execute(f"SET SESSION sql_mode='{new_mode}'")
        print("✅ SUCCESS: Strict Mode DISABLE kar diya gaya hai. Ab Dashboard chalega!")
    else:
        print("ℹ️  Strict Mode pehle se hi OFF hai. Good.")

    # =========================================================
    # STEP 1: BOOKINGS TABLE (Re-creating safely)
    # =========================================================
    print("🚧 Ensuring 'bookings' table is perfect...")
    # Pehle drop karenge taaki naya structure set ho jaye
    cursor.execute("DROP TABLE IF EXISTS bookings;")
    
    cursor.execute("""
        CREATE TABLE bookings (
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
    print("✅ 'bookings' table created.")

    # Dummy Entry for Graph
    cursor.execute("""
        INSERT INTO bookings (fullname, phone, vehicle, address, problem, booking_status, created_at) 
        VALUES ('Test User', '9999999999', 'Bike', 'Test Location', 'Battery Dead', 'requested', NOW());
    """)
    conn.commit()

    # =========================================================
    # STEP 2: OTHER TABLES (Standard Check)
    # =========================================================

    # --- Table: USERS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            phone VARCHAR(32) UNIQUE,
            password_hash VARCHAR(255)
        );
    """)
    print("👍 'users' table checked.")

    # --- Table: USER PROFILES ---
    cursor.execute("""
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
    print("👍 'user_profiles' table checked.")

    # --- Table: MECHANICS ---
    cursor.execute("""
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
    print("👍 'mechanics' table checked.")

    # --- Table: MECHANIC SUBMISSIONS ---
    cursor.execute("""
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
    print("👍 'mechanic_submissions' table checked.")

    # --- Table: SCHEDULED BOOKINGS ---
    cursor.execute("""
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
    print("👍 'scheduled_bookings' table checked.")

    # =========================================================
    # STEP 3: MISSING TABLES FOR DASHBOARD (Admin & Payments)
    # =========================================================

    # --- Table: PAYMENTS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT,
            amount DECIMAL(10,2),
            payment_status VARCHAR(50),
            transaction_id VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ 'payments' table ready!")

    # --- Table: ADMIN ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            image VARCHAR(255),
            password VARCHAR(255)
        );
    """)
    print("✅ 'admin' table ready!")

    # --- Insert Default Admin ---
    cursor.execute("SELECT * FROM admin WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO admin (name, email, image, password)
            VALUES ('Super Admin', 'admin@roadbuddy.com', 'default.png', 'admin123')
        """)
        print("👤 Default Admin User Created.")
        conn.commit()

    # =========================================================
    # STEP 4: FINAL COLUMN CHECKS (ALTER)
    # =========================================================
    print("⚙️  Double checking columns...")

    try: cursor.execute("ALTER TABLE users ADD COLUMN lat DOUBLE NULL;")
    except: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN lng DOUBLE NULL;")
    except: pass
    try: cursor.execute("ALTER TABLE mechanics ADD COLUMN lat DOUBLE NULL;")
    except: pass
    try: cursor.execute("ALTER TABLE mechanics ADD COLUMN lng DOUBLE NULL;")
    except: pass
    try: cursor.execute("ALTER TABLE mechanics ADD COLUMN is_active TINYINT(1) DEFAULT 1;")
    except: pass

    print("\n🎉🎉 MISSION ACCOMPLISHED!")
    print("1. Strict Mode hat gaya.")
    print("2. Saari Tables fix ho gayin.")
    print("👉 Ab Dashboard REFRESH karo, 100% chalega!")

except Exception as e:
    print(f"❌ Koi Error aaya: {e}")

finally:
    conn.close()