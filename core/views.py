# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.generic.edit import CreateView 
from django.urls import reverse_lazy           
from django.contrib.auth.views import LoginView
from django.contrib.auth import login # Import the login function
from django.contrib import messages             
from .forms import CustomUserCreationForm 


# ----------------------------------------------------------------------
# 1. CONSOLIDATED LOGIN VIEW (Handles both user and admin)
# ----------------------------------------------------------------------
# Renamed from UserLoginView
class LoginView(LoginView):
    template_name = 'core/login.html'
    # success_url is no longer needed here, we handle redirect manually

    def form_valid(self, form):
        # 1. Get the authenticated user
        user = form.get_user()
        
        # 2. Determine the intended role from the hidden input field
        login_role = self.request.POST.get('login_role', 'user')

        # 3. Handle Admin Login flow
        if login_role == 'admin':
            if user.is_staff:
                # Log the user in
                login(self.request, user) 
                # Redirect to admin home
                return redirect('admin_home')
            else:
                # If not staff, add a non-field error and return to the form
                error_message = "Invalid credentials or lack of administrative privileges."
                form.add_error(None, error_message)
                return self.form_invalid(form)
        
        # 4. Handle Standard User Login flow ('user' role)
        else: # login_role == 'user'
            # The base LoginView handles the login and sets the default success_url
            # to settings.LOGIN_REDIRECT_URL if no 'next' param exists.
            # However, since we defined 'home' in urls.py, we redirect manually for clarity.
            login(self.request, user)
            return redirect('home')

# ----------------------------------------------------------------------
# 2. REMOVE AdminLoginView 💥
# ----------------------------------------------------------------------
# ... (Remove the AdminLoginView class entirely) ...

# ----------------------------------------------------------------------
# 3. USER HOME PAGE VIEW
# ----------------------------------------------------------------------
@login_required 
def home_page(request):
    # This is the view for the home page (/).
    return render(request, 'core/home.html', {'user': request.user})


# ----------------------------------------------------------------------
# 4. ADMIN HOME PAGE VIEW (Must still protect against unauthorized access)
# ----------------------------------------------------------------------
# ... (This remains unchanged) ...
@login_required
def admin_home_page(request):
    # Security check: only allow access if the user is staff
    if not request.user.is_staff:
        # Redirect non-admins back to the user home
        return redirect('home') 
        
    return render(request, 'core/admin_home.html', {'user': request.user})


# ----------------------------------------------------------------------
# 5. OTHER VIEWS (Unchanged)
# ----------------------------------------------------------------------
# ... (report_issue_view and SignUpView remain unchanged) ...
@login_required 
def report_issue_view(request):
    return render(request, 'core/report_issue.html', {}) 

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') 
    template_name = 'core/signup.html'

# ======================================================================
# 6. USER PROFILE VIEW (NEW - Add this entire function)
# ======================================================================
@login_required
def user_profile(request):
    """
    Displays the user's profile page with their stats and activity.
    """
    # This is where you will later add logic to fetch the user's reported issues
    # from the database. For now, it just shows the page.
    # Example logic to add later:
    # reported_issues = Issue.objects.filter(reporter=request.user)
    # context = {'reported_issues': reported_issues}
    
    return render(request, 'core/profile.html', {}) # The context is empty for now