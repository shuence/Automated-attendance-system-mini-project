# Viva Questions - Automated Attendance System

## Table of Contents

1. [Project Overview & Introduction](#1-project-overview--introduction)
2. [Technology Stack & Tools](#2-technology-stack--tools)
3. [System Architecture & Design](#3-system-architecture--design)
4. [Facial Recognition & Deep Learning](#4-facial-recognition--deep-learning)
5. [Database Design & Management](#5-database-design--management)
6. [Implementation Details](#6-implementation-details)
7. [Features & Functionality](#7-features--functionality)
8. [Performance & Accuracy](#8-performance--accuracy)
9. [Challenges & Solutions](#9-challenges--solutions)
10. [Security & Privacy](#10-security--privacy)
11. [Testing & Validation](#11-testing--validation)
12. [Future Enhancements](#12-future-enhancements)
13. [ESP32-CAM Integration](#13-esp32-cam-integration)
14. [Data Export & Reporting](#14-data-export--reporting)

---

## 1. Project Overview & Introduction

### Q1.1: What is the main objective of your project?

**Answer:** The main objective is to develop an automated attendance system using facial recognition technology that eliminates proxy attendance, saves time, reduces administrative burden, and provides accurate attendance tracking for educational institutions.

### Q1.2: Why did you choose facial recognition over other biometric methods?

**Answer:** Facial recognition is contactless, non-intrusive, can identify multiple students simultaneously from a single image, eliminates proxy attendance, requires no specialized hardware beyond a camera, and is hygienic (important post-pandemic).

### Q1.3: What are the limitations of traditional attendance systems?

**Answer:**

- Manual roll calls consume valuable class time (5-10 minutes per class)
- Susceptible to proxy attendance (students marking attendance for absent friends)
- Paper-based records are difficult to manage and analyze
- Prone to human errors in data entry
- Time-consuming administrative work for compiling records

### Q1.4: What problem does your system solve?

**Answer:** The system solves:

- Proxy attendance fraud
- Time wastage during manual roll calls
- Administrative burden of managing paper records
- Data entry errors
- Lack of real-time attendance analytics

### Q1.5: Who are the target users of your system?

**Answer:**

- Teachers/Instructors (for marking attendance)
- Class Teachers (for monitoring class attendance)
- HOD (Head of Department) for department-wide oversight
- Administrative staff (for generating reports)

### Q1.6: What is the scope of your project?

**Answer:** The system is designed for ENTC B.Tech B division students, supporting multiple subjects, real-time attendance marking from classroom images, comprehensive reporting, and data export capabilities.

---

## 2. Technology Stack & Tools

### Q2.1: Why did you choose Python for this project?

**Answer:** Python has excellent libraries for machine learning (TensorFlow, Keras), computer vision (OpenCV), web development (Streamlit), and data manipulation (Pandas), making it ideal for this AI-based application.

### Q2.2: What is Streamlit and why did you use it?

**Answer:** Streamlit is a Python framework for building web applications quickly. It's perfect for data science and ML projects, requires minimal code for interactive UIs, and doesn't require frontend development skills.

### Q2.3: What is DeepFace and what does it provide?

**Answer:** DeepFace is an open-source facial recognition library that provides a unified interface to multiple state-of-the-art face recognition models (VGG-Face, FaceNet, ArcFace) and face detectors (OpenCV, MTCNN, RetinaFace).

### Q2.4: Why did you choose SQLite as the database?

**Answer:** SQLite is lightweight, serverless, requires no separate installation, stores data in a single file (portable), and is sufficient for small to medium-scale applications like this attendance system.

### Q2.5: What role does OpenCV play in your system?

**Answer:** OpenCV is used for:

- Image loading and preprocessing
- Face detection (using Haar Cascades or other detectors)
- Image manipulation and cropping
- Basic computer vision operations

### Q2.6: What is TensorFlow and why is it needed?

**Answer:** TensorFlow is the backend deep learning framework that powers the facial recognition models in DeepFace. It provides the computational engine for neural network inference.

### Q2.7: What libraries are used for data visualization?

**Answer:**

- Plotly: For interactive charts and graphs
- Matplotlib: For static visualizations
- Seaborn: For statistical visualizations

### Q2.8: How does Pandas help in your project?

**Answer:** Pandas is used for:

- Converting database query results to DataFrames
- Data filtering, sorting, and manipulation
- Preparing data for reports and exports
- Data analysis and aggregation

---

## 3. System Architecture & Design

### Q3.1: Explain the overall architecture of your system

**Answer:** The system follows a modular architecture:

- **Frontend:** Streamlit web interface (app.py)
- **Backend:** Python application logic
- **Facial Recognition Engine:** DeepFace library (deepface_utils.py)
- **Database Layer:** SQLite database (db_utils.py)
- **Storage:** Face images in `faces/` directory, database in `db/` directory

### Q3.2: What is the workflow of your system?

**Answer:**

1. Student Registration: Upload student photo and details → Save to database and faces directory
2. Attendance Marking: Upload classroom image → Face detection → Face recognition → Update attendance records
3. Reports: Query database → Filter data → Display/Export reports

### Q3.3: How is your code organized? Explain the project structure

**Answer:**

- `app.py`: Main application with Streamlit UI
- `config.py`: Configuration management
- `utils/`: Utility modules
  - `db_utils.py`: Database operations
  - `deepface_utils.py`: Facial recognition functions
  - `auth_utils.py`: Authentication utilities
  - `session_utils.py`: Session management
  - `email_utils.py`: Email notifications
  - `sheets_utils.py`: Google Sheets integration
- `db/`: Database files
- `faces/`: Student face images
- `excel_exports/`: Exported reports

### Q3.4: What design pattern did you follow?

**Answer:** Modular design pattern - separating concerns into different modules (UI, database, facial recognition, utilities) for maintainability, reusability, and testability.

### Q3.5: How does the system handle user authentication?

**Answer:** The system uses role-based authentication with three roles (HOD, Class Teacher, Teacher), password hashing for security, and session management to track logged-in users.

### Q3.6: What is the role of the configuration file (config.py)?

**Answer:** It centralizes all configuration settings including:

- File paths (faces directory, database path, exports directory)
- DeepFace model settings (model name, threshold, detector backend)
- ESP32-CAM settings
- Email and Google Sheets integration settings
- Department, year, and division information

---

## 4. Facial Recognition & Deep Learning

### Q4.1: How does facial recognition work in your system?

**Answer:**

1. Face Detection: Locate all faces in the classroom image
2. Feature Extraction: Convert each detected face to a numerical embedding (vector) using a deep learning model
3. Comparison: Compare embeddings of detected faces with registered student embeddings
4. Matching: If distance between embeddings is below threshold, it's a match

### Q4.2: What is a facial embedding?

**Answer:** A facial embedding is a numerical vector (typically 128-512 dimensions) that represents unique facial features in a high-dimensional space. Similar faces have embeddings that are close together in this space.

### Q4.3: What models are available in DeepFace and which one did you use?

**Answer:** Available models:

- VGG-Face
- FaceNet
- Facenet512 (default in our system)
- ArcFace (highest accuracy)
- OpenFace
- DeepFace
- SFace

We use Facenet512 by default, but users can select ArcFace for maximum accuracy.

### Q4.4: What is the difference between VGG-Face, FaceNet, and ArcFace?

**Answer:**

- **VGG-Face:** Based on VGG-16 CNN architecture, trained on classification task
- **FaceNet:** Uses triplet loss function, directly optimizes embedding space
- **ArcFace:** Uses additive angular margin loss, most discriminative, highest accuracy

### Q4.5: What is a threshold in facial recognition?

**Answer:** Threshold is a similarity score (0-1) that determines if two faces match. Lower threshold = stricter matching (fewer false positives but more false negatives). Default is 0.6, but 0.3-0.4 is recommended for high accuracy.

### Q4.6: What face detection backends are available?

**Answer:**

- **opencv:** Fast but less accurate (default)
- **MTCNN:** Highly accurate, detects faces at angles, slower
- **RetinaFace:** Very accurate, good for challenging conditions
- **ssd:** Fast but lower accuracy
- **dlib:** HOG + SVM based, moderate accuracy

### Q4.7: How does the system handle multiple faces in one image?

**Answer:** The system:

1. Detects all faces in the image
2. Extracts embeddings for each detected face
3. Compares each detected face against all registered students
4. Matches each face to the best-matching student (one-to-one matching)
5. Prevents duplicate matches

### Q4.8: What happens if a face is not recognized?

**Answer:** The system marks that student as absent. The system shows:

- List of recognized (present) students
- List of registered students not found (absent)
- Confidence scores for matches

### Q4.9: What factors affect recognition accuracy?

**Answer:**

- Image quality (resolution, focus)
- Lighting conditions
- Face pose (frontal vs. profile)
- Occlusions (glasses, masks, hands)
- Quality of reference image
- Model selection
- Threshold setting

### Q4.10: How can accuracy be improved?

**Answer:**

- Use ArcFace model (highest accuracy)
- Use MTCNN detector
- Lower threshold (0.3-0.4)
- High-quality registration photos
- Good lighting in classroom
- Frontal face images
- Face alignment

### Q4.11: What is face alignment and why is it important?

**Answer:** Face alignment rotates and scales the face to a standard position (eyes at same level, face centered). This improves recognition accuracy by normalizing face orientation.

### Q4.12: How does the system handle false positives and false negatives?

**Answer:**

- **False Positives:** Prevented by using appropriate threshold and high-quality models
- **False Negatives:** Reduced by improving image quality, lighting, and using better models
- System shows confidence scores to help identify uncertain matches

---

## 5. Database Design & Management

### Q5.1: What database schema did you design?

**Answer:** The database has these main tables:

- `users`: User authentication (username, password_hash, role, name, email)
- `students`: Student information (name, roll_number, class, image_path)
- `subjects`: Subject details (code, name)
- `student_subjects`: Many-to-many relationship between students and subjects
- `attendance`: Attendance records (student_id, subject_id, date, status, period)
- `sessions`: Active attendance sessions

### Q5.2: Why did you use a many-to-many relationship for students and subjects?

**Answer:** A student can enroll in multiple subjects, and a subject has multiple students. The `student_subjects` junction table allows this flexible relationship.

### Q5.3: How do you ensure data integrity?

**Answer:**

- Foreign key constraints
- Unique constraints (e.g., unique roll numbers)
- Check constraints (e.g., valid roles)
- Transaction management (commit/rollback)
- Input validation

### Q5.4: What is the purpose of the sessions table?

**Answer:** The sessions table tracks active attendance sessions, allowing the system to:

- Prevent duplicate attendance marking
- Track when attendance was taken
- Support session-based attendance management

### Q5.5: How do you handle database migrations?

**Answer:** The `migrate_db.py` utility handles database schema updates, ensuring the database structure is up-to-date when the application starts.

### Q5.6: What indexes did you create and why?

**Answer:** Indexes are created on frequently queried columns like:

- `student_id` in attendance table (for fast lookups)
- `date` in attendance table (for date range queries)
- `roll_number` in students table (for unique identification)

### Q5.7: How do you prevent duplicate attendance records?

**Answer:** By checking if attendance already exists for a student, subject, date, and period combination before inserting a new record.

---

## 6. Implementation Details

### Q6.1: How does the student registration process work?

**Answer:**

1. User enters student details (name, roll number, class)
2. User uploads student photo
3. System validates inputs
4. Photo is saved to `faces/` directory with filename as roll number
5. Student record is inserted into database
6. User selects subjects for the student
7. Student-subject relationships are created

### Q6.2: How does the attendance marking process work?

**Answer:**

1. User selects subject and period
2. User uploads classroom image (or captures from ESP32-CAM)
3. System calls `verify_faces()` function
4. Face detection identifies all faces in image
5. For each detected face, extract embedding
6. Compare with all registered student embeddings
7. If distance < threshold, mark as present
8. Update attendance records in database
9. Display results (present/absent lists)

### Q6.3: How does the system handle image uploads?

**Answer:**

- Streamlit file uploader accepts image files
- Image is saved temporarily
- OpenCV/PIL reads and processes the image
- Image is passed to face detection/recognition
- Temporary files are cleaned up

### Q6.4: How does the report generation work?

**Answer:**

1. User selects filters (date range, subject, student, class)
2. System constructs SQL query based on filters
3. Query results are loaded into Pandas DataFrame
4. Data is processed and formatted
5. Report is displayed in tabular format
6. User can export to Excel

### Q6.5: How does Excel export work?

**Answer:**

- Pandas DataFrame is converted to Excel format using `openpyxl`
- File is saved to `excel_exports/` directory
- Streamlit provides download button
- File includes formatted data with proper columns

### Q6.6: How does the dashboard display statistics?

**Answer:**

- Queries database for attendance data
- Calculates metrics (total students, present count, absent count, percentage)
- Uses Streamlit metrics widgets to display
- Creates visualizations using Plotly

### Q6.7: How does session management work?

**Answer:**

- Streamlit session state stores user login information
- Session utilities manage active sessions
- Sessions are tracked in database
- Session timeout/logout functionality

### Q6.8: How does error handling work in your system?

**Answer:**

- Try-except blocks around critical operations
- Logging for debugging (app.log, deepface.log)
- User-friendly error messages
- Graceful degradation (e.g., if DeepFace unavailable)

---

## 7. Features & Functionality

### Q7.1: What are the main features of your system?

**Answer:**

1. Student Registration with photo upload
2. Real-time attendance marking from images
3. Teacher Dashboard with statistics
4. Individual student reports
5. Class-wise reports
6. Subject-wise reports
7. Date range filtering
8. Excel export
9. Attendance analytics and visualizations
10. ESP32-CAM integration
11. Email notifications
12. Google Sheets integration

### Q7.2: How does the dashboard help teachers?

**Answer:** The dashboard provides:

- Quick overview of attendance statistics
- Present/absent student lists
- Attendance percentages
- Visual charts and graphs
- Recent attendance history

### Q7.3: What filtering options are available in reports?

**Answer:**

- Date range (from date to date)
- Subject filter
- Student filter
- Class filter
- Period filter

### Q7.4: What analytics features are provided?

**Answer:**

- Attendance percentage per student
- Attendance trends over time
- Recognition statistics
- Class attendance patterns
- Subject-wise attendance analysis

### Q7.5: How does the system handle multiple subjects?

**Answer:** Students can be enrolled in multiple subjects. When taking attendance, the teacher selects the subject, and attendance is recorded specifically for that subject.

### Q7.6: What is the period field used for?

**Answer:** The period field allows tracking attendance for different time slots (e.g., Period 1, Period 2) on the same day for the same subject.

### Q7.7: How does the system handle different user roles?

**Answer:**

- **HOD:** Full access to all features, department-wide view
- **Class Teacher:** Access to their class, can view and manage attendance
- **Teacher:** Can mark attendance and view reports for assigned subjects

---

## 8. Performance & Accuracy

### Q8.1: What is the accuracy of your system?

**Answer:** With optimal settings (ArcFace model, MTCNN detector, threshold 0.3-0.4), the system achieves 98-99% accuracy. With default settings (Facenet512, opencv), accuracy is around 94-96%.

### Q8.2: How long does it take to process a classroom image?

**Answer:** Processing time depends on:

- Number of faces in image
- Number of registered students
- Model used (ArcFace slower than VGG-Face)
- Hardware (CPU vs GPU)
- Typically 5-15 seconds for 20-30 students on CPU

### Q8.3: How does the system scale with more students?

**Answer:** Current implementation uses linear search (compares against all students). For large-scale deployment (1000+ students), this could be slow. Future improvement: use vector database (Faiss, Milvus) for faster similarity search.

### Q8.4: What are the performance bottlenecks?

**Answer:**

- Face detection time (especially with MTCNN)
- Embedding extraction for each face
- Comparison with all registered students
- Database queries for large datasets

### Q8.5: How can performance be improved?

**Answer:**

- Use GPU for faster deep learning inference
- Pre-compute and cache student embeddings
- Use vector database for fast similarity search
- Optimize face detection (use faster detector for initial screening)
- Parallel processing for multiple faces

### Q8.6: What metrics do you use to evaluate performance?

**Answer:**

- Recognition accuracy (True Positives / Total)
- False Positive Rate
- False Negative Rate
- Processing time
- Confidence scores

### Q8.7: How do you measure system accuracy?

**Answer:**

- Test with known students in controlled conditions
- Compare system results with manual verification
- Calculate precision, recall, and F1-score
- Monitor confidence scores

---

## 9. Challenges & Solutions

### Q9.1: What were the main challenges you faced?

**Answer:**

1. **Accuracy issues:** Solved by model selection and threshold tuning
2. **Lighting variations:** Addressed through guidelines and preprocessing
3. **Multiple face detection:** Implemented one-to-one matching algorithm
4. **Performance:** Optimized with appropriate model/detector selection
5. **Database design:** Designed flexible schema for multiple subjects

### Q9.2: How did you handle poor lighting conditions?

**Answer:**

- Provided guidelines for good lighting
- Recommended MTCNN detector (handles shadows better)
- Suggested histogram equalization preprocessing
- Encouraged proper camera setup

### Q9.3: How did you handle students with glasses or masks?

**Answer:**

- Recommended registering multiple photos (with/without glasses)
- Used lower threshold for stricter matching
- Suggested ArcFace model (better with variations)
- Provided guidelines for registration photos

### Q9.4: How did you prevent duplicate attendance marking?

**Answer:**

- Check database before inserting attendance record
- Use unique constraint on (student_id, subject_id, date, period)
- Session-based tracking

### Q9.5: How did you handle cases where face is not detected?

**Answer:**

- System logs warning and continues
- Student is marked as absent
- User is notified about detection issues
- Suggested using better detector (MTCNN)

### Q9.6: How did you handle large image files?

**Answer:**

- Streamlit handles file uploads efficiently
- Images are processed in memory
- Temporary files are cleaned up
- No permanent storage of classroom images (only face crops if needed)

---

## 10. Security & Privacy

### Q10.1: How do you secure user passwords?

**Answer:** Passwords are hashed using secure hashing algorithms (bcrypt or similar) before storing in database. Plain text passwords are never stored.

### Q10.2: How do you protect facial data?

**Answer:**

- Face images stored in secure directory
- Access controlled through authentication
- Images not exposed through web interface
- Database access restricted

### Q10.3: What privacy concerns exist with facial recognition?

**Answer:**

- Collection of biometric data
- Storage of facial images
- Potential for misuse
- Need for consent and transparency

### Q10.4: How would you address privacy concerns in production?

**Answer:**

- Implement data encryption
- Obtain explicit consent from students
- Comply with data protection regulations (GDPR, etc.)
- Implement data retention policies
- Provide data deletion options
- Secure database and file storage

### Q10.5: How do you prevent unauthorized access?

**Answer:**

- Role-based authentication
- Session management
- Password protection
- Secure file storage
- Database access controls

### Q10.6: What security measures are in place for ESP32-CAM?

**Answer:**

- HTTP Basic Authentication (username/password)
- Configurable credentials
- Network isolation recommended
- HTTPS for production (requires SSL)

---

## 11. Testing & Validation

### Q11.1: How did you test your system?

**Answer:**

- Unit testing for individual functions
- Integration testing for complete workflows
- Testing with real classroom images
- Validation with known students
- Performance testing with different image sizes

### Q11.2: How did you validate recognition accuracy?

**Answer:**

- Tested with controlled images (known students)
- Compared results with manual verification
- Tested under different lighting conditions
- Tested with various face poses
- Calculated accuracy metrics

### Q11.3: What test cases did you create?

**Answer:**

- Student registration with valid/invalid data
- Attendance marking with single/multiple faces
- Report generation with various filters
- Excel export functionality
- Error handling (missing images, database errors)
- Authentication and authorization

### Q11.4: How did you handle edge cases?

**Answer:**

- No faces detected in image
- Face not matching any student
- Multiple matches for one face
- Database connection failures
- Invalid image formats
- Missing student photos

### Q11.5: What validation did you perform on user inputs?

**Answer:**

- Roll number uniqueness
- Email format validation
- Image format validation
- Date range validation
- Required field checks

---

## 12. Future Enhancements

### Q12.1: What improvements would you make to the system?

**Answer:**

1. Real-time video processing
2. Liveness detection (prevent spoofing)
3. Vector database for scalability
4. Mobile application
5. Integration with existing SIS/LMS
6. Advanced analytics and predictive models
7. Multi-factor authentication
8. Cloud deployment
9. Batch processing for multiple classes
10. Automatic attendance reminders

### Q12.2: How would you implement real-time video processing?

**Answer:**

- Capture video stream from camera
- Process frames at intervals (e.g., every 5 seconds)
- Detect and recognize faces in each frame
- Track attendance over time
- Handle movement and pose changes

### Q12.3: What is liveness detection and why is it important?

**Answer:** Liveness detection distinguishes between a live person and a photo/video. It prevents spoofing attacks where someone shows a photo of a student. Can be implemented using:

- Eye blink detection
- Head movement tracking
- 3D face analysis
- Challenge-response methods

### Q12.4: How would you scale the system for a large university?

**Answer:**

- Use vector database (Faiss, Milvus) for fast similarity search
- Pre-compute all student embeddings
- Use distributed computing (GPU clusters)
- Implement caching mechanisms
- Use cloud infrastructure
- Database optimization and indexing

### Q12.5: How would you integrate with existing systems?

**Answer:**

- REST API for data exchange
- Database synchronization
- Import/export functionality
- Standard data formats (CSV, JSON)
- Webhook support for real-time updates

---

## 13. ESP32-CAM Integration

### Q13.1: What is ESP32-CAM and why did you integrate it?

**Answer:** ESP32-CAM is a low-cost camera module with WiFi. It allows remote image capture without needing to upload files manually, making the system more convenient for teachers.

### Q13.2: How does ESP32-CAM integration work?

**Answer:**

1. ESP32-CAM connects to WiFi
2. Creates HTTP server with authentication
3. Provides endpoints: `/stream` (video), `/capture` (image)
4. System connects to ESP32-CAM URL
5. Captures image on demand
6. Processes image for attendance

### Q13.3: What are the advantages of ESP32-CAM?

**Answer:**

- Wireless image capture
- No need to transfer files manually
- Can be mounted in classroom
- Low cost
- Easy setup

### Q13.4: What security measures are implemented for ESP32-CAM?

**Answer:**

- HTTP Basic Authentication
- Configurable username/password
- Network isolation recommended
- HTTPS for production (requires additional setup)

### Q13.5: What are the limitations of ESP32-CAM?

**Answer:**

- Lower image quality compared to DSLR
- Limited processing power
- WiFi dependency
- Range limitations
- HTTP only (not HTTPS by default)

---

## 14. Data Export & Reporting

### Q14.1: What export formats are supported?

**Answer:** Currently supports Excel (.xlsx) format. Can be extended to CSV, PDF, JSON.

### Q14.2: What information is included in exported reports?

**Answer:**

- Student details (name, roll number)
- Subject information
- Date and period
- Attendance status (Present/Absent)
- Attendance percentage
- Date range summary

### Q14.3: How does Google Sheets integration work?

**Answer:**

- Uses Google Sheets API
- Authenticates with service account
- Creates/updates spreadsheets automatically
- Shares sheets with specified email
- Syncs attendance data

### Q14.4: What reporting features are available?

**Answer:**

- Individual student reports
- Class-wise reports
- Subject-wise reports
- Date range reports
- Attendance percentage calculations
- Visual charts and graphs
- Export to Excel

### Q14.5: How are reports customized?

**Answer:**

- Filter by date range
- Filter by subject
- Filter by student
- Filter by class
- Filter by period
- Sort by various columns

---

## Additional Technical Questions

### Q15.1: What is the difference between face detection and face recognition?

**Answer:**

- **Face Detection:** Locating faces in an image (finding where faces are)
- **Face Recognition:** Identifying who the person is (matching to known individuals)

### Q15.2: What is cosine similarity and how is it used?

**Answer:** Cosine similarity measures the angle between two vectors. In facial recognition, it's used to compare embeddings. Values range from -1 to 1, where 1 means identical faces.

### Q15.3: What is the difference between supervised and unsupervised learning in your context?

**Answer:** Facial recognition uses supervised learning - the model is trained on labeled face datasets (faces with known identities) to learn discriminative features.

### Q15.4: How does transfer learning apply to your project?

**Answer:** We use pre-trained models (VGG-Face, FaceNet, ArcFace) that were trained on large face datasets. We don't retrain them; we use them for feature extraction (transfer learning).

### Q15.5: What is the role of neural networks in facial recognition?

**Answer:** Convolutional Neural Networks (CNNs) extract hierarchical features from face images:

- Early layers detect edges and textures
- Middle layers detect facial parts (eyes, nose)
- Deep layers capture high-level features for identity

### Q15.6: How do you handle image preprocessing?

**Answer:**

- Image loading and validation
- Face detection and cropping
- Face alignment (normalization)
- Resizing to model input size
- Normalization (pixel values to 0-1 range)

### Q15.7: What is the difference between batch processing and real-time processing?

**Answer:**

- **Batch Processing:** Process multiple images at once (current implementation)
- **Real-time Processing:** Process video stream frame-by-frame (future enhancement)

### Q15.8: How would you deploy this system in production?

**Answer:**

- Use cloud platform (AWS, Azure, GCP)
- Set up web server (Gunicorn, uWSGI)
- Use production database (PostgreSQL)
- Implement load balancing
- Set up monitoring and logging
- Use HTTPS/SSL
- Implement backup strategies

### Q15.9: What is the difference between accuracy and precision in your context?

**Answer:**

- **Accuracy:** Overall correctness (correct identifications / total)
- **Precision:** Correct positive identifications / total positive identifications
- **Recall:** Correct positive identifications / actual positives

### Q15.10: How do you handle model versioning and updates?

**Answer:**

- Configuration file allows model selection
- Users can switch models without code changes
- Model files are managed by DeepFace library
- Can update models by changing config

---

## Project-Specific Questions

### Q16.1: Why is this system specifically for ENTC B.Tech B division?

**Answer:** The system was designed for a specific department and class as a proof of concept. It can be easily extended to other departments/classes by modifying configuration.

### Q16.2: How many subjects does the system support?

**Answer:** The system supports 8 default subjects:

- Fiber Optic Communication (FOC)
- Microwave Engineering (ME)
- Mobile Computing (MC)
- E-Waste Management
- Data Structures and Algorithms in Java (DSAJ)
- Engineering Economics and Financial Management (EEFM)
- Microwave Engineering Lab
- Mini Project

### Q16.3: Can the system handle multiple classes?

**Answer:** Yes, the database schema supports multiple classes. The system can be extended to handle multiple classes by adding class filtering in the UI.

### Q16.4: What is the maximum number of students the system can handle?

**Answer:** Technically unlimited, but performance degrades with linear search. For optimal performance:

- < 100 students: Excellent
- 100-500 students: Good
- 500-1000 students: Acceptable
- > 1000 students: Needs optimization (vector database)

### Q16.5: How does the system handle attendance for the same student in multiple periods?

**Answer:** The attendance table includes a `period` field, allowing separate attendance records for the same student, subject, and date but different periods.

---

## Conclusion

These questions cover all aspects of the Automated Attendance System project. Prepare answers based on your actual implementation and be ready to demonstrate the system during the viva voce examination.

**Tips for Viva:**

1. Be confident and clear in your explanations
2. Demonstrate the system if possible
3. Be honest about limitations and challenges
4. Show understanding of the technology stack
5. Discuss future improvements
6. Be prepared to explain any code you've written
7. Understand the theoretical concepts behind facial recognition

Good luck with your viva!
