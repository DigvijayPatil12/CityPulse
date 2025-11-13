# core/views.py

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
from django.contrib.auth import get_user_model 
from django.views.decorators.http import require_POST
from django.db.models import F, Count
from django.db import transaction 

from .forms import CustomUserCreationForm 
from .models import IssueReport, IssueImage, ISSUE_TYPES, STATUS_CHOICES, STATUS_RESOLVED, STATUS_REPORTED, STATUS_IN_PROGRESS # Ensure all constants are imported
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging 

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# 1. CONSOLIDATED LOGIN VIEW (UNCHANGED)
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
        
        else:
            login(self.request, user)
            return redirect('home')

# ----------------------------------------------------------------------
# 2. HOME PAGE VIEW (UNCHANGED)
# ----------------------------------------------------------------------
@login_required 
def home_page(request):
    context = {
        'user': request.user,
        'issue_types_choices': ISSUE_TYPES, # Pass issue types
        'status_choices': STATUS_CHOICES, # Pass status choices
    }
    return render(request, 'core/home.html', context)



# ----------------------------------------------------------------------
# 3. ADMIN HOME PAGE VIEW (UNCHANGED)
# ----------------------------------------------------------------------
@login_required
def admin_home_page(request):
    if not request.user.is_staff:
        return redirect('home') 
        
    return render(request, 'core/admin_home.html', {'user': request.user})


# ----------------------------------------------------------------------
# 4. REPORT ISSUE VIEW (UNCHANGED)
# ----------------------------------------------------------------------
@login_required 
def report_issue_view(request):
    if request.method == 'POST':
        # Retrieve all form data
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        sub_category = request.POST.get('sub_category') 
        
        # --- SERVER-SIDE VALIDATION ---
        if not all([issue_type, description, latitude, longitude]):
            return JsonResponse({
                'success': False, 
                'message': 'Missing required fields for issue type, location, or description.'
            }, status=400) 
            
        if issue_type == 'other' and not sub_category:
            return JsonResponse({
                'success': False, 
                'message': 'Please specify the issue in the text box for "Other" issue type.'
            }, status=400)
            
        try:
            # Type conversion and validation
            lat_decimal = Decimal(latitude.strip()).quantize(Decimal('0.000001'))
            lon_decimal = Decimal(longitude.strip()).quantize(Decimal('0.000001'))

            with transaction.atomic():
                # 1. Create the IssueReport object
                new_issue = IssueReport.objects.create(
                    reporter=request.user, 
                    issue_type=issue_type,
                    sub_category=sub_category if sub_category else None,
                    latitude=lat_decimal,
                    longitude=lon_decimal,
                    description=description,
                )
                
                # 2. Calculate and Save Sentiment/Intensity
                analyzer = SentimentIntensityAnalyzer()
                sentiment_scores = analyzer.polarity_scores(description)
                compound_score = sentiment_scores['compound']
                intensity_value = (1.0 - compound_score) / 2.0 
                new_issue.intensity = Decimal.from_float(intensity_value).quantize(Decimal('0.01'))
                new_issue.save()

                # 3. Handle Images
                images = request.FILES.getlist('issue_images') 
                if images:
                    for image_file in images[:3]: 
                        try:
                            IssueImage.objects.create(
                                issue=new_issue, 
                                image=image_file
                            )
                        except Exception as file_error:
                            logger.error(f"File Save Error for {image_file.name}: {file_error}", exc_info=True)
                            messages.warning(request, f"Report saved, but image '{image_file.name}' could not be uploaded.")

            # --- SUCCESS RESPONSE (REDIRECT) ---
            messages.success(request, 'Your issue has been successfully reported!')
            return redirect('home') 

        except (ValueError, InvalidOperation):
            return JsonResponse({
                'success': False, 
                'message': 'Invalid location coordinates submitted. Please check the map.'
            }, status=400)
        except Exception as e:
            logger.error(f"Unexpected server error during report submission: {e}", exc_info=True)
            return JsonResponse({
                'success': False, 
                'message': 'An unexpected server error occurred. Please try again.'
            }, status=500)

    # Handle GET request: simply render the template
    return render(request, 'core/report_issue.html')

