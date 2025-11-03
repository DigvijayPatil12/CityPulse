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
        # Include all necessary fields: username, first_name, last_name
        fields = ('username', 'first_name', 'last_name') 

    # 🚨 FIX 1: The save method MUST be defined inside the CustomUserCreationForm class, not after its Meta.
    # 🚨 FIX 2: Corrected logic to ensure it calls UserCreationForm's save method properly.
    def save(self, commit=True):
        # Call UserCreationForm's save logic first to create the user and hash the password
        user = super().save(commit=False)
        
        # Save the new fields (first_name, last_name)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user

# 🚨 FIX 3: Removed the incomplete CommentForm which was crashing the server.