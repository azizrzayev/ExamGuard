from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models.exam import Exam
from exams.forms import ExamForm
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
            return redirect('dashboard')  
    else:
        form = ExamForm()

    exams = Exam.objects.filter(created_by=request.user)
    return render(request, 'teacher_dashboard.html', {
        'form': form,
        'exams': exams
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