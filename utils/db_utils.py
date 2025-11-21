import os
import sqlite3
import datetime
import logging
from contextlib import contextmanager
from typing import Generator, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Try to import from config, fallback to default
try:
    from config import DB_PATH
    # Convert Path object to string if needed
    if hasattr(DB_PATH, '__str__'):
        DB_PATH = str(DB_PATH)
except ImportError:
    # Fallback to default path if config not available
    DB_PATH = os.path.join("db", "attendance.db")

# Ensure DB_PATH is a string
if not isinstance(DB_PATH, str):
    DB_PATH = str(DB_PATH)

def get_connection():
    """Get a connection to the SQLite database"""
    try:
        # Ensure directory exists
        db_dir = os.path.dirname(DB_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Log database path for debugging (especially in deployment)
        logger.debug(f"Connecting to database at: {DB_PATH}")
        logger.debug(f"Database file exists: {os.path.exists(DB_PATH)}")
        
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row  # Enable row factory for column name access
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error(f"Database path: {DB_PATH}")
        logger.error(f"Current working directory: {os.getcwd()}")
        raise

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures proper connection cleanup.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students")
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database operation error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the database with required tables if they don't exist"""
    # Ensure DB_PATH is a string
    db_path_str = str(DB_PATH) if not isinstance(DB_PATH, str) else DB_PATH
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path_str)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Database directory created/verified: {db_dir}")
    
    logger.info(f"Initializing database at: {db_path_str}")
    logger.info(f"Database file exists: {os.path.exists(db_path_str)}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table for authentication
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('HOD', 'Class Teacher', 'Teacher')),
        name TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'ENTC',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Create students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'ENTC',
        year TEXT DEFAULT 'B.Tech',
        division TEXT DEFAULT 'B',
        image_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create subjects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    # Create student_subjects table (many-to-many relationship)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id)
    )
    ''')
    
    # Create attendance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        period TEXT NOT NULL,
        status TEXT DEFAULT 'present',
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id, date, period)
    )
    ''')
    
    # Insert default subjects if they don't exist
    # Try to import from config, fallback to hardcoded list
    try:
        from config import DEFAULT_SUBJECTS
        subjects = DEFAULT_SUBJECTS
    except ImportError:
        # Fallback to hardcoded subjects
        subjects = [
            ("FOC", "Fiber Optic Communication"),
            ("ME", "Microwave Engineering"),
            ("MC", "Mobile Computing"),
            ("Ewaste", "E-Waste Management"),
            ("DSAJ", "Data Structures and Algorithms in Java"),
            ("EEFM", "Engineering Economics and Financial Management"),
            ("ME Lab", "Microwave Engineering Lab"),
            ("Mini project", "Mini Project"),
        ]
    
    for code, name in subjects:
        cursor.execute('''
        INSERT OR IGNORE INTO subjects (code, name) VALUES (?, ?)
        ''', (code, name))
    
    # Create default users if no users exist
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    
    if user_count == 0:
        import hashlib
        
        def hash_password(password):
            return hashlib.sha256(password.encode()).hexdigest()
        
        # Sample users for all roles
        sample_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'HOD',
                'name': 'Head of Department',
                'email': 'hod@example.com',
                'department': 'ENTC'
            },
            {
                'username': 'classteacher',
                'password': 'teacher123',
                'role': 'Class Teacher',
                'name': 'Class Teacher',
                'email': 'classteacher@example.com',
                'department': 'ENTC'
            },
            {
                'username': 'teacher',
                'password': 'teacher123',
                'role': 'Teacher',
                'name': 'Subject Teacher',
                'email': 'teacher@example.com',
                'department': 'ENTC'
            }
        ]
        
        # Insert all sample users
        for user in sample_users:
            password_hash = hash_password(user['password'])
            cursor.execute('''
            INSERT INTO users (username, password_hash, role, name, email, department)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (user['username'], password_hash, user['role'], user['name'], 
                  user['email'], user['department']))
            logger.info(f"Sample user created: {user['username']} ({user['role']}) - password: {user['password']}")
        
        logger.info("Sample authentication users created successfully!")
    
    conn.commit()
    
    # Verify database was created and has tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    table_names = [table[0] for table in tables]
    logger.info(f"Database initialized. Tables created: {', '.join(table_names)}")
    
    # Check if database has data
    try:
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM attendance")
        attendance_count = cursor.fetchone()[0]
        logger.info(f"Database status - Students: {student_count}, Subjects: {subject_count}, Attendance records: {attendance_count}")
    except Exception as e:
        logger.warning(f"Could not check database data counts: {str(e)}")
    
    conn.close()
    
    db_path_str = str(DB_PATH) if not isinstance(DB_PATH, str) else DB_PATH
    logger.info(f"Database initialized successfully at: {db_path_str}")

def register_student(roll_no, name, department, year, division, image_path, subject_ids, email=None):
    """Register a new student in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Insert student
        cursor.execute('''
        INSERT INTO students (roll_no, name, email, department, year, division, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (roll_no, name, email, department, year, division, image_path))
        
        # Get the ID of the newly inserted student
        student_id = cursor.lastrowid
        
        # If no subjects provided, enroll in all subjects by default
        if not subject_ids or len(subject_ids) == 0:
            logger.info(f"No subjects provided for student {roll_no}, enrolling in all subjects by default")
            cursor.execute('SELECT id FROM subjects')
            all_subjects = cursor.fetchall()
            subject_ids = [s['id'] for s in all_subjects]
        
        # Associate student with subjects
        for subject_id in subject_ids:
            cursor.execute('''
            INSERT OR IGNORE INTO student_subjects (student_id, subject_id)
            VALUES (?, ?)
            ''', (student_id, subject_id))
        
        conn.commit()
        return student_id
    except sqlite3.IntegrityError:
        # Roll number already exists
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_students():
    """Get all students from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, roll_no, name, email, department, year, division, image_path
    FROM students
    ORDER BY roll_no
    ''')
    
    # Convert to list of dictionaries
    students = []
    for row in cursor.fetchall():
        students.append({
            "id": row["id"],
            "roll_no": row["roll_no"],
            "name": row["name"],
            "email": row["email"],
            "department": row["department"],
            "year": row["year"],
            "division": row["division"],
            "image_path": row["image_path"]
        })
    
    conn.close()
    return students

def get_students_by_subject(subject_id):
    """Get all students enrolled in a specific subject"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT s.id, s.roll_no, s.name, s.email, s.image_path
    FROM students s
    JOIN student_subjects ss ON s.id = ss.student_id
    WHERE ss.subject_id = ?
    ORDER BY s.roll_no
    ''', (subject_id,))
    
    # Convert to list of dictionaries
    students = []
    for row in cursor.fetchall():
        students.append({
            "id": row["id"],
            "roll_no": row["roll_no"],
            "name": row["name"],
            "email": row["email"],
            "image_path": row["image_path"]
        })
    
    conn.close()
    return students

def get_subjects():
    """Get all subjects from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, code, name FROM subjects ORDER BY name
    ''')
    
    subjects = cursor.fetchall()
    conn.close()
    
    return subjects

