PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'ENTC',
        year TEXT DEFAULT 'TY',
        division TEXT DEFAULT 'B',
        image_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
INSERT INTO students VALUES(1,'EC4237','Shubham Pitekar','shubhampitekar2323@gmail.com','ENTC','B.Tech','B','faces/EC4237.jpg','2025-10-11 09:34:34');
INSERT INTO students VALUES(2,'EC4220','Anushka Mote','anushska484m@gmail.com','ENTC','B.Tech','B','faces/EC4220.jpg','2025-11-19 11:08:36');
INSERT INTO students VALUES(3,'EC4255','Damini Solunke','daminisolunke@gmail.com','ENTC','B.Tech','B','faces/EC4255.jpg','2025-11-21 07:31:38');
INSERT INTO students VALUES(4,'EC4233','Sagar Pawar','sagarpawar@gmail.com','ENTC','B.Tech','B','faces/EC4233.jpg','2025-11-21 08:17:49');
INSERT INTO students VALUES(5,'EC4231','Vaishnavi Pawar','vaishnavipawar@gmail.com','ENTC','B.Tech','B','faces/EC4231.jpg','2025-11-21 08:19:51');
INSERT INTO students VALUES(6,'EC4206','Sai Kenekar','saikanekar@gmail.com','ENTC','B.Tech','B','faces/EC4206.jpg','2025-11-21 08:26:16');
INSERT INTO students VALUES(7,'EC4202','Divya Bhagas','divyabhagas@gmail.com','ENTC','B.Tech','B','faces/EC4202.jpg','2025-11-21 08:27:33');
INSERT INTO students VALUES(8,'EC4236','Shubham Phad','shubhamphad03@gmail.com','ENTC','B.Tech','B','faces/EC4236.jpg','2025-11-21 09:33:27');
INSERT INTO students VALUES(9,'EC4226','Abhishek Pathak','abhipathak2513@gmail.com','ENTC','B.Tech','B','faces/EC4226.jpg','2025-11-21 09:58:51');
CREATE TABLE subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL
    );
INSERT INTO subjects VALUES(496,'FOC','Fiber Optic Communication');
INSERT INTO subjects VALUES(497,'ME','Microwave Engineering');
INSERT INTO subjects VALUES(498,'MC','Mobile Computing');
INSERT INTO subjects VALUES(499,'Ewaste','E-Waste Management');
INSERT INTO subjects VALUES(500,'DSAJ','Data Structures and Algorithms in Java');
INSERT INTO subjects VALUES(501,'EEFM','Engineering Economics and Financial Management');
INSERT INTO subjects VALUES(502,'ME Lab','Microwave Engineering Lab');
INSERT INTO subjects VALUES(503,'Mini project','Mini Project');
CREATE TABLE student_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id)
    );
