"""
Benchmark Academic Data Generator for ML Pipeline Evaluation.

Generates realistic longitudinal multi-semester student cohorts with:
- Temporal progression across 1 to 8 semesters
- Academic trajectories (improving, stable, declining)
- Pre-exam markers (Mid 1, Mid 2, Internal Marks, Attendance)
- Historical and current semester CGPA targets
- Categorical attributes (Gender, Department)
"""

import random
from pathlib import Path
import pandas as pd
import numpy as np

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "ml" / "data" / "raw" / "academic_records_benchmark.csv"


def generate_benchmark_dataset(num_students: int = 120, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    
    departments = ["CS", "IT", "ECE", "EEE", "MECH", "CIVIL", "AI", "DS"]
    genders = ["MALE", "FEMALE", "OTHER"]
    gender_weights = [0.52, 0.45, 0.03]
    
    first_names_m = ["Aarav", "Rohan", "Vikram", "Aditya", "Rahul", "Karthik", "Siddharth", "Nikhil", "Pranav", "Varun"]
    first_names_f = ["Ananya", "Pooja", "Sneha", "Kavya", "Divya", "Ishita", "Meera", "Rhea", "Tanvi", "Sanya"]
    last_names = ["Sharma", "Verma", "Reddy", "Singireddy", "Patel", "Rao", "Nair", "Iyer", "Chopra", "Gupta", "Deshmukh"]
    
    records = []
    
    for i in range(1, num_students + 1):
        dept = random.choice(departments)
        gender = random.choices(genders, weights=gender_weights)[0]
        if gender == "FEMALE":
            name = f"{random.choice(first_names_f)} {random.choice(last_names)}"
        else:
            name = f"{random.choice(first_names_m)} {random.choice(last_names)}"
            
        student_num = f"2023{dept.lower()}{i:03d}"
        base_age = random.randint(18, 20)
        
        # Student innate capability & academic trajectory archetype
        # 0: high achiever, 1: average stable, 2: struggling/improving, 3: at-risk declining
        archetype = random.choices([0, 1, 2, 3], weights=[0.25, 0.45, 0.15, 0.15])[0]
        
        if archetype == 0:
            base_cgpa = random.uniform(8.2, 9.6)
            base_attendance = random.uniform(85.0, 98.0)
            base_internal = random.uniform(80.0, 98.0)
            trend_slope = random.uniform(-0.05, 0.1)
        elif archetype == 1:
            base_cgpa = random.uniform(6.8, 8.2)
            base_attendance = random.uniform(75.0, 90.0)
            base_internal = random.uniform(65.0, 85.0)
            trend_slope = random.uniform(-0.1, 0.1)
        elif archetype == 2:
            base_cgpa = random.uniform(5.5, 6.8)
            base_attendance = random.uniform(65.0, 80.0)
            base_internal = random.uniform(50.0, 70.0)
            trend_slope = random.uniform(0.1, 0.3)  # Improving
        else:
            base_cgpa = random.uniform(5.0, 6.5)
            base_attendance = random.uniform(50.0, 72.0)
            base_internal = random.uniform(40.0, 60.0)
            trend_slope = random.uniform(-0.3, -0.05)  # Declining
            
        # Number of completed semesters for this student (between 4 and 8)
        num_semesters = random.randint(4, 8)
        current_prev_cgpa = base_cgpa
        cumulative_points = 0.0
        
        for sem in range(1, num_semesters + 1):
            sem_age = base_age + (sem - 1) // 2
            acad_year = f"{2020 + (sem - 1) // 2}-{2021 + (sem - 1) // 2}"
            
            # Semester attendance with noise
            attendance = max(35.0, min(100.0, base_attendance + (sem * trend_slope * 10) + np.random.normal(0, 4.0)))
            
            # Midterms & internal marks
            mid_1 = max(0.0, min(100.0, base_internal + np.random.normal(0, 6.0) + (sem * trend_slope * 5)))
            mid_2 = max(0.0, min(100.0, base_internal + np.random.normal(0, 6.0) + (sem * trend_slope * 5)))
            internal = max(0.0, min(100.0, base_internal + np.random.normal(0, 5.0)))
            
            # Backlogs
            if base_cgpa < 6.0 or attendance < 65.0:
                backlogs = random.choices([0, 1, 2, 3, 4], weights=[0.2, 0.4, 0.25, 0.1, 0.05])[0]
            elif base_cgpa < 7.5:
                backlogs = random.choices([0, 1, 2], weights=[0.75, 0.2, 0.05])[0]
            else:
                backlogs = 0
                
            # Previous CGPA for semester 1 is initial high school / entrance normalized CGPA
            if sem == 1:
                prev_cgpa = round(base_cgpa, 2)
            else:
                prev_cgpa = round(current_prev_cgpa, 2)
                
            # Target Semester CGPA (End of semester result)
            exam_factor = (mid_1 * 0.3 + mid_2 * 0.3 + internal * 0.4) / 10.0
            sem_cgpa = max(0.0, min(10.0, 0.6 * prev_cgpa + 0.4 * exam_factor - (backlogs * 0.25) + np.random.normal(0, 0.2)))
            sem_cgpa = round(sem_cgpa, 2)
            
            # Update cumulative for next semester
            cumulative_points += sem_cgpa
            current_prev_cgpa = cumulative_points / sem
            
            # Derived grade & risk (for optional tracking / verification of leakage removal)
            if sem_cgpa >= 9.0:
                grade = "O"
                risk = "LOW"
            elif sem_cgpa >= 8.0:
                grade = "A+"
                risk = "LOW"
            elif sem_cgpa >= 7.0:
                grade = "A"
                risk = "LOW"
            elif sem_cgpa >= 6.0:
                grade = "B"
                risk = "MEDIUM"
            else:
                grade = "C"
                risk = "HIGH"
                
            records.append({
                "student_number": student_num,
                "name": name,
                "gender": gender,
                "age": sem_age,
                "department_code": dept,
                "semester": sem,
                "academic_year": acad_year,
                "attendance_percentage": round(attendance, 2),
                "previous_cgpa": prev_cgpa,
                "mid_1": round(mid_1, 2),
                "mid_2": round(mid_2, 2),
                "internal_marks": round(internal, 2),
                "backlogs": backlogs,
                "semester_cgpa": sem_cgpa,
                "grade": grade,
                "risk_level": risk,
            })
            
    df = pd.DataFrame(records)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df)} longitudinal academic records for {num_students} students across 8 semesters at {OUTPUT_PATH}")
    return df


if __name__ == "__main__":
    generate_benchmark_dataset()