def get_subject_by_id(subject_id):
    """Get subject details by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, code, name FROM subjects WHERE id = ?
    ''', (subject_id,))
    
    row = cursor.fetchone()
    if row:
        subject = dict(row)
    else:
        subject = None
    
    conn.close()
    
    return subject

def mark_attendance(student_id, subject_id, date, period, status="present"):
    """Mark attendance for a student and send email notification"""
    print(f"MARK_ATTENDANCE CALLED: student_id={student_id}, subject_id={subject_id}, date={date}, period={period}")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Log detailed information for debugging
        logger.info(f"Marking attendance: student_id={student_id}, subject_id={subject_id}, date={date}, period={period}, status={status}")
        
        cursor.execute('''
        INSERT OR REPLACE INTO attendance (student_id, subject_id, date, period, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (student_id, subject_id, date, period, status))
        
        conn.commit()
        
        # Verify the insertion was successful by querying the record
        cursor.execute('''
        SELECT id FROM attendance 
        WHERE student_id = ? AND subject_id = ? AND date = ? AND period = ?
        ''', (student_id, subject_id, date, period))
        
        result = cursor.fetchone()
        if result:
            print(f"Successfully marked attendance with ID: {result[0]}")
            logger.info(f"Successfully marked attendance with ID: {result[0]}")
            
            # Send email notification
            try:
                from utils.email_utils import send_attendance_email
                from config import EMAIL_SEND_ON_PRESENT, EMAIL_SEND_ON_ABSENT
                
                # Check if email should be sent for this status
                should_send = (status == "present" and EMAIL_SEND_ON_PRESENT) or \
                             (status == "absent" and EMAIL_SEND_ON_ABSENT)
                
                if should_send:
                    # Get student and subject details
                    student = get_student_details(student_id)
                    subject = get_subject_by_id(subject_id)
                    
                    if student and subject:
                        send_attendance_email(
                            student_email=student.get('email', ''),
                            student_name=student.get('name', 'Student'),
                            subject_name=subject.get('name', 'Unknown Subject'),
                            date=date,
                            period=period,
                            status=status,
                            roll_no=student.get('roll_no', '')
                        )
            except Exception as email_error:
                # Don't fail attendance marking if email fails
                logger.warning(f"Failed to send email notification: {str(email_error)}")
            
            return True
        else:
            print("Attendance was not saved despite successful execution")
            logger.error("Attendance was not saved despite successful execution")
            return False
            
    except Exception as e:
        print(f"Error marking attendance: {str(e)}")
        logger.error(f"Error marking attendance: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_attendance_report(subject_id, date):
    """Get attendance report for a specific subject and date"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # First, get the most common period for this date/subject (from actual attendance records)
    cursor.execute('''
    SELECT period, COUNT(*) as count
    FROM attendance
    WHERE subject_id = ? AND date = ?
    GROUP BY period
    ORDER BY count DESC
    LIMIT 1
    ''', (subject_id, date))
    
    period_result = cursor.fetchone()
    most_common_period = period_result[0] if period_result else 'N/A'
    
    # Now get the attendance report
    cursor.execute('''
    SELECT 
        s.id, 
        s.roll_no, 
        s.name,
        s.email,
        COALESCE(a.status, 'absent') as status,
        COALESCE(a.period, ?) as period
    FROM 
        students s
    JOIN 
        student_subjects ss ON s.id = ss.student_id
    LEFT JOIN 
        attendance a ON s.id = a.student_id AND a.date = ? AND a.subject_id = ?
    WHERE 
        ss.subject_id = ?
    ORDER BY 
        s.roll_no
    ''', (most_common_period, date, subject_id, subject_id))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_class_attendance_report(date):
    """Get attendance report for all subjects on a specific date"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        s.id, 
        s.roll_no,
        s.name,
        s.email,
        sub.code as subject_code,
        sub.name as subject_name,
        COALESCE(a.status, 'absent') as status
    FROM 
        students s
    JOIN 
        student_subjects ss ON s.id = ss.student_id
    JOIN
        subjects sub ON ss.subject_id = sub.id
    LEFT JOIN 
        attendance a ON s.id = a.student_id AND a.date = ? AND a.subject_id = sub.id
    ORDER BY 
        s.roll_no, sub.name
    ''', (date,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_student_attendance_report(student_id):
    """Get detailed attendance report for a specific student"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        a.date,
        sub.code as subject_code,
        sub.name as subject_name,
        a.period,
        a.status
    FROM 
        attendance a
    JOIN
        subjects sub ON a.subject_id = sub.id
    WHERE 
        a.student_id = ?
    ORDER BY 
        a.date DESC, a.period
    ''', (student_id,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results

def get_student_attendance_summary(student_id):
    """Get summary of attendance for a student across all subjects"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        sub.id as subject_id,
        sub.code as subject_code,
        sub.name as subject_name,
        COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
        COUNT(a.id) as total_classes
    FROM 
        subjects sub
    JOIN
        student_subjects ss ON sub.id = ss.subject_id
    LEFT JOIN 
        attendance a ON sub.id = a.subject_id AND a.student_id = ?
    WHERE 
        ss.student_id = ?
    GROUP BY 
        sub.id
    ORDER BY 
        sub.name
    ''', (student_id, student_id))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results