INSERT INTO student_subjects VALUES(1,1,1);
INSERT INTO student_subjects VALUES(2,1,3);
INSERT INTO student_subjects VALUES(3,1,2);
INSERT INTO student_subjects VALUES(4,1,7);
INSERT INTO student_subjects VALUES(5,1,5);
INSERT INTO student_subjects VALUES(6,1,4);
INSERT INTO student_subjects VALUES(7,1,6);
INSERT INTO student_subjects VALUES(8,1,8);
INSERT INTO student_subjects VALUES(9,1,9);
INSERT INTO student_subjects VALUES(10,2,500);
INSERT INTO student_subjects VALUES(11,2,499);
INSERT INTO student_subjects VALUES(12,2,501);
INSERT INTO student_subjects VALUES(13,2,496);
INSERT INTO student_subjects VALUES(14,2,497);
INSERT INTO student_subjects VALUES(15,2,502);
INSERT INTO student_subjects VALUES(16,2,503);
INSERT INTO student_subjects VALUES(17,2,498);
INSERT INTO student_subjects VALUES(18,3,500);
INSERT INTO student_subjects VALUES(19,3,499);
INSERT INTO student_subjects VALUES(20,3,501);
INSERT INTO student_subjects VALUES(21,3,496);
INSERT INTO student_subjects VALUES(22,3,497);
INSERT INTO student_subjects VALUES(23,3,502);
INSERT INTO student_subjects VALUES(24,3,503);
INSERT INTO student_subjects VALUES(25,3,498);
INSERT INTO student_subjects VALUES(26,4,500);
INSERT INTO student_subjects VALUES(27,4,499);
INSERT INTO student_subjects VALUES(28,4,501);
INSERT INTO student_subjects VALUES(29,4,496);
INSERT INTO student_subjects VALUES(30,4,497);
INSERT INTO student_subjects VALUES(31,4,502);
INSERT INTO student_subjects VALUES(32,4,503);
INSERT INTO student_subjects VALUES(33,4,498);
INSERT INTO student_subjects VALUES(34,5,500);
INSERT INTO student_subjects VALUES(35,5,499);
INSERT INTO student_subjects VALUES(36,5,501);
INSERT INTO student_subjects VALUES(37,5,496);
INSERT INTO student_subjects VALUES(38,5,497);
INSERT INTO student_subjects VALUES(39,5,502);
INSERT INTO student_subjects VALUES(40,5,503);
INSERT INTO student_subjects VALUES(41,5,498);
INSERT INTO student_subjects VALUES(42,6,500);
INSERT INTO student_subjects VALUES(43,6,499);
INSERT INTO student_subjects VALUES(44,6,501);
INSERT INTO student_subjects VALUES(45,6,496);
INSERT INTO student_subjects VALUES(46,6,497);
INSERT INTO student_subjects VALUES(47,6,502);
INSERT INTO student_subjects VALUES(48,6,503);
INSERT INTO student_subjects VALUES(49,6,498);
INSERT INTO student_subjects VALUES(58,8,500);
INSERT INTO student_subjects VALUES(59,8,499);
INSERT INTO student_subjects VALUES(60,8,501);
INSERT INTO student_subjects VALUES(61,8,496);
INSERT INTO student_subjects VALUES(62,8,497);
INSERT INTO student_subjects VALUES(63,8,502);
INSERT INTO student_subjects VALUES(64,8,503);
INSERT INTO student_subjects VALUES(65,8,498);
INSERT INTO student_subjects VALUES(66,9,500);
INSERT INTO student_subjects VALUES(67,9,499);
INSERT INTO student_subjects VALUES(68,9,501);
INSERT INTO student_subjects VALUES(69,9,496);
INSERT INTO student_subjects VALUES(70,9,497);
INSERT INTO student_subjects VALUES(71,9,502);
INSERT INTO student_subjects VALUES(72,9,503);
INSERT INTO student_subjects VALUES(73,9,498);
INSERT INTO student_subjects VALUES(74,7,500);
INSERT INTO student_subjects VALUES(75,7,499);
INSERT INTO student_subjects VALUES(76,7,501);
INSERT INTO student_subjects VALUES(77,7,496);
INSERT INTO student_subjects VALUES(78,7,497);
INSERT INTO student_subjects VALUES(79,7,502);
INSERT INTO student_subjects VALUES(80,7,503);
INSERT INTO student_subjects VALUES(81,7,498);
INSERT INTO student_subjects VALUES(138,1,500);
INSERT INTO student_subjects VALUES(139,1,501);
INSERT INTO student_subjects VALUES(140,1,499);
INSERT INTO student_subjects VALUES(141,1,496);
INSERT INTO student_subjects VALUES(142,1,498);
INSERT INTO student_subjects VALUES(143,1,497);
INSERT INTO student_subjects VALUES(144,1,502);
INSERT INTO student_subjects VALUES(145,1,503);
CREATE TABLE attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        period TEXT NOT NULL,
        status TEXT DEFAULT 'present',
        FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id, date, period)
    );
INSERT INTO attendance VALUES(1,1,501,'2025-11-15','10:15 - 11:15','present');
INSERT INTO attendance VALUES(2,1,500,'2025-11-15','10:15 - 11:15','present');
INSERT INTO attendance VALUES(3,2,501,'2025-11-19','10:15 - 11:15','present');
INSERT INTO attendance VALUES(4,1,501,'2025-11-19','10:15 - 11:15','present');
INSERT INTO attendance VALUES(5,3,499,'2025-11-20','10:15 - 11:15','present');
INSERT INTO attendance VALUES(6,4,499,'2025-11-19','10:15 - 11:15','present');
INSERT INTO attendance VALUES(7,8,500,'2025-11-21','10:15 - 11:15','present');
INSERT INTO attendance VALUES(8,1,500,'2025-11-21','10:15 - 11:15','present');
INSERT INTO attendance VALUES(9,7,500,'2025-11-21','10:15 - 11:15','present');
INSERT INTO attendance VALUES(10,4,500,'2025-11-21','10:15 - 11:15','present');
CREATE TABLE users (
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
    );
INSERT INTO users VALUES(1,'admin','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','HOD','Administrator','admin@example.com','ENTC',1,'2025-11-21 18:52:29','2025-11-22T01:14:37.390814');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('subjects',3343);
INSERT INTO sqlite_sequence VALUES('students',9);
INSERT INTO sqlite_sequence VALUES('student_subjects',6849);
INSERT INTO sqlite_sequence VALUES('attendance',10);
INSERT INTO sqlite_sequence VALUES('users',1);
COMMIT;
