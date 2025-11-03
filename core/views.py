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
# 2. USER HOME PAGE VIEW (UNCHANGED)
# ----------------------------------------------------------------------
@login_required 
def home_page(request):
    return render(request, 'core/home.html', {'user': request.user})


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
# 5. OTHER VIEWS (UPDATED: user_profile, user_update_issue_status, user_delete_issue)
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


@require_POST
@login_required
def user_update_issue_status(request, issue_id):
    # CRUCIAL: Check ownership
    issue = get_object_or_404(IssueReport, id=issue_id, reporter=request.user) 
    new_status = request.POST.get('status')
    
    # User can only change status to 'Reported' or 'In Progress'. 
    # This allows a user to "dispute" a 'Resolved' status by setting it back to 'Reported'.
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
    
    # LOGIC UPDATE: Allow user to delete ANY issue they posted, regardless of status.
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


def issue_data_api(request):
    try:
        issues = IssueReport.objects.all()

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
        
        return JsonResponse(data_points, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def recent_issues_api(request):
    try:
        recent_issues = IssueReport.objects.select_related('reporter') \
                                           .order_by('-reported_at')[:15]

        data_list = []
        for issue in recent_issues:
            detail_url = '#' 
            try:
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

@login_required
def issue_detail_view(request, pk):
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
        
    except Exception as e:
        messages.error(request, f"Error loading issue: {e}")
        return redirect('home')
    
    return render(request, 'core/issue_detail.html', context)