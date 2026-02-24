from django import forms
from .models import User, Document, Department, DocumentRouting


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'password2']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in ['username', 'first_name', 'last_name', 'email']}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'department']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }


class DocumentCreateForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'source', 'description', 'correspondent_name', 'correspondent_agency', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'correspondent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'correspondent_agency': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DocumentClassifyForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['classification']
        widgets = {'classification': forms.Select(attrs={'class': 'form-select'})}


class DocumentAssignForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['assigned_to']
        widgets = {'assigned_to': forms.Select(attrs={'class': 'form-select'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['dept_sender_receiver', 'executive']
        )


class DocumentReviewForm(forms.Form):
    DECISION_CHOICES = [('approve', 'Approve'), ('reject', 'Return for Revision')]
    decision = forms.ChoiceField(choices=DECISION_CHOICES, widget=forms.RadioSelect())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))


class DocumentRoutingForm(forms.ModelForm):
    class Meta:
        model = DocumentRouting
        fields = ['to_department', 'notes']
        widgets = {
            'to_department': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DocumentSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'}))
    status = forms.ChoiceField(required=False, choices=[('', 'All Statuses')] + Document.STATUS_CHOICES,
                               widget=forms.Select(attrs={'class': 'form-select'}))
    source = forms.ChoiceField(required=False, choices=[('', 'All Sources')] + Document.SOURCE_CHOICES,
                               widget=forms.Select(attrs={'class': 'form-select'}))
