from django.contrib import admin
from .models import (
    StudentPerformance,
    LecturerPerformance,
    CourseProgress,
    SystemAnalytics
)

@admin.register(StudentPerformance)
class StudentPerformanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'semester', 'academic_year', 'overall_grade', 'created_at')
    list_filter = ('semester', 'academic_year', 'course')
    search_fields = ('student__user__username', 'student__user__email', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(LecturerPerformance)
class LecturerPerformanceAdmin(admin.ModelAdmin):
    list_display = ('lecturer', 'course', 'semester', 'academic_year', 'student_satisfaction', 'created_at')
    list_filter = ('semester', 'academic_year', 'course')
    search_fields = ('lecturer__user__username', 'lecturer__user__email', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('course', 'semester', 'academic_year', 'enrollment_count', 'completion_rate', 'created_at')
    list_filter = ('semester', 'academic_year')
    search_fields = ('course__title', 'course__code')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(SystemAnalytics)
class SystemAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'active_users', 'total_courses', 'total_enrollments', 'system_uptime')
    list_filter = ('date',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date',)
