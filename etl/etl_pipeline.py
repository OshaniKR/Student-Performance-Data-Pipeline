"""
Student Performance Data Pipeline - ETL Script
================================================
This script handles:
  1. Extracting data from CSV files
  2. Cleaning and transforming the data
  3. Calculating GPA
  4. Loading into PostgreSQL

How to run:
  python etl_pipeline.py

Requirements:
  pip install pandas psycopg2-binary sqlalchemy python-dotenv
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env file BEFORE os.getenv() calls
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("etl_pipeline.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
# Update these with your own PostgreSQL credentials
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "student_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
}

RAW_DATA_DIR      = "../data/raw"
PROCESSED_DATA_DIR = "../data/processed"


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — EXTRACT
# ══════════════════════════════════════════════════════════════════════════════

def extract(students_path: str, grades_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the two raw CSV files."""
    log.info("📂 Extracting data from CSV files...")

    students = pd.read_csv(students_path)
    grades   = pd.read_csv(grades_path)

    log.info(f"   Students loaded : {len(students):,} rows")
    log.info(f"   Grades loaded   : {len(grades):,} rows")

    return students, grades


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — TRANSFORM
# ══════════════════════════════════════════════════════════════════════════════

def clean_students(df: pd.DataFrame) -> pd.DataFrame:
    """Clean student records."""
    log.info("🧹 Cleaning students table...")

    before = len(df)

    # Remove exact duplicate rows
    df = df.drop_duplicates()
    log.info(f"   Duplicates removed : {before - len(df)}")

    # Fill missing emails with a generated placeholder
    mask = df["email"].isna()
    df.loc[mask, "email"] = (
        df.loc[mask, "first_name"].str.lower() + "." +
        df.loc[mask, "last_name"].str.lower()  + "@unknown.lk"
    )
    log.info(f"   Missing emails filled : {mask.sum()}")

    # Standardise text columns
    df["first_name"]  = df["first_name"].str.strip().str.title()
    df["last_name"]   = df["last_name"].str.strip().str.title()
    df["department"]  = df["department"].str.strip()
    df["gender"]      = df["gender"].str.strip().str.capitalize()

    # Add metadata
    df["created_at"] = datetime.now()

    log.info(f"   Final student rows : {len(df):,}")
    return df


def clean_grades(df: pd.DataFrame) -> pd.DataFrame:
    """Clean grade records."""
    log.info("🧹 Cleaning grades table...")

    before = len(df)

    # Remove exact duplicates
    df = df.drop_duplicates()
    log.info(f"   Duplicates removed : {before - len(df)}")

    # Drop rows where marks are missing (we can't impute exam scores)
    missing_marks = df["marks"].isna().sum()
    df = df.dropna(subset=["marks"])
    log.info(f"   Rows with missing marks dropped : {missing_marks}")

    # Sanity check — marks must be between 0 and max_marks
    invalid = df[df["marks"] > df["max_marks"]]
    if not invalid.empty:
        log.warning(f"   ⚠️  {len(invalid)} rows have marks > max_marks — dropping")
        df = df[df["marks"] <= df["max_marks"]]

    df["marks"]     = df["marks"].astype(float)
    df["max_marks"] = df["max_marks"].astype(float)
    df["created_at"] = datetime.now()

    log.info(f"   Final grade rows : {len(df):,}")
    return df


