from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Giriş və Çıxış
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Əsas səhifə və panellər
    path('', views.dashboard_view, name='dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),

    # İmtahan silmə marşrutu
    path('teacher/exam/delete/<int:exam_id>/', views.delete_exam_view, name='delete_exam'),
]