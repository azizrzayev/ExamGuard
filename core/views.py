from core.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.forms import GroupForm, ExamForm, PDFUploadForm
from core.models.exam import Exam
from pypdf import PdfReader
from core.services.pdf_import import parse_test_questions
from core.models.question import Question
from django.db import transaction
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
        form = ExamForm(request.POST, teacher=request.user)
        pdf_form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid() and pdf_form.is_valid():
            try:
                reader = PdfReader(pdf_form.cleaned_data['pdf_file'])
                full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                questions, errors = parse_test_questions(full_text)
            except Exception:
                pdf_form.add_error('pdf_file', 'PDF faylını oxumaq olmadı.')
            else:
                if not full_text.strip():
                    pdf_form.add_error(
                        'pdf_file',
                        'PDF-də düzgün formatlı suallar tapılmadı.'
                    )
                elif errors:
                    for error in errors:
                        pdf_form.add_error('pdf_file', error)
                elif not questions:
                    pdf_form.add_error(
                        'pdf_file',
                        "PDF-də düzgün formatlı suallar tapılmadı."
                    )
                else:
                    with transaction.atomic():
                        exam = form.save(commit=False)
                        exam.created_by = request.user
                        exam.save()
                        form.save_m2m()

                        Question.objects.bulk_create([
                            Question(exam=exam, created_by=request.user, **q)
                            for q in questions
                    ])
                    return redirect('teacher_dashboard')
    else:
        form = ExamForm(teacher=request.user)
        pdf_form = PDFUploadForm()
    exams = Exam.objects.filter(created_by=request.user)
    return render(request, 'teacher_dashboard.html', {
        'exam_form': form,
        'pdf_form': pdf_form,
        'exams': exams,
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
    if request.user.is_teacher():
        return redirect('teacher_dashboard')

    exams = Exam.objects.filter(groups__students=request.user).distinct()

    return render(request, 'student_dashboard.html', {
        'exams': exams,
    })
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

@login_required
def upload_exam_pdf(request, exam_id):
    if not request.user.is_teacher():
        return redirect("student_dashboard")
    exam = get_object_or_404(
        Exam,
        id=exam_id,
        created_by=request.user,
    )
    form = PDFUploadForm()
    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                reader = PdfReader(form.cleaned_data["pdf_file"])
                full_text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )
            except Exception:
                form.add_error("pdf_file", "PDF faylını oxumaq mümkün olmadı.")
            else:
                if not full_text.strip():
                    form.add_error(
                        "pdf_file",
                        "PDF-dən mətn çıxmadı. Skan edilmiş PDF dəstəklənmir.",
                    )
                else:
                    questions, errors = parse_test_questions(full_text)
                    can_confirm = bool(questions) and not errors

                    if can_confirm:
                        request.session[f"pdf_preview_{exam.id}"] = questions
                    return render(
                        request,
                        "pdf_preview.html",
                        {
                            "exam": exam,
                            "questions": questions,
                            "errors": errors,
                            "can_confirm": can_confirm,
                        },
                    )
    return render(
        request,
        "pdf_upload.html",
        {
            "exam": exam,
            "exam_form": form,
        },
    )
@login_required
def start_exam_view(request, exam_id):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        groups__students=request.user,
    )

    questions = exam.questions.order_by('id')[:exam.questions_per_student]

    return render(request, 'take_exam.html', {
        'exam': exam,
        'questions': questions,
    })