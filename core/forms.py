from django import forms
from core.models import Question, Exam
from core.patterns.factory import QuestionFactory


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration_minutes', 'max_warnings']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration is not None and duration <= 0:
            raise forms.ValidationError("İmtahan müddəti 0-dan böyük olmalıdır.")
        return duration

    def clean_max_warnings(self):
        warnings = self.cleaned_data.get('max_warnings')
        if warnings is not None and warnings < 0:
            raise forms.ValidationError("Xəbərdarlıq sayı mənfi ola bilməz.")
        return warnings


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'points', 'question_type', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_question_type'}),
            'option_a': forms.TextInput(attrs={'class': 'form-control'}),
            'option_b': forms.TextInput(attrs={'class': 'form-control'}),
            'option_c': forms.TextInput(attrs={'class': 'form-control'}),
            'option_d': forms.TextInput(attrs={'class': 'form-control'}),
            'correct_option': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'A, B, C və ya D'}),
        }

    def save(self, commit=True):
        data = self.cleaned_data
        question = QuestionFactory.create_question(
            question_type=data.get('question_type'),
            text=data.get('text'),
            points=data.get('points'),
            correct_option=data.get('correct_option'),
            option_a=data.get('option_a'),
            option_b=data.get('option_b'),
            option_c=data.get('option_c'),
            option_d=data.get('option_d'),
        )
        return question