# ----------------------------------------------------------------------
# 5. OTHER VIEWS (UNCHANGED)
# ----------------------------------------------------------------------
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login') 
    template_name = 'core/signup.html'

@login_required
def user_profile(request):
    reported_issues = IssueReport.objects.filter(reporter=request.user).order_by('-reported_at')
    
    # --- Calculate User Stats ---
    total_reports = reported_issues.count()
    resolved_issues = reported_issues.filter(status=STATUS_RESOLVED).count()
    reputation_score = resolved_issues * 10 + (total_reports - resolved_issues) * 2 

    context = {
        'reported_issues': reported_issues,
        'total_reports': total_reports,         
        'resolved_issues': resolved_issues,     
        'reputation_score': reputation_score,   
        'STATUS_CHOICES': STATUS_CHOICES,       
    }
    return render(request, 'core/profile.html', context)

# ======================================================================
# 6. RECENT COMPLAINTS LIST (MODIFIED)
# ======================================================================
@login_required
def recent_complaints_list(request):
    """
    Shows a list of all recent issues reported by all users, with filtering.
    """
    # Get filter parameters from the URL
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('issue_type')

    # Start with the base queryset
    all_issues = IssueReport.objects.select_related('reporter').all()

    # Apply filters if they exist and are not empty
    if status_filter:
        all_issues = all_issues.filter(status=status_filter)
    
    if type_filter:
        all_issues = all_issues.filter(issue_type=type_filter)

    # Order by newest first
    all_issues = all_issues.order_by('-reported_at')

    context = {
        'issues': all_issues,
        'user': request.user,
        'STATUS_CHOICES': STATUS_CHOICES,  # Pass choices for the dropdown
        'ISSUE_TYPES': ISSUE_TYPES,      # Pass choices for the dropdown
        'selected_status': status_filter,  # Pass back the selected value
        'selected_type': type_filter,      # Pass back the selected value
    }
    return render(request, 'core/recent_complaints.html', context)
# ======================================================================


@require_POST
@login_required
def user_update_issue_status(request, issue_id):
    # CRUCIAL: Check ownership
    issue = get_object_or_404(IssueReport, id=issue_id, reporter=request.user) 
    new_status = request.POST.get('status')
    
    # User can only change status to 'Reported' or 'In Progress'. 
    valid_user_statuses = [STATUS_REPORTED, STATUS_IN_PROGRESS]

    if new_status and new_status in valid_user_statuses:
        if issue.status != new_status:
            issue.status = new_status
            issue.save()
            messages.success(request, f'Issue #{issue.id} status updated to {issue.get_status_display()}.')
        else:
            messages.info(request, f'Issue #{issue.id} status is already {issue.get_status_display()}.')
    else:
        messages.error(request, 'Invalid status or missing data.')
        
    redirect_url = request.META.get('HTTP_REFERER', reverse('profile'))
    return redirect(redirect_url)

@require_POST
@login_required
def user_delete_issue(request, issue_id):
    # CRUCIAL: Check ownership
    issue = get_object_or_404(IssueReport, id=issue_id, reporter=request.user) 
    
    try:
        issue.delete()
        messages.success(request, f'Issue #{issue.id} successfully deleted.')
    except Exception as e:
        logger.error(f"Error deleting issue {issue_id}: {e}", exc_info=True)
        messages.error(request, 'An unexpected error occurred during deletion.')
        
    redirect_url = reverse('profile')
    return redirect(redirect_url)


def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def all_issues_list(request):
    issues = IssueReport.objects.select_related('reporter').all()
    
    issue_type = request.GET.get('issue_type')
    if issue_type:
        issues = issues.filter(issue_type=issue_type)

    status = request.GET.get('status')
    if status:
        issues = issues.filter(status=status)

    sort_by = request.GET.get('sort')
    if sort_by == 'intensity_desc':
        issues = issues.order_by(F('intensity').desc(nulls_last=True)) 
    else:
        issues = issues.order_by('-reported_at')
        
    context = {
        'issues': issues,
        'issue_types': ISSUE_TYPES,      
        'status_choices': STATUS_CHOICES, 
    }
    return render(request, 'core/issue_list.html', context)


