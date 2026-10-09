from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Answer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers', verbose_name="Tələbə")
    question = models.ForeignKey('core.Question', on_delete=models.CASCADE, related_name='answers', verbose_name="Sual")
    selected_option = models.CharField(max_length=1, verbose_name="Seçilmiş variant")
    class Meta:
        unique_together = ('student', 'question')
    def is_correct(self):
        return self.selected_option.strip().upper() == self.question.correct_option.strip().upper()