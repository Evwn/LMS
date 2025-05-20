from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from course.models import Course, CourseAllocation
from quiz.models import Quiz, Sitting
from accounts.models import Student
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class StudentPerformance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, choices=settings.SEMESTER_CHOICES)
    academic_year = models.CharField(max_length=20)
    
    # Performance Metrics
    quiz_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assignment_average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    participation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Additional Metrics
    time_spent_learning = models.DurationField(default=0)
    resources_accessed = models.IntegerField(default=0)
    discussion_participation = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course', 'semester', 'academic_year')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student} - {self.course} ({self.semester} {self.academic_year})"

class LecturerPerformance(models.Model):
    lecturer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_lecturer': True})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, choices=settings.SEMESTER_CHOICES)
    academic_year = models.CharField(max_length=20)
    
    # Performance Metrics
    student_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    course_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_student_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    resource_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Additional Metrics
    feedback_responses = models.IntegerField(default=0)
    active_engagement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    course_updates = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('lecturer', 'course', 'semester', 'academic_year')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.lecturer} - {self.course} ({self.semester} {self.academic_year})"

class CourseProgress(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20, choices=settings.SEMESTER_CHOICES)
    academic_year = models.CharField(max_length=20)
    
    # Progress Metrics
    enrollment_count = models.IntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dropout_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Resource Usage
    resource_views = models.IntegerField(default=0)
    discussion_posts = models.IntegerField(default=0)
    assignment_submissions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course', 'semester', 'academic_year')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course} Progress ({self.semester} {self.academic_year})"

    @property
    def resource_usage(self):
        """Calculate resource usage as a percentage of expected usage"""
        if self.enrollment_count == 0:
            return 0
            
        # Total resource interactions
        total_interactions = self.resource_views + self.discussion_posts + self.assignment_submissions
        
        # Expected interactions (assuming 20 interactions per student is 100%)
        expected_interactions = self.enrollment_count * 20
        
        if expected_interactions == 0:
            return 0
            
        # Calculate percentage (max 100%)
        usage_percentage = (total_interactions / expected_interactions) * 100
        return min(100, round(usage_percentage, 1))

class SystemAnalytics(models.Model):
    date = models.DateField(unique=True)
    
    # System-wide Metrics
    active_users = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    total_quizzes = models.IntegerField(default=0)
    total_assignments = models.IntegerField(default=0)
    
    # Performance Metrics
    system_uptime = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_response_time = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # User Engagement
    daily_logins = models.IntegerField(default=0)
    resource_accesses = models.IntegerField(default=0)
    discussion_activities = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "System Analytics"

    def __str__(self):
        return f"System Analytics for {self.date}"

class StudentProgressReport(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_reports')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    semester = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=20)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assignment_completion = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quiz_scores = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    midterm_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_grade = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    participation_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course', 'semester', 'academic_year')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} Progress Report"

class SystemMetrics(models.Model):
    timestamp = models.DateTimeField()
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()
    response_time = models.FloatField()
    active_users = models.IntegerField()
    total_requests = models.IntegerField()

    def __str__(self):
        return f"{self.timestamp} | CPU: {self.cpu_usage}% | Mem: {self.memory_usage}% | Disk: {self.disk_usage}%"
