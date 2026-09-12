import os
import sys
import asyncio
from datetime import datetime, timezone

# Ensure project root is in sys.path and UTF-8 stdout
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import select
from backend.app.core.database import AsyncSessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User, UserRole
from backend.app.models.department import Department
from backend.app.models.student import StudentProfile, GenderEnum
from backend.app.models.faculty import FacultyProfile
from backend.app.models.academic_record import SemesterAcademicRecord


async def seed():
    print("[SEED] Starting database seeding...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        res = await db.execute(select(Department))
        if res.scalars().first():
            print("[INFO] Database already contains data. Skipping seeding.")
            return

        # 1. Seed Departments
        dept_cs = Department(code="CS", name="Computer Science & Engineering")
        dept_it = Department(code="IT", name="Information Technology")
        dept_ece = Department(code="ECE", name="Electronics & Communication Engineering")
        dept_mech = Department(code="MECH", name="Mechanical Engineering")

        db.add_all([dept_cs, dept_it, dept_ece, dept_mech])
        await db.flush()
        print("[SUCCESS] Seeded Departments (CS, IT, ECE, MECH)")

        # 2. Seed Admin User
        admin_user = User(
            email="admin@university.edu",
            hashed_password=get_password_hash("Password@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)

        # 3. Seed Faculty Users
        faculty1_user = User(
            email="faculty.cs@university.edu",
            hashed_password=get_password_hash("Password@123"),
            full_name="Dr. Robert Vance",
            role=UserRole.FACULTY,
            is_active=True,
            is_verified=True
        )
        faculty2_user = User(
            email="faculty.it@university.edu",
            hashed_password=get_password_hash("Password@123"),
            full_name="Dr. Sarah Connor",
            role=UserRole.FACULTY,
            is_active=True,
            is_verified=True
        )
        db.add_all([faculty1_user, faculty2_user])
        await db.flush()

        faculty1_prof = FacultyProfile(
            user_id=faculty1_user.id,
            employee_number="EMP-CS-001",
            department_id=dept_cs.id,
            designation="Professor & HOD"
        )
        faculty2_prof = FacultyProfile(
            user_id=faculty2_user.id,
            employee_number="EMP-IT-002",
            department_id=dept_it.id,
            designation="Associate Professor"
        )
        db.add_all([faculty1_prof, faculty2_prof])
        print("[SUCCESS] Seeded Admin and Faculty accounts")

        # 4. Seed Primary Student User (Alice Johnson)
        student_user = User(
            email="student.alice@university.edu",
            hashed_password=get_password_hash("Password@123"),
            full_name="Alice Johnson",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True
        )
        db.add(student_user)
        await db.flush()

        student_alice = StudentProfile(
            user_id=student_user.id,
            student_number="STU-2023-001",
            name="Alice Johnson",
            gender=GenderEnum.FEMALE,
            age=21,
            department_id=dept_cs.id,
            enrollment_year=2023,
            current_semester=4,
            cumulative_gpa=8.65,
            total_credits_earned=84,
            is_archived=False
        )
        db.add(student_alice)
        await db.flush()

        # Alice's 4 semesters of records
        records_alice = [
            SemesterAcademicRecord(
                student_id=student_alice.id,
                academic_year="2023-2024",
                semester=1,
                attendance_percentage=92.5,
                previous_cgpa=None,
                mid_1=85.0,
                mid_2=88.0,
                internal_marks=86.5,
                backlogs=0,
                semester_cgpa=8.50,
                grade="A+",
                historical_risk_level="LOW",
                notes="Excellent start in programming fundamentals."
            ),
            SemesterAcademicRecord(
                student_id=student_alice.id,
                academic_year="2023-2024",
                semester=2,
                attendance_percentage=90.0,
                previous_cgpa=8.50,
                mid_1=82.0,
                mid_2=86.0,
                internal_marks=84.0,
                backlogs=0,
                semester_cgpa=8.60,
                grade="A+",
                historical_risk_level="LOW"
            ),
            SemesterAcademicRecord(
                student_id=student_alice.id,
                academic_year="2024-2025",
                semester=3,
                attendance_percentage=94.0,
                previous_cgpa=8.55,
                mid_1=90.0,
                mid_2=91.0,
                internal_marks=90.5,
                backlogs=0,
                semester_cgpa=8.80,
                grade="O",
                historical_risk_level="LOW"
            ),
            SemesterAcademicRecord(
                student_id=student_alice.id,
                academic_year="2024-2025",
                semester=4,
                attendance_percentage=88.5,
                previous_cgpa=8.63,
                mid_1=84.0,
                mid_2=87.0,
                internal_marks=85.5,
                backlogs=0,
                semester_cgpa=8.70,
                grade="A+",
                historical_risk_level="LOW"
            )
        ]
        db.add_all(records_alice)

        # 5. Seed Additional Student Cohorts
        sample_students_data = [
            # High Performer
            ("STU-2023-002", "David Miller", GenderEnum.MALE, 21, dept_cs, 2023, 4, 9.15, 84, [
                ("2023-2024", 1, 96.0, None, 92.0, 95.0, 93.5, 0, 9.10, "O", "LOW"),
                ("2023-2024", 2, 95.0, 9.10, 90.0, 94.0, 92.0, 0, 9.05, "O", "LOW"),
                ("2024-2025", 3, 98.0, 9.08, 95.0, 96.0, 95.5, 0, 9.30, "O", "LOW"),
                ("2024-2025", 4, 94.5, 9.15, 88.0, 92.0, 90.0, 0, 9.15, "O", "LOW"),
            ]),
            # Moderate Performer
            ("STU-2023-003", "Elena Rostova", GenderEnum.FEMALE, 20, dept_it, 2023, 4, 7.40, 80, [
                ("2023-2024", 1, 82.0, None, 74.0, 78.0, 76.0, 0, 7.50, "A", "LOW"),
                ("2023-2024", 2, 78.5, 7.50, 70.0, 72.0, 71.0, 0, 7.20, "B+", "MODERATE"),
                ("2024-2025", 3, 80.0, 7.35, 75.0, 77.0, 76.0, 0, 7.50, "A", "LOW"),
                ("2024-2025", 4, 76.0, 7.40, 68.0, 74.0, 71.0, 0, 7.40, "B+", "MODERATE"),
            ]),
            # At-Risk Student (Low Attendance & Backlogs)
            ("STU-2023-004", "Marcus Brody", GenderEnum.MALE, 22, dept_cs, 2023, 4, 5.25, 68, [
                ("2023-2024", 1, 72.0, None, 60.0, 62.0, 61.0, 0, 6.20, "B", "MODERATE"),
                ("2023-2024", 2, 64.0, 6.20, 52.0, 50.0, 51.0, 1, 5.40, "C", "HIGH"),
                ("2024-2025", 3, 58.0, 5.80, 45.0, 48.0, 46.5, 2, 4.80, "F", "CRITICAL"),
                ("2024-2025", 4, 62.5, 5.47, 50.0, 55.0, 52.5, 1, 5.25, "C", "HIGH"),
            ]),
            # IT Student
            ("STU-2023-005", "Priya Sharma", GenderEnum.FEMALE, 20, dept_it, 2023, 4, 8.20, 84, [
                ("2023-2024", 1, 88.0, None, 80.0, 82.0, 81.0, 0, 8.10, "A", "LOW"),
                ("2023-2024", 2, 85.0, 8.10, 78.0, 84.0, 81.0, 0, 8.20, "A", "LOW"),
                ("2024-2025", 3, 90.0, 8.15, 85.0, 86.0, 85.5, 0, 8.40, "A+", "LOW"),
                ("2024-2025", 4, 86.0, 8.23, 79.0, 82.0, 80.5, 0, 8.10, "A", "LOW"),
            ]),
            # ECE Student
            ("STU-2023-006", "Brian O'Connor", GenderEnum.MALE, 21, dept_ece, 2023, 4, 6.80, 76, [
                ("2023-2024", 1, 78.0, None, 68.0, 70.0, 69.0, 0, 7.00, "B+", "MODERATE"),
                ("2023-2024", 2, 72.0, 7.00, 62.0, 65.0, 63.5, 1, 6.40, "B", "MODERATE"),
                ("2024-2025", 3, 75.0, 6.70, 70.0, 68.0, 69.0, 0, 6.90, "B+", "MODERATE"),
                ("2024-2025", 4, 74.0, 6.77, 66.0, 71.0, 68.5, 0, 6.90, "B+", "MODERATE"),
            ]),
            # MECH Student
            ("STU-2023-007", "Carlos Santana", GenderEnum.MALE, 21, dept_mech, 2023, 4, 7.10, 80, [
                ("2023-2024", 1, 85.0, None, 72.0, 75.0, 73.5, 0, 7.30, "B+", "LOW"),
                ("2023-2024", 2, 80.0, 7.30, 68.0, 70.0, 69.0, 0, 7.00, "B+", "MODERATE"),
                ("2024-2025", 3, 82.0, 7.15, 71.0, 73.0, 72.0, 0, 7.10, "B+", "LOW"),
                ("2024-2025", 4, 79.0, 7.13, 67.0, 72.0, 69.5, 0, 7.00, "B+", "MODERATE"),
            ]),
            # Critical Risk CS Student
            ("STU-2023-008", "Zack Snyder", GenderEnum.MALE, 22, dept_cs, 2023, 4, 4.30, 56, [
                ("2023-2024", 1, 55.0, None, 45.0, 48.0, 46.5, 1, 5.00, "C", "HIGH"),
                ("2023-2024", 2, 48.0, 5.00, 40.0, 42.0, 41.0, 3, 4.20, "F", "CRITICAL"),
                ("2024-2025", 3, 50.0, 4.60, 38.0, 40.0, 39.0, 2, 4.00, "F", "CRITICAL"),
                ("2024-2025", 4, 52.0, 4.40, 41.0, 44.0, 42.5, 2, 4.10, "F", "CRITICAL"),
            ]),
        ]

        for stu_num, name, gender, age, dept, year, sem, cgpa, credits_earned, terms in sample_students_data:
            stu = StudentProfile(
                student_number=stu_num,
                name=name,
                gender=gender,
                age=age,
                department_id=dept.id,
                enrollment_year=year,
                current_semester=sem,
                cumulative_gpa=cgpa,
                total_credits_earned=credits_earned,
                is_archived=False
            )
            db.add(stu)
            await db.flush()

            for acad_yr, term_sem, att, p_cgpa, m1, m2, int_m, bl, sem_cgpa, grd, rsk in terms:
                rec = SemesterAcademicRecord(
                    student_id=stu.id,
                    academic_year=acad_yr,
                    semester=term_sem,
                    attendance_percentage=att,
                    previous_cgpa=p_cgpa,
                    mid_1=m1,
                    mid_2=m2,
                    internal_marks=int_m,
                    backlogs=bl,
                    semester_cgpa=sem_cgpa,
                    grade=grd,
                    historical_risk_level=rsk
                )
                db.add(rec)

        await db.commit()
        print("[SUCCESS] Seeded 8 comprehensive student profiles with 32 historical semester records.")
        print("\n[READY] Seeding complete! Demo credentials:")
        print("   Admin:   admin@university.edu       / Password@123")
        print("   Faculty: faculty.cs@university.edu  / Password@123")
        print("   Student: student.alice@university.edu / Password@123\n")


if __name__ == "__main__":
    asyncio.run(seed())
