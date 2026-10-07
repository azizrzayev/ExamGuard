from django.db import models
from django.conf import settings
from .question import Question

class Exam(models.Model):
    EXAM_TYPES = [
        ('test', 'Test'),
        ('written', 'Yazılı'),
    ]
    title = models.CharField(max_length=200, verbose_name="İmtahan adı")
    exam_type = models.CharField(
        max_length=10,
        choices=EXAM_TYPES,
        default='test',
        verbose_name="İmtahan növü"
    )
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    duration_minutes = models.IntegerField(default=60, verbose_name="Müddət (dəqiqə)")
    max_warnings = models.IntegerField(default=3, verbose_name="Maksimum xəbərdarlıq limiti")
    questions_per_student = models.PositiveIntegerField(default=10, verbose_name="Hər tələbəyə düşən sual sayı")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Başlama vaxtı")
    groups = models.ManyToManyField('core.Group', related_name='exams', blank=True, verbose_name="Qruplar")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Ticket(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=50, verbose_name="Bilet adı (Məs: Bilet 1)")
    questions = models.ManyToManyField(Question, related_name='tickets')

    def __str__(self):
        return f"{self.exam.title} - {self.name}"