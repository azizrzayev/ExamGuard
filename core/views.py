import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from pypdf import PdfReader
from core.forms import GroupForm, ExamForm, PDFUploadForm
from core.models import Group, ExamSession, Answer
from core.models.exam import Exam
from core.models.question import Question
from core.models.result import ExamResult
from core.services.pdf_import import parse_test_questions
from django.contrib.auth import get_user_model
from core.models import Institution



@login_required
def dashboard_view(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    
    if request.user.is_superadmin():
        return redirect('superadmin_dashboard')
    return redirect('student_dashboard')


@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    exams = Exam.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'teacher_dashboard.html', {'exams': exams})

User = get_user_model()

@login_required
def superadmin_dashboard(request):

    if not request.user.is_superadmin():
        return redirect('dashboard')

    institutions = Institution.objects.all()

    context = {
        'institutions': institutions,
        'institution_count': institutions.count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'teacher_count': User.objects.filter(role='teacher').count(),
        'student_count': User.objects.filter(role='student').count(),
    }

    return render(request, 'superadmin_dashboard.html', context)

@login_required
def create_exam_view(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = ExamForm(request.POST, teacher=request.user)
        pdf_form = PDFUploadForm(request.POST, request.FILES)
        form_ok = form.is_valid()
        pdf_ok = pdf_form.is_valid()

        if form_ok and pdf_ok:
            try:
                reader = PdfReader(pdf_form.cleaned_data['pdf_file'])
                full_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                questions, errors = parse_test_questions(full_text)
            except Exception:
                pdf_form.add_error('pdf_file', 'PDF faylını oxumaq olmadı.')
            else:
                if not full_text.strip():
                    pdf_form.add_error(
                        'pdf_file', 'PDF-də düzgün formatlı suallar tapılmadı.'
                    )
                elif errors:
                    for error in errors:
                        pdf_form.add_error('pdf_file', error)
                elif not questions:
                    pdf_form.add_error(
                        'pdf_file', 'PDF-də düzgün formatlı suallar tapılmadı.'
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
                    messages.success(request, "İmtahan uğurla yaradıldı.")
                    return redirect('teacher_dashboard')
    else:
        form = ExamForm(teacher=request.user)
        pdf_form = PDFUploadForm()

    return render(request, 'exam_create.html', {
        'exam_form': form,
        'pdf_form': pdf_form,
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
    exams = [e for e in exams if not e.has_ended()]

    results = {
        r.exam_id: r
        for r in ExamResult.objects.filter(student=request.user)
    }
    for exam in exams:
        exam.result = results.get(exam.id)

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
    if not request.user.is_teacher():
        return redirect('student_dashboard')
    get_object_or_404(Exam, id=exam_id, created_by=request.user)
    return redirect('teacher_dashboard')


@login_required
def upload_exam_pdf(request, exam_id):
    if not request.user.is_teacher():
        return redirect("student_dashboard")
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    form = PDFUploadForm()
    if request.method == "POST":
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                reader = PdfReader(form.cleaned_data["pdf_file"])
                full_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
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
                    return render(request, "pdf_preview.html", {
                        "exam": exam,
                        "questions": questions,
                        "errors": errors,
                        "can_confirm": can_confirm,
                    })
    return render(request, "pdf_upload.html", {
        "exam": exam,
        "exam_form": form,
    })


@login_required
def start_exam_view(request, exam_id):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')

    exam = get_object_or_404(Exam, id=exam_id, groups__students=request.user)

    if ExamResult.objects.filter(student=request.user, exam=exam).exists():
        return redirect('student_dashboard')

    grace = 30 if request.method == 'POST' else 0
    if not exam.is_open(grace_seconds=grace):
        messages.error(request, "İmtahan hazırda açıq deyil.")
        return redirect('student_dashboard')

    session, created = ExamSession.objects.get_or_create(
        student=request.user,
        exam=exam,
    )

    if request.method == 'GET' and not created and not exam.allow_reentry:
        messages.error(request, "Bu imtahana yalnız bir dəfə girmək olar.")
        return redirect('student_dashboard')

    if created:
        all_questions = list(exam.questions.all())
        sample_size = min(len(all_questions), exam.questions_per_student)
        selected_questions = random.sample(all_questions, sample_size)
        session.questions.set(selected_questions)

    questions = session.questions.order_by('id')

    if request.method == 'POST':
        for q in questions:
            selected_option = request.POST.get(f'question_{q.id}')
            if not selected_option:
                continue

            Answer.objects.update_or_create(
                student=request.user,
                question=q,
                defaults={'selected_option': selected_option},
            )

        student_answers = Answer.objects.filter(
            student=request.user, question__exam=exam
        )

        score = len([ans for ans in student_answers if ans.is_correct()])
        total = len(questions)

        ExamResult.objects.update_or_create(
            student=request.user,
            exam=exam,
            defaults={'score': score, 'total': total},
        )
        return redirect('student_dashboard')
    return render(request, 'take_exam.html', {
        'exam': exam,
        'questions': questions,
        'remaining_seconds': exam.remaining_seconds(),
    })
@login_required
def exam_results_view(request, exam_id):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    results = exam.results.select_related('student').order_by('-score')
    return render(
        request,
        'exam_results.html',
        {
            'exam': exam,
            'results': results,
        },
    )
