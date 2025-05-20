from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from course.models import Course, Enrollment, Resource, Assignment, Grade, Program
from analytics.models import StudentPerformance, LecturerPerformance, CourseProgress, SystemMetrics
import random
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.core import mail

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates test data for analytics system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating test data...')

        # Temporarily disable email sending
        original_backend = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

        try:
            # Create test users
            self.create_test_users()
            
            # Create test courses
            courses = self.create_test_courses()
            
            # Create enrollments
            self.create_test_enrollments(courses)
            
            # Create resources and assignments
            self.create_test_resources_and_assignments(courses)
            
            # Create grades
            self.create_test_grades()
            
            # Create performance data
            self.create_test_performance_data()
            
            # Create system metrics
            self.create_test_system_metrics()

            self.stdout.write(self.style.SUCCESS('Successfully generated test data'))
        finally:
            # Restore original email backend
            settings.EMAIL_BACKEND = original_backend

    @transaction.atomic
    def create_test_users(self):
        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')

        # Create test students
        for i in range(1, 21):
            username = f'student{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='student123',
                    is_student=True,
                    first_name=f'Student{i}',
                    last_name='Test'
                )

        # Create test lecturers
        for i in range(1, 6):
            username = f'lecturer{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='lecturer123',
                    is_lecturer=True,
                    first_name=f'Lecturer{i}',
                    last_name='Test'
                )

    def create_test_courses(self):
        courses = []
        subjects = ['Mathematics', 'Physics', 'Computer Science', 'English', 'History']
        levels = ['Beginner', 'Intermediate', 'Advanced']
        
        # Create a test program first
        program = Program.objects.create(
            title='Test Program',
            summary='Test program for analytics'
        )
        
        for subject in subjects:
            for level in levels:
                course = Course.objects.create(
                    title=f'{subject} {level}',
                    code=f'{subject[:3].upper()}-{level[:3].upper()}',
                    summary=f'Test course for {subject} at {level} level',
                    program=program,
                    level=level,
                    year=1,
                    semester='Fall',
                    is_elective=False
                )
                courses.append(course)
        
        return courses

    def create_test_enrollments(self, courses):
        students = User.objects.filter(is_student=True)
        for student in students:
            # Enroll each student in 3-5 random courses
            num_courses = random.randint(3, 5)
            selected_courses = random.sample(list(courses), num_courses)
            
            for course in selected_courses:
                Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrollment_date=timezone.now() - timedelta(days=random.randint(1, 30))
                )

    def create_test_resources_and_assignments(self, courses):
        resource_types = ['Document', 'Video', 'Link']
        assignment_types = ['Homework', 'Project', 'Essay', 'Presentation']
        
        for course in courses:
            # Create 5-8 resources per course
            for i in range(random.randint(5, 8)):
                Resource.objects.create(
                    course=course,
                    title=f'Resource {i+1} for {course.title}',
                    description=f'Test resource {i+1}',
                    resource_type=random.choice(resource_types),
                    created_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )
            
            # Create 3-5 assignments per course
            for i in range(random.randint(3, 5)):
                Assignment.objects.create(
                    course=course,
                    title=f'Assignment {i+1} for {course.title}',
                    description=f'Test assignment {i+1}',
                    assignment_type=random.choice(assignment_types),
                    due_date=timezone.now() + timedelta(days=random.randint(1, 30))
                )

    def create_test_grades(self):
        enrollments = Enrollment.objects.all()
        for enrollment in enrollments:
            # Create grades for assignments
            for assignment in enrollment.course.assignment_set.all():
                Grade.objects.create(
                    student=enrollment.student,
                    assignment=assignment,
                    score=random.uniform(60, 100),
                    feedback='Test feedback',
                    graded_at=timezone.now() - timedelta(days=random.randint(1, 15))
                )

    def create_test_performance_data(self):
        # Create student performance data
        for student in User.objects.filter(is_student=True):
            for enrollment in student.enrollment_set.all():
                StudentPerformance.objects.create(
                    student=student,
                    course=enrollment.course,
                    semester=enrollment.course.semester,
                    academic_year='2023-2024',  # Hardcoded for test data
                    quiz_average=random.uniform(70, 95),
                    assignment_average=random.uniform(75, 95),
                    attendance_rate=random.uniform(80, 100),
                    overall_grade=random.uniform(75, 95)
                )

        # Create lecturer performance data
        for lecturer in User.objects.filter(is_lecturer=True):
            for course in Course.objects.all():  # Changed to get all courses since lecturer field doesn't exist
                LecturerPerformance.objects.create(
                    lecturer=lecturer,
                    course=course,
                    semester=course.semester,
                    academic_year='2023-2024',  # Hardcoded for test data
                    student_satisfaction=random.uniform(80, 100),
                    course_completion_rate=random.uniform(85, 100),
                    average_student_grade=random.uniform(75, 95),
                    resource_utilization=random.uniform(70, 95)
                )

        # Create course progress data
        for course in Course.objects.all():
            CourseProgress.objects.create(
                course=course,
                semester=course.semester,
                academic_year='2023-2024',  # Hardcoded for test data
                enrollment_count=course.enrollment_set.count(),
                completion_rate=random.uniform(80, 100),
                dropout_rate=random.uniform(0, 10),
                resource_usage=random.uniform(70, 95)
            )

    def create_test_system_metrics(self):
        # Create system metrics for the last 30 days
        for i in range(30):
            SystemMetrics.objects.create(
                timestamp=timezone.now() - timedelta(days=i),
                cpu_usage=random.uniform(20, 80),
                memory_usage=random.uniform(40, 90),
                disk_usage=random.uniform(50, 85),
                response_time=random.uniform(0.1, 2.0),
                active_users=random.randint(50, 200),
                total_requests=random.randint(1000, 5000)
            ) 