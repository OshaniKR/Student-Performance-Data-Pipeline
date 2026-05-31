# 🎓 Student Performance Data Pipeline

A beginner-friendly **Data Engineering** project covering the full ETL workflow:
CSV → Python → PostgreSQL → SQL Analysis → Dashboard

---

## 📁 Project Structure

```
student_pipeline/
├── data/
│   ├── raw/                  # Original CSV files (never edit these)
│   │   ├── students.csv
│   │   └── grades.csv
│   └── processed/            # Output of ETL (auto-generated)
│       ├── students_clean.csv
│       └── grades_clean.csv
├── etl/
│   └── etl_pipeline.py       # Main ETL script
├── sql/
│   ├── schema.sql            # Create tables in PostgreSQL
│   └── analysis_queries.sql  # All analysis queries
├── dashboard/                # Power BI (.pbix) or HTML dashboard goes here
├── docs/                     # Notes and diagrams
├── .env.example              # DB credentials template
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL
- Install PostgreSQL if you haven't: https://www.postgresql.org/download/
- Create the database:
```sql
CREATE DATABASE student_db;
```
- Run the schema script:
```bash
psql -U postgres -d student_db -f sql/schema.sql
```

### 3. Configure your credentials
```bash
cp .env.example .env
# Edit .env with your real PostgreSQL password
```

### 4. Run the ETL pipeline
```bash
cd etl
python etl_pipeline.py
```

### 5. Run SQL analysis
```bash
psql -U postgres -d student_db -f ../sql/analysis_queries.sql
```

---

## 🧪 What the ETL Does

| Step | Action |
|------|--------|
| **Extract** | Reads `students.csv` and `grades.csv` |
| **Clean** | Removes duplicates, fills missing emails, drops null marks |
| **Transform** | Calculates percentage, letter grade, grade point, pass/fail |
| **GPA** | Aggregates per-student GPA (4.0 scale) |
| **Load** | Inserts into PostgreSQL `students` and `grades` tables |
| **Export** | Also saves cleaned CSVs to `data/processed/` |

### GPA Scale Used
| Percentage | Grade Point | Letter |
|-----------|-------------|--------|
| 90 – 100  | 4.0 | A+ |
| 80 – 89   | 3.7 | A  |
| 70 – 79   | 3.3 | B+ |
| 60 – 69   | 3.0 | B  |
| 50 – 59   | 2.0 | C  |
| < 50      | 0.0 | F  |

---

## 📊 SQL Queries Included

1. **Top 5 students** by GPA
2. **Department averages** — GPA and percentage per department
3. **Pass/fail rates** — by department
4. **Subject difficulty** — hardest subjects by avg marks
5. **Full report card** — all student grade details
6. **Grade distribution** — A+, A, B+, B, C, F counts
7. **Semester trend** — performance over time
8. **At-risk students** — GPA below 2.0

---

## 📈 Dashboard (Power BI)

Import `data/processed/students_clean.csv` and `grades_clean.csv` into Power BI.

Suggested visuals:
- Bar chart: Department avg GPA
- Donut chart: Pass/Fail rate
- Table: Top students leaderboard
- Line chart: Semester trend
- Card: Total students, avg GPA, pass rate

---

## 🗂️ Skills Practised

- ✅ ETL (Extract, Transform, Load)
- ✅ Data cleaning with Pandas
- ✅ GPA calculation logic
- ✅ PostgreSQL database design
- ✅ SQL analysis queries
- ✅ Data pipeline logging
- ✅ Project structure & documentation

---

## 🐛 Troubleshooting

**`psycopg2` install error on Windows?**
Use `pip install psycopg2-binary` instead.

**PostgreSQL connection refused?**
Make sure the PostgreSQL service is running:
- Windows: Services → PostgreSQL → Start
- Mac: `brew services start postgresql`
- Linux: `sudo service postgresql start`

**ETL runs but no DB?**
That's fine! The processed CSVs in `data/processed/` are still saved and can be used directly in Power BI.
