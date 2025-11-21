# Deployment Guide

## Common Deployment Issues and Solutions

### Issue: Data Not Showing After Deployment

This is a common issue when deploying to platforms like Streamlit Cloud, Heroku, Railway, etc. Here are the most common causes and solutions:

### 1. Database Path Issues

**Problem:** The database file might be in a different location or not accessible in deployment.

**Solution:**

- The database is stored at: `db/attendance.db` (relative to project root)
- Ensure the `db` directory is created and writable
- Check file permissions in deployment environment

**Environment Variables:**
You can override the database path using:
```bash
export DATABASE_PATH="/path/to/your/database.db"
```

### 2. Ephemeral File Systems

**Problem:** Some deployment platforms (like Heroku) use ephemeral file systems that reset on each deployment.

**Solution:**

- Use a persistent database service (PostgreSQL, MySQL) instead of SQLite
- Or use cloud storage for the database file
- Consider using environment variables to point to a persistent storage location

### 3. Database Not Initialized

**Problem:** The database might not be initialized on first deployment.

**Solution:**

- The app automatically initializes the database on startup
- Check logs for "Database initialized successfully" message
- If initialization fails, check file permissions

### 4. Missing Data After Deployment

**Problem:** Your local database data doesn't appear in deployment.

**Solution:**

- **Local database is NOT automatically synced to deployment**
- You need to either:
  1. **Export and import data:**
     ```bash
     # Export from local
     sqlite3 db/attendance.db .dump > database_backup.sql
     
     # Import to deployment (if you have database access)
     sqlite3 db/attendance.db < database_backup.sql
     ```
  
  2. **Use a migration script:**
     - Create a script to populate initial data
     - Run it after deployment
  
  3. **Use environment variables for initial data:**
     - Store initial data in a JSON/CSV file
     - Load it on first startup

### 5. File Path Issues

**Problem:** Relative paths might not work in deployment.

**Solution:**

- All paths are now handled using `Path` objects
- Paths are relative to the project root
- Check that all directories are created:
  - `db/` - Database files
  - `faces/` - Student face images
  - `excel_exports/` - Export files
  - `db/sessions/` - Session files

### 6. Check Database Status

The app logs database status on startup. Check logs for:
```
Database path: /path/to/db/attendance.db
Database file exists: True/False
Database ready - Students: X, Subjects: Y, Attendance: Z
```

### 7. Deployment Platform Specific

#### Streamlit Cloud

- Database persists in the app's file system
- Data survives restarts but NOT redeployments
- Use Streamlit Secrets for sensitive data
- Consider using Streamlit's database integrations

#### Heroku

- Uses ephemeral file system
- Database resets on each deployment
- **Must use external database** (PostgreSQL addon recommended)

#### Railway/Render

- File system persists
- Database should work as-is
- Check file permissions

### Quick Diagnostic Checklist

1. ✅ Check if database file exists: `ls -la db/attendance.db`
2. ✅ Check database initialization logs
3. ✅ Verify file permissions: `chmod 644 db/attendance.db`
4. ✅ Check if tables exist: Run `sqlite3 db/attendance.db ".tables"`
5. ✅ Verify data exists: Run `sqlite3 db/attendance.db "SELECT COUNT(*) FROM students;"`

### Recommended: Use External Database for Production

For production deployments, consider migrating to:

- **PostgreSQL** (recommended)
- **MySQL**
- **SQLite with cloud storage** (S3, Google Cloud Storage)

This ensures data persistence across deployments.

### Environment Variables for Deployment

```bash
# Database
DATABASE_PATH=/app/data/attendance.db  # Optional: override database path
DEPLOYMENT_DATA_DIR=/app/data          # Optional: override data directory

# Application
DEPARTMENT=ENTC
YEAR=B.Tech
DIVISION=B

# Email (if using)
EMAIL_ENABLED=true
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USERNAME=resend
SMTP_PASSWORD=your-api-key
EMAIL_FROM=attendance@yourdomain.com

# Google Sheets (if using)
GOOGLE_SHEETS_ENABLED=true
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/data/google_credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
```

### Troubleshooting Commands

```bash
# Check database status
python -c "from utils.db_utils import get_connection; conn = get_connection(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM students'); print(cursor.fetchone()[0]); conn.close()"

# Initialize database manually
python -c "from utils.db_utils import init_db; init_db()"

# Check database path
python -c "from config import DB_PATH; print(DB_PATH)"
```

