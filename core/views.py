import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from pypdf import PdfReader
from core.forms import (GroupForm, AdminGroupForm, ExamForm, InstitutionForm, PDFUploadForm, TeacherForm, StudentForm)
from core.models import Group, ExamSession, Answer
from core.models.exam import Exam
from core.models.question import Question
from core.models.result import ExamResult
from core.services.pdf_import import parse_test_questions, parse_written_questions
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from core.models import Institution
from core.forms import InstitutionAdminForm
from core.code_import import parse_code_tasks
from core.code_runner import run_python
from core.models import CodeTask, CodeTestCase
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from core.code_runner import run_python, check_task
from core.models import CodeSubmission
from core.excel_import import parse_students_excel

User = get_user_model()

def role_login_view(request, allowed_roles, title, subtitle):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user and user.role in allowed_roles:
            login(request, user)
            return redirect('dashboard')

        error = 'İstifadəçi adı, şifrə və ya giriş növü yanlışdır.'

    return render(request, 'login.html', {
        'error': error,
        'login_title': title,
        'login_subtitle': subtitle,
    })


def user_login_view(request):
    return role_login_view(
        request,
        ('teacher', 'student'),
        'ExamGuard',
        'Müəllim və tələbə girişi',
    )


def admin_login_view(request):
    return role_login_view(
        request,
        ('admin',),
        'ExamGuard Admin',
        'Müəssisə inzibatçısı girişi',
    )


def superadmin_login_view(request):
    return role_login_view(
        request,
        ('superadmin',),
        'ExamGuard Control',
        'Sistem superadmin girişi',
    )

