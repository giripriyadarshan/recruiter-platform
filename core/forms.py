from django import forms
from django.contrib.auth import get_user_model
from .models import Candidate

User = get_user_model()


class AddCandidateForm(forms.Form):
    """
    Form for hiring managers to add new candidates to the system
    """
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=255, required=True)
    source = forms.ChoiceField(choices=Candidate.SOURCE_CHOICES, required=True)
    source_ranking = forms.IntegerField(min_value=0, max_value=10, required=False, initial=0)
    years_of_experience = forms.IntegerField(min_value=0, required=False, initial=0)
    skills = forms.CharField(widget=forms.Textarea, required=False)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

# Add to core/forms.py

from django import forms
from django.contrib.auth import get_user_model
from .models import Candidate

class CandidateForm(forms.ModelForm):
    """Form for editing Candidate model fields"""
    class Meta:
        model = Candidate
        fields = ['skills', 'resume_url', 'interview_status', 'interview_notes']
        widgets = {
            'interview_notes': forms.Textarea(attrs={'rows': 4}),
        }

class UserForm(forms.ModelForm):
    """Form for editing User model fields associated with a Candidate"""
    class Meta:
        model = get_user_model()
        fields = ['email', 'full_name']