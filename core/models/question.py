from django.db import models

class Question(models.Model):
    QUESTION_TYPES = (
        ('test', 'Test (A-D)'),
        ('written', 'Yazılı'),
        ('code', 'Proqramlaşdırma (Kod)'),
    )
    
    text = models.TextField(verbose_name="Sualın mətni")
    points = models.FloatField(default=1.0, verbose_name="Sualın maks balı")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='test')
    
    # Test sualları üçün variantlar
    option_a = models.CharField(max_length=255, blank=True, null=True)
    option_b = models.CharField(max_length=255, blank=True, null=True)
    option_c = models.CharField(max_length=255, blank=True, null=True)
    option_d = models.CharField(max_length=255, blank=True, null=True)
    correct_option = models.CharField(max_length=1, blank=True, null=True, help_text="A, B, C və ya D")

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.text[:30]}..."

    def calculate_score(self, student_answer):
        """
        Qismən bal məntiqi:
        Test sualı üçün tam bal (0 və ya 1*points).
        Yazılı sual üçün avtomatik yoxlanmır (None qaytarır, müəllim yoxlayır).
        """
        if self.question_type == 'test':
            if student_answer and student_answer.strip().upper() == self.correct_option:
                return self.points
            return 0.0
        elif self.question_type == 'written':
            return None  # Müəllim paneldən manual qiymətləndirəcək
        return 0.0