@login_required
def admin_dashboard(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    institution = request.user.institution

    context = {
        'institution': institution,
        'teacher_count': User.objects.filter(
            institution=institution, role='teacher'
        ).count(),
        'student_count': User.objects.filter(
            institution=institution, role='student'
        ).count(),
    }

    return render(request, 'admin_dashboard.html', context)

@login_required
def institution_admin_create_view(request, institution_id):
    # Superadmin yoxlaması
    if not request.user.is_superadmin():
        return redirect('dashboard')

    institution = get_object_or_404(Institution, id=institution_id)

    if request.method == 'POST':
        form = InstitutionAdminForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'admin'
            user.institution = institution
            user.save()

            messages.success(
                request,
                f"'{institution.name}' üçün inzibatçı (admin) uğurla yaradıldı.",
            )
            return redirect('superadmin_dashboard')
    else:
        form = InstitutionAdminForm()

    return render(
        request,
        'institution_admin_create.html',
        {
            'form': form,
            'institution': institution,
        },
    )
@login_required
def teacher_create_view(request):

    if not request.user.is_admin():
        return redirect('dashboard')

    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'teacher'
            user.institution = request.user.institution  
            user.save()

            messages.success(request, "Müəllim uğurla yaradıldı.")
            return redirect('admin_dashboard')
    else:
        form = TeacherForm()

    return render(request, 'teacher_create.html', {'form': form})
@login_required
def admin_groups_view(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    institution = request.user.institution

    if request.method == 'POST':
        form = AdminGroupForm(
            request.POST,
            institution=institution,
        )

        if form.is_valid():
            group = form.save(commit=False)
            group.institution = institution
            group.save()

            messages.success(
                request,
                f"'{group.name}' qrupu uğurla yaradıldı.",
            )
            return redirect('admin_groups')
    else:
        form = AdminGroupForm(institution=institution)

    groups = Group.objects.filter(
        institution=institution,
    ).select_related('teacher').order_by('name')

    return render(request, 'admin_groups.html', {
        'group_form': form,
        'groups': groups,
    })
@login_required
def institution_create_view(request):
    # Superadmin yoxlaması
    if not request.user.is_superadmin():
        return redirect('dashboard')

    if request.method == 'POST':
        form = InstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Müəssisə yaradıldı.")
            return redirect('superadmin_dashboard')
    else:
        form = InstitutionForm()

    return render(request, 'institution_create.html', {'form': form})
@login_required
def dashboard_view(request):
    if request.user.is_teacher():
        return redirect('teacher_dashboard')
    
    if request.user.is_superadmin():
        return redirect('superadmin_dashboard')
    
    if request.user.is_admin():
        return redirect('admin_dashboard')
    return redirect('student_dashboard')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher():
        return redirect('student_dashboard')

    exams = Exam.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'teacher_dashboard.html', {'exams': exams})



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
            exam_type = form.cleaned_data.get('exam_type')
            question_type = exam_type if exam_type in ('written', 'code') else 'test'

            questions = []
            code_tasks = []
            errors = []
            full_text = ""

            try:
                reader = PdfReader(pdf_form.cleaned_data['pdf_file'])
                full_text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                if question_type == 'code':
                    code_tasks, errors = parse_code_tasks(full_text)
                elif question_type == 'written':
                    questions, errors = parse_written_questions(full_text)
                else:
                    questions, errors = parse_test_questions(full_text)
            except Exception:
                pdf_form.add_error('pdf_file', 'PDF faylını oxumaq olmadı.')
                full_text = None

            if full_text is not None:
                # Kod imtahanı: etalon kodu işlədib gözlənilən çıxışları hesabla
                if question_type == 'code' and not errors:
                    for i, task in enumerate(code_tasks, start=1):
                        task['tests'] = []
                        for inp in task['inputs']:
                            out, err = run_python(task['reference_code'], inp)
                            if err:
                                errors.append(f"Tapşırıq {i}: etalon kod xəta verdi: {err[:150]}")
                                break
                            task['tests'].append((inp, out))

                found = code_tasks if question_type == 'code' else questions

                if not full_text.strip() or (not found and not errors):
                    pdf_form.add_error(
                        'pdf_file', 'PDF-də düzgün formatlı suallar tapılmadı.'
                    )
                elif errors:
                    for error in errors:
                        pdf_form.add_error('pdf_file', error)
                else:
                    with transaction.atomic():
                        exam = form.save(commit=False)
                        exam.created_by = request.user
                        exam.save()
                        form.save_m2m()

                        if question_type == 'code':
                            for task in code_tasks:
                                ct = CodeTask.objects.create(
                                    exam=exam,
                                    title=task['title'],
                                    description=task['description'],
                                    reference_code=task['reference_code'],
                                    points=task['points'],
                                    starter_code=task['starter_code'],
                                )
                                CodeTestCase.objects.bulk_create([
                                    CodeTestCase(
                                        task=ct, input_data=inp, expected_output=out,
                                        is_hidden=(idx > 0),
                                    )
                                    for idx, (inp, out) in enumerate(task['tests'])
                                ])
                        else:
                            Question.objects.bulk_create([
                                Question(
                                    exam=exam,
                                    created_by=request.user,
                                    question_type=question_type,
                                    **q,
                                )
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
def student_create_view(request):
    if not request.user.is_admin():
        return redirect('dashboard')

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'
            user.institution = request.user.institution
            user.save()
            messages.success(request, "Tələbə uğurla yaradıldı.")
            return redirect('admin_dashboard')
    else:
        form = StudentForm()

    return render(request, 'student_create.html', {'form': form})

@login_required
def student_import_view(request):
    if not request.user.is_admin() or request.user.institution is None:
        return redirect('dashboard')

    institution = request.user.institution

    if request.method == 'POST':
        file = request.FILES.get('excel_file')

        if file is None:
            messages.error(request, "Fayl seçilməyib.")
        elif not file.name.lower().endswith('.xlsx'):
            messages.error(request, "Yalnız .xlsx formatı qəbul olunur.")
        elif file.size > 2 * 1024 * 1024:
            messages.error(request, "Fayl 2 MB-dan böyük ola bilməz.")
        else:
            group_names = set(
                Group.objects.filter(institution=institution).values_list('name', flat=True)
            )
            existing = {
                u: (r, i)
                for u, r, i in User.objects.values_list('username', 'role', 'institution_id')
            }
            rows, fatal = parse_students_excel(file, group_names, existing, institution.id)

            if fatal:
                messages.error(request, fatal)
            else:
                valid = [r for r in rows if not r['errors']]
                request.session['import_rows'] = valid
                return render(request, 'student_import.html', {
                    'rows': rows,
                    'ok_count': len(valid),
                    'error_count': len(rows) - len(valid),
                    'preview': True,
                })

    return render(request, 'student_import.html', {'preview': False})


@login_required
def student_import_confirm_view(request):
    if not request.user.is_admin() or request.user.institution is None:
        return redirect('dashboard')
    if request.method != 'POST':
        return redirect('student_import')

    institution = request.user.institution
    rows = request.session.pop('import_rows', None)
    if not rows:
        messages.error(request, "Yükləmə vaxtı bitib. Faylı yenidən yüklə.")
        return redirect('student_import')

    created = added = skipped = 0
    with transaction.atomic():
        for row in rows:
            group = Group.objects.filter(
                name=row['group'], institution=institution
            ).first()
            if group is None:
                skipped += 1
                continue

            user = User.objects.filter(username=row['username']).first()
            if user is None:
                user = User.objects.create_user(
                    username=row['username'],
                    password=row['password'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    role='student',
                    institution=institution,
                )
                created += 1
            elif user.role == 'student' and user.institution_id == institution.id:
                added += 1
            else:
                skipped += 1
                continue

            group.students.add(user)

    messages.success(
        request,
        f"Yeni tələbə: {created}, mövcud tələbə qrupa əlavə olundu: {added}, keçilən: {skipped}.",
    )
    return redirect('admin_dashboard')

@login_required
def grade_written_view(request, exam_id, student_id):
    if not request.user.is_teacher():
        return redirect('dashboard')

    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    student = get_object_or_404(User, id=student_id)
    result = get_object_or_404(ExamResult, exam=exam, student=student)

    answers = (
        Answer.objects
        .filter(student=student, question__exam=exam, question__question_type='written')
        .select_related('question')
        .order_by('question_id')
    )

    if request.method == 'POST':
        for a in answers:
            raw = request.POST.get(f'points_{a.id}', '').strip().replace(',', '.')
            if raw == '':
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            a.awarded_points = max(0.0, min(value, a.question.points))
            a.save()

        # Yekun nəticəni yenidən hesabla
        all_answers = Answer.objects.filter(
            student=student, question__exam=exam
        ).select_related('question')
        result.score = sum(x.awarded_points or 0 for x in all_answers)
        result.total = sum(x.question.points for x in all_answers)
        result.save()

        messages.success(request, "Ballar saxlanıldı.")
        return redirect('exam_results', exam_id=exam.id)

    return render(request, 'grade_written.html', {
        'exam': exam,
        'student': student,
        'result': result,
        'answers': answers,
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
    if request.user.role != 'student':
        return redirect('dashboard')

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        groups__students=request.user,
    )
    # Artıq təhvil verilibsə
    if ExamResult.objects.filter(student=request.user, exam=exam).exists():
        return redirect('student_dashboard')

    # İmtahan vaxtı yoxlanışı (POST üçün 30 saniyə güzəşt)
    if not exam.is_open(grace_seconds=30):
        return redirect('student_dashboard')

    session, created = ExamSession.objects.get_or_create(
        student=request.user, exam=exam
    )

    if request.method == 'GET' and not created and not exam.allow_reentry:
        return redirect('student_dashboard')

 
    if created:
        pool = list(exam.questions.all())
        n = exam.questions_per_student
        chosen = random.sample(pool, n) if n and n < len(pool) else pool
        session.questions.set(chosen)

       
    if exam.exam_type == 'code':
        tasks = list(exam.code_tasks.all().order_by('id'))
        subs = {
            s.task_id: s
            for s in CodeSubmission.objects.filter(student=request.user, task__in=tasks)
        }

        if request.method == 'POST':
            score = 0.0
            total = 0.0
            for task in tasks:
                sub = subs.get(task.id)
                if sub is None:
                 
                    code = request.POST.get(f'code_{task.id}', '')
                    passed, count = check_task(task, code)
                    earned = task.points * passed / count if count else 0.0
                    CodeSubmission.objects.update_or_create(
                        student=request.user, task=task,
                        defaults={'code': code, 'passed': passed, 'total': count, 'score': earned},
                    )
                else:
                    earned = sub.score
                score += earned
                total += task.points
            ExamResult.objects.update_or_create(
                student=request.user, exam=exam,
                defaults={'score': score, 'total': total},
            )
            return redirect('student_dashboard')

        for task in tasks:
            task.sub = subs.get(task.id)
            task.initial_code = task.sub.code if task.sub else task.starter_code

        return render(request, 'take_code_exam.html', {
            'exam': exam,
            'tasks': tasks,
            'remaining_seconds': exam.remaining_seconds(),
        })

    questions = session.questions.all()

    if request.method == 'POST':
        score = 0.0
        total = 0.0

        for question in questions:
            total += question.points
            value = request.POST.get(f'question_{question.id}', '').strip()

            if question.question_type == 'written':
                # Yazılı: mətn saxlanır, bal müəllim yoxlayanda verilir
                Answer.objects.update_or_create(
                    student=request.user, question=question,
                    defaults={'text_answer': value, 'selected_option': '', 'awarded_points': None},
                )
            else:
                # Test: avtomatik yoxlanır
                earned = question.calculate_score(value) or 0.0
                score += earned
                Answer.objects.update_or_create(
                    student=request.user, question=question,
                    defaults={'selected_option': value.upper()[:1], 'text_answer': '', 'awarded_points': earned},
                )

        ExamResult.objects.update_or_create(
            student=request.user, exam=exam,
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

@login_required
@require_POST
def run_code_view(request, exam_id):
    if request.user.role != 'student':
        return JsonResponse({'error': 'İcazəniz yoxdur.'}, status=403)

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        exam_type='code',
        groups__students=request.user,
    )


    if ExamResult.objects.filter(student=request.user, exam=exam).exists() \
            or not exam.is_open(grace_seconds=30):
        return JsonResponse({'error': 'İmtahan bağlıdır.'}, status=403)

    try:
        data = json.loads(request.body)
        task = CodeTask.objects.filter(id=int(data.get('task_id')), exam=exam).first()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Səhv sorğu.'}, status=400)

    if task is None:
        return JsonResponse({'error': 'Tapşırıq tapılmadı.'}, status=404)

    code = data.get('code', '')
    if len(code) > 20000:
        return JsonResponse({'error': 'Kod çox uzundur.'}, status=400)

    results = []
    for t in task.visible_tests():
        out, err = run_python(code, t.input_data)
        results.append({
            'input': t.input_data,
            'expected': t.expected_output,
            'output': out,
            'error': err,
            'ok': (not err and out == t.expected_output.strip()),
        })
    return JsonResponse({'results': results})
@login_required
@require_POST
def submit_task_view(request, exam_id):
    if request.user.role != 'student':
        return JsonResponse({'error': 'İcazəniz yoxdur.'}, status=403)

    exam = get_object_or_404(
        Exam,
        id=exam_id,
        exam_type='code',
        groups__students=request.user,
    )

    if ExamResult.objects.filter(student=request.user, exam=exam).exists() \
            or not exam.is_open(grace_seconds=30):
        return JsonResponse({'error': 'İmtahan bağlıdır.'}, status=403)

    try:
        data = json.loads(request.body)
        task = CodeTask.objects.filter(id=int(data.get('task_id')), exam=exam).first()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Səhv sorğu.'}, status=400)

    if task is None:
        return JsonResponse({'error': 'Tapşırıq tapılmadı.'}, status=404)

    code = data.get('code', '')
    if len(code) > 20000:
        return JsonResponse({'error': 'Kod çox uzundur.'}, status=400)

    passed, count = check_task(task, code)
    earned = task.points * passed / count if count else 0.0

    CodeSubmission.objects.update_or_create(
        student=request.user, task=task,
        defaults={'code': code, 'passed': passed, 'total': count, 'score': earned},
    )
    return JsonResponse({
        'task_id': task.id, 'passed': passed, 'total': count,
        'score': round(earned, 2), 'max': task.points,
    })