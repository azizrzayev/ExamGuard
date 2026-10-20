from django.db import models


class CodeTask(models.Model):
    exam = models.ForeignKey(
        "core.Exam", on_delete=models.CASCADE, related_name="code_tasks"
    )
    title = models.CharField(max_length=150, verbose_name="Başlıq")
    description = models.TextField(verbose_name="Tapşırığın mətni")
    starter_code = models.TextField(blank=True, verbose_name="Başlanğıc kod")

    def __str__(self):
        return self.title


class CodeTestCase(models.Model):
    task = models.ForeignKey(
        CodeTask, on_delete=models.CASCADE, related_name="test_cases"
    )
    input_data = models.TextField(blank=True, verbose_name="Giriş")
    expected_output = models.TextField(verbose_name="Gözlənilən çıxış")
    is_hidden = models.BooleanField(default=False, verbose_name="Gizli test")

    def __str__(self):
        return f"{self.task.title} testi"