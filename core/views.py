from core.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.forms import GroupForm
from core.models.exam import Exam
from core.forms import GroupForm, ExamForm
@login_required
def dashboard_view(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    return redirect('student_dashboard')
@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            return redirect('teacher_dashboard')  
    else:
        form = ExamForm()

    exams = Exam.objects.filter(created_by=request.user)
    return render(request, 'teacher_dashboard.html', {
        'exam_form': form,
        'exams': exams
    })
@login_required
def teacher_groups(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.teacher = request.user
            group.save()
            return redirect('teacher_groups')
    else:
        form = GroupForm()

    groups = Group.objects.filter(teacher=request.user)
    return render(request, 'teacher_groups.html', {
        'group_form': form,
        'groups': groups,
    })
@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html')



@login_required
def delete_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    if request.method == 'POST':
        exam.delete()
    return redirect('teacher_dashboard')


@login_required
def add_question_view(request, exam_id):
    is_teacher_user = getattr(request.user, 'is_teacher', False)
    if callable(is_teacher_user):
        is_teacher_user = is_teacher_user()
    if not is_teacher_user:
        return redirect('student_dashboard')
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    return redirect('teacher_dashboard')