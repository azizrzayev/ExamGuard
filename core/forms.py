from django import forms
from core.models import Question, Exam, Group

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 
            'description', 
            'duration_minutes', 
            'max_warnings', 
            'questions_per_student', 
            'start_time', 
            'groups'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İmtahan Adı'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıqlama'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Müddət (dəqiqə)'}),
            'max_warnings': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Maksimum xəbərdarlıq sayı'}),
            'questions_per_student': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'groups': forms.CheckboxSelectMultiple(),
        }
    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['groups'].queryset = Group.objects.filter(teacher=teacher)
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

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Məs: 2445a'}),
        }