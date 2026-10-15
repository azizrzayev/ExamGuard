from django.db import models


class Institution(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Müəssisə adı",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaradılma tarixi",
    )

    class Meta:
        verbose_name = "Müəssisə"
        verbose_name_plural = "Müəssisələr"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def admins(self):
        return self.users.filter(role='admin')