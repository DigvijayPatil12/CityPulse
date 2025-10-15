# core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.generic.edit import CreateView # <--- NEW IMPORT
from django.urls import reverse_lazy           # <--- NEW IMPORT
from .forms import CustomUserCreationForm

# This is the view for the home page.
# @login_required forces non-logged-in users to the LOGIN_URL (which is '/login/')
@login_required 
def home_page(request):
    # This assumes you create a simple core/home.html template
    return render(request, 'core/home.html', {'user': request.user})

@login_required 
def report_issue(request):
    # This renders the new report_issue.html template
    return render(request, 'core/report_issue.html', {}) 

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    # Redirect to the login page (name 'login') on successful sign-up
    success_url = reverse_lazy('login') 
    template_name = 'core/signup.html'  