def get_student_details(student_id):
    """Get detailed information about a student"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        id, 
        roll_no, 
        name, 
        email, 
        department, 
        year, 
        division, 
        image_path
    FROM 
        students
    WHERE 
        id = ?
    ''', (student_id,))
    
    row = cursor.fetchone()
    if row:
        student = dict(row)
    else:
        student = None
    
    conn.close()
    
    return student

def get_class_attendance_summary(date_from, date_to):
    """Get attendance summary for all students in the class within a date range"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        s.id,
        s.roll_no,
        s.name,
        s.division,
        COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
        COUNT(DISTINCT a.date || a.period || a.subject_id) as total_classes
    FROM 
        students s
    LEFT JOIN 
        attendance a ON s.id = a.student_id AND a.date BETWEEN ? AND ?
    GROUP BY 
        s.id
    ORDER BY 
        s.roll_no
    ''', (date_from, date_to))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results

def get_student_enrolled_subjects(student_id):
    """Get all subjects a student is enrolled in"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.code, s.name
        FROM subjects s
        JOIN student_subjects ss ON s.id = ss.subject_id
        WHERE ss.student_id = ?
        ORDER BY s.name
    ''', (student_id,))
    
    subjects = []
    for row in cursor.fetchall():
        subjects.append({
            'id': row['id'],
            'code': row['code'],
            'name': row['name']
        })
    
    conn.close()
    return subjects

