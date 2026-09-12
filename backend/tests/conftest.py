import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash
from backend.app.models.user import User, UserRole
from backend.app.models.department import Department
from backend.app.models.student import StudentProfile, GenderEnum
from backend.app.models.faculty import FacultyProfile
from backend.app.models.academic_record import SemesterAcademicRecord
from backend.app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # Seed test base data
        dept = Department(code="CS", name="Computer Science")
        session.add(dept)
        await session.flush()

        admin = User(
            email="admin.test@university.edu",
            hashed_password=get_password_hash("TestPass@123"),
            full_name="Admin Test",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        faculty = User(
            email="faculty.test@university.edu",
            hashed_password=get_password_hash("TestPass@123"),
            full_name="Faculty Test",
            role=UserRole.FACULTY,
            is_active=True,
            is_verified=True
        )
        student_user_1 = User(
            email="student1.test@university.edu",
            hashed_password=get_password_hash("TestPass@123"),
            full_name="Student One",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True
        )
        student_user_2 = User(
            email="student2.test@university.edu",
            hashed_password=get_password_hash("TestPass@123"),
            full_name="Student Two",
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=True
        )
        session.add_all([admin, faculty, student_user_1, student_user_2])
        await session.flush()

        faculty_prof = FacultyProfile(
            user_id=faculty.id,
            employee_number="EMP-TEST-001",
            department_id=dept.id,
            designation="Professor"
        )
        session.add(faculty_prof)

        student_prof_1 = StudentProfile(
            user_id=student_user_1.id,
            student_number="STU-TEST-001",
            name="Student One",
            gender=GenderEnum.FEMALE,
            age=20,
            department_id=dept.id,
            enrollment_year=2023,
            current_semester=3,
            cumulative_gpa=8.5,
            is_archived=False
        )
        student_prof_2 = StudentProfile(
            user_id=student_user_2.id,
            student_number="STU-TEST-002",
            name="Student Two",
            gender=GenderEnum.MALE,
            age=21,
            department_id=dept.id,
            enrollment_year=2023,
            current_semester=3,
            cumulative_gpa=6.8,
            is_archived=False
        )
        session.add_all([student_prof_1, student_prof_2])
        await session.flush()

        rec = SemesterAcademicRecord(
            student_id=student_prof_1.id,
            academic_year="2023-2024",
            semester=1,
            attendance_percentage=90.0,
            previous_cgpa=None,
            mid_1=80.0,
            mid_2=85.0,
            internal_marks=82.5,
            backlogs=0,
            semester_cgpa=8.5,
            grade="A",
            historical_risk_level="LOW"
        )
        session.add(rec)
        await session.commit()

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_token(client: AsyncClient) -> str:
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "admin.test@university.edu", "password": "TestPass@123"}
    )
    return res.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def faculty_token(client: AsyncClient) -> str:
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "faculty.test@university.edu", "password": "TestPass@123"}
    )
    return res.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def student1_token(client: AsyncClient) -> str:
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "student1.test@university.edu", "password": "TestPass@123"}
    )
    return res.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def student2_token(client: AsyncClient) -> str:
    res = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "student2.test@university.edu", "password": "TestPass@123"}
    )
    return res.json()["access_token"]
