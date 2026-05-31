-- ============================================================
-- Student Performance Data Pipeline — Analysis Queries
-- ============================================================
-- Run these in PostgreSQL after the ETL pipeline has loaded
-- data into the students and grades tables.
-- ============================================================


-- ────────────────────────────────────────────────────────────
-- 1. TOP 5 STUDENTS BY GPA
-- ────────────────────────────────────────────────────────────
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name AS full_name,
    s.department,
    s.gpa,
    s.avg_percentage,
    s.total_subjects
FROM students s
ORDER BY s.gpa DESC, s.avg_percentage DESC
LIMIT 5;


-- ────────────────────────────────────────────────────────────
-- 2. DEPARTMENT AVERAGES
-- ────────────────────────────────────────────────────────────
SELECT
    s.department,
    COUNT(DISTINCT s.student_id)          AS total_students,
    ROUND(AVG(s.gpa)::numeric, 2)         AS avg_gpa,
    ROUND(AVG(s.avg_percentage)::numeric, 2) AS avg_percentage,
    MAX(s.gpa)                            AS highest_gpa,
    MIN(s.gpa)                            AS lowest_gpa
FROM students s
WHERE s.gpa > 0
GROUP BY s.department
ORDER BY avg_gpa DESC;


-- ────────────────────────────────────────────────────────────
-- 3. PASS / FAIL RATES BY DEPARTMENT
-- ────────────────────────────────────────────────────────────
SELECT
    s.department,
    COUNT(g.grade_id)                        AS total_attempts,
    SUM(CASE WHEN g.pass_fail = 'Pass' THEN 1 ELSE 0 END) AS passed,
    SUM(CASE WHEN g.pass_fail = 'Fail' THEN 1 ELSE 0 END) AS failed,
    ROUND(
        100.0 * SUM(CASE WHEN g.pass_fail = 'Pass' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(g.grade_id), 0), 1
    ) AS pass_rate_pct
FROM grades g
JOIN students s ON g.student_id = s.student_id
GROUP BY s.department
ORDER BY pass_rate_pct DESC;


-- ────────────────────────────────────────────────────────────
-- 4. SUBJECT DIFFICULTY — HARDEST SUBJECTS (LOWEST AVG MARKS)
-- ────────────────────────────────────────────────────────────
SELECT
    subject_code,
    subject_name,
    COUNT(*)                              AS times_taken,
    ROUND(AVG(percentage)::numeric, 1)    AS avg_percentage,
    MIN(percentage)                       AS min_percentage,
    MAX(percentage)                       AS max_percentage,
    SUM(CASE WHEN pass_fail='Fail' THEN 1 ELSE 0 END) AS fail_count
FROM grades
GROUP BY subject_code, subject_name
ORDER BY avg_percentage ASC;


-- ────────────────────────────────────────────────────────────
-- 5. FULL STUDENT REPORT CARD (all students with grade details)
-- ────────────────────────────────────────────────────────────
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name  AS full_name,
    s.department,
    g.subject_code,
    g.subject_name,
    g.marks,
    g.percentage,
    g.letter_grade,
    g.pass_fail,
    g.semester,
    g.year
FROM students s
JOIN grades g ON s.student_id = g.student_id
ORDER BY s.student_id, g.year, g.semester;


-- ────────────────────────────────────────────────────────────
-- 6. GRADE DISTRIBUTION (A+, A, B+, B, C, F)
-- ────────────────────────────────────────────────────────────
SELECT
    letter_grade,
    COUNT(*)                               AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM grades
GROUP BY letter_grade
ORDER BY
    CASE letter_grade
        WHEN 'A+' THEN 1 WHEN 'A'  THEN 2 WHEN 'B+' THEN 3
        WHEN 'B'  THEN 4 WHEN 'C'  THEN 5 WHEN 'F'  THEN 6
    END;


-- ────────────────────────────────────────────────────────────
-- 7. SEMESTER-OVER-SEMESTER PERFORMANCE TREND
-- ────────────────────────────────────────────────────────────
SELECT
    year,
    semester,
    COUNT(DISTINCT student_id)            AS active_students,
    ROUND(AVG(percentage)::numeric, 1)    AS avg_percentage,
    ROUND(AVG(grade_point)::numeric, 2)   AS avg_gpa
FROM grades
GROUP BY year, semester
ORDER BY year, semester;


-- ────────────────────────────────────────────────────────────
-- 8. AT-RISK STUDENTS (GPA < 2.0)
-- ────────────────────────────────────────────────────────────
SELECT
    student_id,
    first_name || ' ' || last_name AS full_name,
    department,
    gpa,
    avg_percentage,
    total_subjects
FROM students
WHERE gpa < 2.0 AND gpa > 0
ORDER BY gpa ASC;