def enroll_student_in_all_subjects(student_id):
    """Enroll a student in all available subjects"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all subjects
        cursor.execute('SELECT id FROM subjects')
        all_subjects = cursor.fetchall()
        
        if not all_subjects:
            logger.warning("No subjects found in database")
            return False
        
        # Enroll student in all subjects (ignore if already enrolled)
        enrolled_count = 0
        for subject in all_subjects:
            subject_id = subject['id']
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO student_subjects (student_id, subject_id)
                    VALUES (?, ?)
                ''', (student_id, subject_id))
                enrolled_count += 1
            except sqlite3.IntegrityError:
                # Already enrolled, skip
                pass
        
        conn.commit()
        logger.info(f"Enrolled student {student_id} in {enrolled_count} subjects")
        return True
    except Exception as e:
        logger.error(f"Error enrolling student in all subjects: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def enroll_all_students_in_all_subjects():
    """Enroll all existing students in all available subjects"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get all students
        cursor.execute('SELECT id FROM students')
        all_students = cursor.fetchall()
        
        # Get all subjects
        cursor.execute('SELECT id FROM subjects')
        all_subjects = cursor.fetchall()
        
        if not all_students:
            logger.info("No students found to enroll")
            return 0
        
        if not all_subjects:
            logger.warning("No subjects found in database")
            return 0
        
        # Enroll each student in all subjects
        total_enrollments = 0
        for student in all_students:
            student_id = student['id']
            for subject in all_subjects:
                subject_id = subject['id']
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO student_subjects (student_id, subject_id)
                        VALUES (?, ?)
                    ''', (student_id, subject_id))
                    # Check if row was actually inserted (changes() returns number of rows modified)
                    if cursor.rowcount > 0:
                        total_enrollments += 1
                except sqlite3.IntegrityError:
                    # Already enrolled, skip
                    pass
        
        conn.commit()
        logger.info(f"Enrolled {len(all_students)} students in {len(all_subjects)} subjects ({total_enrollments} new enrollments created)")
        return total_enrollments
    except Exception as e:
        logger.error(f"Error enrolling all students: {str(e)}")
        conn.rollback()
        return 0
    finally:
        conn.close()

def update_student(student_id, roll_no=None, name=None, email=None, image_path=None, subject_ids=None):
    """Update student information in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Build update query dynamically based on provided fields
        updates = []
        params = []
        
        if roll_no is not None:
            updates.append("roll_no = ?")
            params.append(roll_no)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if image_path is not None:
            updates.append("image_path = ?")
            params.append(image_path)
        
        # Update student basic info if there are updates
        if updates:
            params.append(student_id)
            cursor.execute(f'''
                UPDATE students
                SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
        
        # Update subject enrollments if provided
        if subject_ids is not None:
            # Delete existing enrollments
            cursor.execute('DELETE FROM student_subjects WHERE student_id = ?', (student_id,))
            
            # Add new enrollments
            for subject_id in subject_ids:
                cursor.execute('''
                    INSERT INTO student_subjects (student_id, subject_id)
                    VALUES (?, ?)
                ''', (student_id, subject_id))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.error(f"Error updating student: {str(e)}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating student: {str(e)}")
        return False
    finally:
        conn.close()

def delete_student(student_id):
    """Delete a student from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Delete student (cascade will handle student_subjects and attendance)
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting student: {str(e)}")
        return False
    finally:
        conn.close()