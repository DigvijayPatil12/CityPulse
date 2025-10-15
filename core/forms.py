# core/forms.py

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import get_user_model

# Get the active User model (usually django.contrib.auth.models.User)
User = get_user_model() 

class CustomUserCreationForm(UserCreationForm):
    # Add fields for first_name and last_name
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')

    class Meta:
        # UserCreationForm.Meta is not used here, we define everything explicitly
        model = User
        # Include all necessary fields: username, first_name, last_name, and the two password fields (from UserCreationForm)
        fields = ('username', 'first_name', 'last_name') 
        
    def save(self, commit=True):
        # Override save to ensure first_name and last_name are saved correctly
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # Call the default UserCreationForm save logic to handle password hashing
        if commit:
            user.save()
        return user