from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Giriş ve Çıxış
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Paneller
    path('', views.dashboard_view, name='dashboard'),
    path('home/', views.dashboard_view, name='home'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/institutions/new/', views.institution_create_view, name='institution_create'),

    # İmtahan əməliyyatları  
    path('teacher/exam/delete/<int:exam_id>/', views.delete_exam_view, name='delete_exam'),
    path('teacher/exam/<int:exam_id>/add-question/', views.add_question_view, name='add_question'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/exam/<int:exam_id>/upload-pdf/', views.upload_exam_pdf, name='upload_exam_pdf'),
    path('student/exam/<int:exam_id>/', views.start_exam_view, name='start_exam'),
    path('teacher/exams/new/', views.create_exam_view, name='create_exam'),
    path('teacher/exams/<int:exam_id>/results/', views.exam_results_view, name='exam_results'),
]