def calculate_gpa(grades: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate GPA per student using percentage bands:
      90-100 → 4.0 (A+)
      80-89  → 3.7 (A)
      70-79  → 3.3 (B+)
      60-69  → 3.0 (B)
      50-59  → 2.0 (C)
      <50    → 0.0 (F)
    """
    log.info("🎓 Calculating GPA...")

    def marks_to_grade_point(marks, max_marks):
        pct = (marks / max_marks) * 100
        if   pct >= 90: return 4.0, "A+"
        elif pct >= 80: return 3.7, "A"
        elif pct >= 70: return 3.3, "B+"
        elif pct >= 60: return 3.0, "B"
        elif pct >= 50: return 2.0, "C"
        else:           return 0.0, "F"

    grades[["grade_point", "letter_grade"]] = grades.apply(
        lambda r: marks_to_grade_point(r["marks"], r["max_marks"]),
        axis=1, result_type="expand"
    )
    grades["percentage"] = (grades["marks"] / grades["max_marks"] * 100).round(2)
    grades["pass_fail"]  = grades["percentage"].apply(lambda p: "Pass" if p >= 50 else "Fail")

    # Aggregate GPA per student
    gpa_df = (
        grades
        .groupby("student_id")
        .agg(
            gpa          = ("grade_point", "mean"),
            total_subjects = ("subject_code", "count"),
            avg_percentage = ("percentage", "mean"),
        )
        .reset_index()
    )
    gpa_df["gpa"]            = gpa_df["gpa"].round(2)
    gpa_df["avg_percentage"] = gpa_df["avg_percentage"].round(2)

    log.info(f"   GPA calculated for {len(gpa_df)} students")
    return grades, gpa_df


def build_summary(students: pd.DataFrame, gpa_df: pd.DataFrame) -> pd.DataFrame:
    """Merge students with their GPA to create a summary table."""
    summary = students.merge(gpa_df, on="student_id", how="left")
    summary["gpa"]            = summary["gpa"].fillna(0.0)
    summary["total_subjects"] = summary["total_subjects"].fillna(0).astype(int)
    summary["avg_percentage"] = summary["avg_percentage"].fillna(0.0)
    return summary


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — LOAD
# ══════════════════════════════════════════════════════════════════════════════

def get_engine():
    """Create SQLAlchemy engine from DB_CONFIG."""
    from urllib.parse import quote_plus
    password = quote_plus(DB_CONFIG['password'])  # safely encodes @ and special chars
    url = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{password}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)


def create_schema(engine):
    """Create tables if they don't already exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS students (
        student_id      VARCHAR(10) PRIMARY KEY,
        first_name      VARCHAR(50),
        last_name       VARCHAR(50),
        email           VARCHAR(100),
        department      VARCHAR(100),
        enrollment_year INT,
        gender          VARCHAR(20),
        gpa             NUMERIC(3,2),
        total_subjects  INT,
        avg_percentage  NUMERIC(5,2),
        created_at      TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS grades (
        grade_id      VARCHAR(10) PRIMARY KEY,
        student_id    VARCHAR(10) REFERENCES students(student_id),
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
        created_at    TIMESTAMP
    );
    """
    with engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()
    log.info("✅ Database schema ready")


def load_to_postgres(summary: pd.DataFrame, grades: pd.DataFrame, engine):
    """Load cleaned DataFrames into PostgreSQL."""
    log.info("Loading data into PostgreSQL...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS grades CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS students CASCADE"))
        conn.commit()

    summary.to_sql("students", engine, if_exists="append", index=False, method="multi")
    log.info(f"   students  -> {len(summary)} rows inserted")

    grades.to_sql("grades", engine, if_exists="append", index=False, method="multi")
    log.info(f"   grades    -> {len(grades)} rows inserted")


def save_processed_csv(summary: pd.DataFrame, grades: pd.DataFrame, out_dir: str):
    """Also save processed data locally as CSV for inspection / Power BI."""
    os.makedirs(out_dir, exist_ok=True)
    summary.to_csv(f"{out_dir}/students_clean.csv", index=False)
    grades.to_csv(f"{out_dir}/grades_clean.csv",   index=False)
    log.info(f"💾 Processed CSVs saved to {out_dir}/")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline():
    log.info("=" * 60)
    log.info("  Student Performance ETL Pipeline — starting")
    log.info("=" * 60)

    # 1. Extract
    students_raw, grades_raw = extract(
        students_path=f"{RAW_DATA_DIR}/students.csv",
        grades_path=f"{RAW_DATA_DIR}/grades.csv",
    )

    # 2. Transform
    students_clean = clean_students(students_raw)
    grades_clean   = clean_grades(grades_raw)
    grades_clean, gpa_df = calculate_gpa(grades_clean)
    summary        = build_summary(students_clean, gpa_df)

    # Save processed CSVs (always, even without DB)
    save_processed_csv(summary, grades_clean, PROCESSED_DATA_DIR)

    # 3. Load into PostgreSQL (comment out if you haven't set up Postgres yet)
    try:
        engine = get_engine()
        create_schema(engine)
        load_to_postgres(summary, grades_clean, engine)
        log.info("✅ Pipeline completed successfully!")
    except Exception as e:
        log.warning(f"⚠️  PostgreSQL load skipped: {e}")
        log.info("   (Processed CSVs are still saved locally)")

    log.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
