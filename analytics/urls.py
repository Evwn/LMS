from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('student-performance/', views.StudentPerformanceView.as_view(), name='student_performance'),
    path('lecturer-performance/', views.LecturerPerformanceView.as_view(), name='lecturer_performance'),
    path('course-progress/', views.CourseProgressView.as_view(), name='course_progress'),
    path('system-analytics/', views.system_analytics, name='system_analytics'),
    path('real-time-metrics/', views.real_time_metrics, name='real_time_metrics'),
    path('performance-report/', views.performance_report, name='performance_report'),
    path('performance-report/student/<int:student_id>/', views.performance_report, name='student_performance_report'),
    path('performance-report/course/<int:course_id>/', views.performance_report, name='course_performance_report'),
    path('debug-performances/', views.debug_performances, name='debug_performances'),
    
    # Student Progress Report URLs
    path('student-progress/', views.StudentProgressView.as_view(), name='student_progress'),
    path('student-progress/<int:student_id>/', views.student_progress_report, name='student_progress_report'),
    path('student-progress/<int:student_id>/course/<int:course_id>/', views.student_progress_report, name='student_progress_report'),
    path('generate-progress-report/<int:student_id>/course/<int:course_id>/', views.generate_progress_report, name='generate_progress_report'),
    path('update-lecturer-performances/', views.update_all_lecturer_performances, name='update_lecturer_performances'),
] 