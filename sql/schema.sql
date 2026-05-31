-- ============================================================
-- Student Performance DB — Schema Setup
-- Run this ONCE before the first ETL run.
-- ============================================================

-- Create the database (run as superuser if needed):
-- CREATE DATABASE student_db;
-- \c student_db

CREATE TABLE IF NOT EXISTS students (
    student_id      VARCHAR(10)  PRIMARY KEY,
    first_name      VARCHAR(50),
    last_name       VARCHAR(50),
    email           VARCHAR(100),
    department      VARCHAR(100),
    enrollment_year INT,
    gender          VARCHAR(20),
    gpa             NUMERIC(3,2),
    total_subjects  INT,
    avg_percentage  NUMERIC(5,2),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS grades (
    grade_id      VARCHAR(10)  PRIMARY KEY,
    student_id    VARCHAR(10)  REFERENCES students(student_id) ON DELETE CASCADE,
    semester      INT,
    subject_code  VARCHAR(20),
    subject_name  VARCHAR(100),
    marks         NUMERIC(5,2),
    max_marks     NUMERIC(5,2),
    year          INT,
    grade_point   NUMERIC(3,1),
    letter_grade  VARCHAR(5),
    percentage    NUMERIC(5,2),
    pass_fail     VARCHAR(10),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Helpful indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_grades_student_id  ON grades(student_id);
CREATE INDEX IF NOT EXISTS idx_grades_subject_code ON grades(subject_code);
CREATE INDEX IF NOT EXISTS idx_students_department ON students(department);

-- Quick verification
SELECT 'Schema created successfully ✅' AS status;
