from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.views.generic.edit import CreateView 
from django.urls import reverse_lazy, reverse          
from django.contrib.auth.views import LoginView
from django.contrib.auth import login 
from django.contrib import messages             
from django.http import JsonResponse 
from decimal import Decimal, InvalidOperation
from django.db.models.functions import TruncSecond 
from django.contrib.auth import get_user_model # Ensure this is always imported if used



from .forms import CustomUserCreationForm 
from .models import IssueReport, IssueImage #, Comment # Assuming Comment model exists for detail view
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging # 🚨 NEW: Use Python's logging for server errors

# Set up logging for better error tracking
logger = logging.getLogger(__name__)

# User = get_user_model() # This is only needed in models.py, can be removed if not used here

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
# 4. REPORT ISSUE VIEW (UPDATED with CRITICAL Error Handling)
# ----------------------------------------------------------------------
@login_required 
def report_issue_view(request):
    if request.method == 'POST':
        # 1. Extract and validate required data from the POST request
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        sub_category = request.POST.get('sub_category')
        
        if not all([issue_type, description, latitude, longitude]):
            messages.error(request, 'Missing required fields for issue type, location, or description.')
            return render(request, 'core/report_issue.html')

        try:
            # Type conversion and validation
            lat_decimal = Decimal(latitude.strip()).quantize(Decimal('0.000001'))
            lon_decimal = Decimal(longitude.strip()).quantize(Decimal('0.000001'))

            # 2. Save the main IssueReport object
            new_issue = IssueReport.objects.create(
                reporter=request.user, 
                issue_type=issue_type,
                sub_category=sub_category if sub_category else None,
                latitude=lat_decimal,
                longitude=lon_decimal,
                description=description,
            )
            
            # --- 3. SEMANTIC ANALYSIS & INTENSITY CALCULATION ---
            analyzer = SentimentIntensityAnalyzer()
            sentiment_scores = analyzer.polarity_scores(description)
            compound_score = sentiment_scores['compound']
            
            # Map score [-1.0, 1.0] to intensity [1.0, 0.0]
            intensity_value = (1.0 - compound_score) / 2.0
            
            # 4. Save the new intensity
            new_issue.intensity = Decimal.from_float(intensity_value).quantize(Decimal('0.01'))
            new_issue.save()
            # ---------------------------------------------------

            # 5. Handle image uploads (up to 3 files)
            images = request.FILES.getlist('issue_images') 
            
            if images:
                for image_file in images[:3]: 
                    try:
                        # Attempt to create the IssueImage object, which saves the file to disk
                        IssueImage.objects.create(
                            issue=new_issue, 
                            image=image_file
                        )
                    except Exception as file_error:
                        # 🚨 CRITICAL ERROR LOGGING ADDED HERE 🚨
                        # Log the error and print a message to the console to help debug
                        logger.error(f"File Save Error for {image_file.name}: {file_error}", exc_info=True)
                        print(f"\n🚨 FILE SAVE FAILED: Check your terminal for detailed traceback. Error: {file_error}\n")
                        messages.warning(request, f"Report saved, but image '{image_file.name}' could not be uploaded.")


            # 6. Success message and redirect
            messages.success(request, 'Your issue has been successfully reported!')
            return redirect('home') 

        except (ValueError, InvalidOperation):
            # Handle cases where latitude/longitude conversion fails
            messages.error(request, 'Invalid location coordinates submitted.')
        except Exception as e:
            # General error handling
            logger.error(f"Unexpected server error during report submission: {e}", exc_info=True)
            messages.error(request, 'An unexpected server error occurred. Please try again.')

        # Fallback to re-render the form with error messages
        return render(request, 'core/report_issue.html')

    # For GET requests (display the form)
    return render(request, 'core/report_issue.html')
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
    """
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
# 8. --- API VIEW FOR HEATMAP ---
# ----------------------------------------------------------------------
def issue_data_api(request):
    """
    This is the API endpoint that provides heatmap data to Leaflet.
    """
    try:
        selected_types = request.GET.getlist('types[]')

        issues = IssueReport.objects.all()

        if selected_types:
            issues = issues.filter(issue_type__in=selected_types)

        data_points = [
            [float(issue.latitude), float(issue.longitude), float(issue.intensity)]
            for issue in issues
        ]
        
        return JsonResponse(data_points, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ----------------------------------------------------------------------
# 9. --- NEW API VIEW FOR RECENT COMPLAINTS ---
# ----------------------------------------------------------------------
@login_required
def recent_issues_api(request):
    """
    This API endpoint provides data for the 'Recent Complaints' list.
    """
    try:
        recent_issues = IssueReport.objects.select_related('reporter') \
                                           .order_by('-reported_at')[:15]

        data_list = []
        for issue in recent_issues:
            detail_url = '#' # Placeholder
            try:
                # Assuming 'issue_detail' URL name exists
                detail_url = reverse('issue_detail', args=[issue.id])
            except:
                pass 

            data_list.append({
                'id': issue.id,
                'reporter_username': issue.reporter.username,
                'issue_type': issue.get_issue_type_display(), 
                'latitude': float(issue.latitude),
                'longitude': float(issue.longitude),
                'description': issue.description,
                'reported_at': issue.reported_at.strftime('%b %d, %Y, %I:%M %p'),
                'detail_url': detail_url
            })
        
        return JsonResponse(data_list, safe=False)

    except Exception as e:
        logger.error(f"Error fetching recent issues: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to load recent issues.'}, status=500)

# ----------------------------------------------------------------------
# 10. --- NEW: ISSUE DETAIL PAGE VIEW ---
# ----------------------------------------------------------------------
@login_required
def issue_detail_view(request, pk):
    """
    Displays a single issue, its images, and its comments.
    'pk' is the primary key (the ID) of the issue.
    """
    try:
        # Get the specific issue report, or show a 404 page if it doesn't exist
        issue = get_object_or_404(IssueReport, pk=pk)
        
        # Get all related images and comments
        # These are 'reverse' lookups from our models.py
        images = issue.images.all()
        comments = issue.comments.order_by('created_at').all()
        
        context = {
            'issue': issue,
            'images': images,
            'comments': comments,
        }
        
        return render(request, 'core/issue_detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading issue: {e}")
        return redirect('home') # Send user home on a bad error
    
    return render(request, 'core/issue_detail.html', context)