@require_POST
@login_required
@user_passes_test(is_staff_user) 
def update_issue_status(request, issue_id):
    issue = get_object_or_404(IssueReport, id=issue_id)
    new_status = request.POST.get('status')
    valid_statuses = [c[0] for c in STATUS_CHOICES] 
    
    if new_status and new_status in valid_statuses:
        if issue.status != new_status:
            issue.status = new_status
            issue.save()
            messages.success(request, f'Issue #{issue.id} status updated to {new_status}.')
        else:
            messages.info(request, f'Issue #{issue.id} status is already {new_status}.')
    else:
        messages.error(request, 'Invalid status or missing data.')
        
    redirect_url = request.META.get('HTTP_REFERER', reverse('all_issues_list'))
    return redirect(redirect_url)


# ----------------------------------------------------------------------
# 7. API VIEW (UNCHANGED)
# ----------------------------------------------------------------------
def issue_data_api(request):
    try:
        issues = IssueReport.objects.all()
        status_filters = request.GET.getlist('status')
        type_filters = request.GET.getlist('type')

        if status_filters:
            issues = issues.filter(status__in=status_filters)
        if type_filters:
            issues = issues.filter(issue_type__in=type_filters)

        data_points = [
            {
                "lat": float(issue.latitude), 
                "lon": float(issue.longitude), 
                "intensity": float(issue.intensity),
                "type": issue.issue_type,
                "description": issue.description,
                "status": issue.status 
            }
            for issue in issues
        ]
        
        logger.info(f"Returning {len(data_points)} filtered issues for API request.")
        return JsonResponse(data_points, safe=False)
        
    except Exception as e:
        logger.error(f"Error in issue_data_api: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)



# ----------------------------------------------------------------------
# 8. API VIEW (UNCHANGED)
# ----------------------------------------------------------------------
@login_required
def api_issue_detail(request, issue_id):
    try:
        # Pre-fetch related data for efficiency
        issue = get_object_or_404(IssueReport.objects.select_related('reporter'), id=issue_id)
        
        # Get a list of all image URLs for this issue
        images = [img.image.url for img in issue.images.all()]

        # Prepare the data
        data = {
            'id': issue.id,
            'issue_type': issue.get_issue_type_display(),
            'description': issue.description,
            'status': issue.get_status_display(),
            'reported_by': issue.reporter.get_full_name() or issue.reporter.username,
            'reported_at': issue.reported_at.strftime('%b %d, %Y, %I:%M %p'),
            'latitude': float(issue.latitude),
            'longitude': float(issue.longitude),
            'images': images,
        }
        
        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error fetching API issue detail for {issue_id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Failed to load issue details.'}, status=500)


# ----------------------------------------------------------------------
# 9. ISSUE DETAIL VIEW (MODIFIED FOR BETTER DEBUGGING)
# ----------------------------------------------------------------------
@login_required
def issue_detail_view(request, pk):
    # This is the view that was causing the redirect.
    # I've made the 'except' block more specific so you can
    # debug the real error in your logs if you want to.
    try:
        issue = get_object_or_404(IssueReport, pk=pk)
        images = issue.images.all()
        comments = [] 
        
        context = {
            'issue': issue,
            'images': images,
            'comments': comments,
        }
        
        return render(request, 'core/issue_detail.html', context)
    
    # get_object_or_404 raises Http404, not DoesNotExist
    except Http404:
        messages.error(request, "The issue you are looking for does not exist.")
        return redirect('home')
    # This error happens if 'core/issue_detail.html' is missing
    except TemplateDoesNotExist:
        logger.error(f"Template 'core/issue_detail.html' not found.", exc_info=True)
        messages.error(request, "There was a problem loading the page. The template is missing.")
        return redirect('home')
    # This catches other errors (e.g., template syntax error)
    except Exception as e:
        logger.error(f"Error loading issue detail {pk}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred while loading the issue.")
        return redirect('home')