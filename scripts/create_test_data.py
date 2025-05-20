import os
import sys
import django
import random
from django.contrib.auth import get_user_model
from django.db import transaction

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from course.models import Program, Course, CourseAllocation
from core.models import Semester

User = get_user_model()

def create_test_data():
    with transaction.atomic():
        # Create test programs
        programs = [
            {
                'title': 'Computer Science',
                'summary': 'Bachelor of Science in Computer Science'
            },
            {
                'title': 'Information Technology',
                'summary': 'Bachelor of Science in Information Technology'
            },
            {
                'title': 'Software Engineering',
                'summary': 'Bachelor of Science in Software Engineering'
            }
        ]
        
        created_programs = []
        for program_data in programs:
            program, created = Program.objects.get_or_create(
                title=program_data['title'],
                defaults={'summary': program_data['summary']}
            )
            created_programs.append(program)
            print(f"Created program: {program.title}")

        # Create test courses
        courses_data = [
            # Computer Science courses
            {
                'title': 'Introduction to Programming',
                'code': 'CS101',
                'credit': 3,
                'program': created_programs[0],
                'level': 'Bachelor',
                'year': 1,
                'semester': 'First',
                'is_elective': False
            },
            {
                'title': 'Data Structures and Algorithms',
                'code': 'CS201',
                'credit': 4,
                'program': created_programs[0],
                'level': 'Bachelor',
                'year': 2,
                'semester': 'First',
                'is_elective': False
            },
            {
                'title': 'Database Systems',
                'code': 'CS301',
                'credit': 3,
                'program': created_programs[0],
                'level': 'Bachelor',
                'year': 3,
                'semester': 'Second',
                'is_elective': False
            },
            # Information Technology courses
            {
                'title': 'Web Development',
                'code': 'IT101',
                'credit': 3,
                'program': created_programs[1],
                'level': 'Bachelor',
                'year': 1,
                'semester': 'First',
                'is_elective': False
            },
            {
                'title': 'Network Security',
                'code': 'IT201',
                'credit': 4,
                'program': created_programs[1],
                'level': 'Bachelor',
                'year': 2,
                'semester': 'Second',
                'is_elective': False
            },
            # Software Engineering courses
            {
                'title': 'Software Design Patterns',
                'code': 'SE301',
                'credit': 3,
                'program': created_programs[2],
                'level': 'Bachelor',
                'year': 3,
                'semester': 'First',
                'is_elective': False
            },
            {
                'title': 'Software Testing',
                'code': 'SE401',
                'credit': 4,
                'program': created_programs[2],
                'level': 'Bachelor',
                'year': 4,
                'semester': 'Second',
                'is_elective': False
            }
        ]

        created_courses = []
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults=course_data
            )
            created_courses.append(course)
            print(f"Created course: {course.title} ({course.code})")

        # Get or create lecturers
        lecturers = User.objects.filter(is_lecturer=True)
        if not lecturers.exists():
            print("No lecturers found. Please create some lecturers first.")
            return

        # Allocate courses to lecturers
        for lecturer in lecturers:
            # Randomly select 2-3 courses for each lecturer
            num_courses = random.randint(2, 3)
            selected_courses = random.sample(created_courses, num_courses)
            
            allocation, created = CourseAllocation.objects.get_or_create(
                lecturer=lecturer
            )
            allocation.courses.set(selected_courses)
            print(f"Allocated courses to lecturer {lecturer.get_full_name}:")
            for course in selected_courses:
                print(f"  - {course.title} ({course.code})")

if __name__ == '__main__':
    print("Creating test data...")
    create_test_data()
    print("Test data creation completed!") 