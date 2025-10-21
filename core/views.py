# core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.views.generic.edit import CreateView 
from django.urls import reverse_lazy           
from django.contrib.auth.views import LoginView
from django.contrib.auth import login 
from django.contrib import messages             
from .forms import CustomUserCreationForm 

# === NEW IMPORTS FOR DATABASE HANDLING ===
from .models import IssueReport, IssueImage
from django.http import JsonResponse # For our new API view
from decimal import Decimal, InvalidOperation # To correctly handle DecimalFields
# =======================================

# ----------------------------------------------------------------------
# 1. CONSOLIDATED LOGIN VIEW (Handles both user and admin)
# ----------------------------------------------------------------------
class LoginView(LoginView):
    template_name = 'core/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login_role = self.request.POST.get('login_role', 'user')

        if login_role == 'admin':
            if user.is_staff:
                login(self.request, user) 
                return redirect('admin_home')
            else:
                error_message = "Invalid credentials or lack of administrative privileges."
                form.add_error(None, error_message)
                return self.form_invalid(form)
        
        else: # login_role == 'user'
            login(self.request, user)
            return redirect('home')

# ----------------------------------------------------------------------
# 2. USER HOME PAGE VIEW
# ----------------------------------------------------------------------
@login_required 
def home_page(request):
    return render(request, 'core/home.html', {'user': request.user})


# ----------------------------------------------------------------------
# 3. ADMIN HOME PAGE VIEW
# ----------------------------------------------------------------------
@login_required
def admin_home_page(request):
    if not request.user.is_staff:
        return redirect('home') 
        
    return render(request, 'core/admin_home.html', {'user': request.user})


# ----------------------------------------------------------------------
# 4. REPORT ISSUE VIEW (UPDATED to handle POST and database storage)
# ----------------------------------------------------------------------
@login_required 
def report_issue_view(request):
    if request.method == 'POST':
        # 1. Extract and validate required data from the POST request
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if not all([issue_type, description, latitude, longitude]):
            messages.error(request, 'Missing required fields for issue type, location, or description.')
            # Re-render the form on error
            return render(request, 'core/report_issue.html')

        try:
            # 2. Save the main IssueReport object
            #    UPDATED: Use Decimal() for coordinates
            new_issue = IssueReport.objects.create(
                reporter=request.user, 
                issue_type=issue_type,
                sub_category=request.POST.get('sub_category'), # Optional
                latitude=Decimal(latitude.strip()),
                longitude=Decimal(longitude.strip()),
                description=description,
            )
            
            # 3. Handle image uploads (up to 3 files)
            images = request.FILES.getlist('issue_images')
            for image_file in images:
                if len(new_issue.images.all()) < 3: # Server-side max limit
                    IssueImage.objects.create(issue=new_issue, image=image_file)

            # 4. Success message and redirect
            messages.success(request, 'Your issue has been successfully reported!')
            return redirect('home') # Redirect to home or a success page

        except (ValueError, InvalidOperation):
            # Handle cases where latitude/longitude conversion fails
            messages.error(request, 'Invalid location coordinates submitted.')
        except Exception as e:
            # General error handling
            messages.error(request, f'An unexpected server error occurred: {e}')

        # Fallback to re-render the form with error messages
        return render(request, 'core/report_issue.html')

    # For GET requests (display the form)
    return render(request, 'core/report_issue.html') 
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
# 5. OTHER VIEWS
# ----------------------------------------------------------------------
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') 
    template_name = 'core/signup.html'

# ----------------------------------------------------------------------
# 6. USER PROFILE VIEW
# ----------------------------------------------------------------------
@login_required
def user_profile(request):
    """
    Displays the user's profile page with their stats and activity.
    Now, we can fetch the user's reported issues.
    """
    # Fetch issues reported by the current user
    reported_issues = IssueReport.objects.filter(reporter=request.user).order_by('-reported_at')
    
    context = {
        'reported_issues': reported_issues
    }
    
    return render(request, 'core/profile.html', context)

# ----------------------------------------------------------------------
# 7. ADMIN/STAFF VIEWS
# ----------------------------------------------------------------------
def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user) # Only staff users can access this page
def all_issues_list(request):
    """
    Retrieves all reported issues for display on a staff-only dashboard.
    """
    issues = IssueReport.objects.select_related('reporter').order_by('-reported_at')
    
    context = {
        'issues': issues
    }
    return render(request, 'core/issue_list.html', context)


# ----------------------------------------------------------------------
# 8. --- NEW API VIEW FOR HEATMAP ---
# ----------------------------------------------------------------------
def issue_data_api(request):
    """
    This is the API endpoint that provides heatmap data to Leaflet.
    It's filterable by issue_type.
    """
    try:
        # Get the list of selected issue types from the query parameters
        # e.g., /api/issue-data/?types[]=pothole&types[]=crime
        selected_types = request.GET.getlist('types[]')

        issues = IssueReport.objects.all()

        # If any types are selected, filter the queryset
        if selected_types:
            issues = issues.filter(issue_type__in=selected_types)

        # Format the data into the [lat, lng, intensity]
        # list that Leaflet.heat expects.
        # Note: We must cast Decimals to float for JSON serialization
        data_points = [
            [float(issue.latitude), float(issue.longitude), float(issue.intensity)]
            for issue in issues
        ]
        
        # Return the data as a JSON response
        return JsonResponse(data_points, safe=False)
        
    except Exception as e:
        # Return an error message if something goes wrong
        return JsonResponse({'error': str(e)}, status=500)