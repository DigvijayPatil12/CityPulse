# core/urls.py (Final Version)

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    # 1. USER HOME Page
    path('', views.home_page, name='home'), 
    
    # 2. CONSOLIDATED LOGIN VIEW
    path('login/', views.LoginView.as_view(), name='login'), 
    
    # 3. Logout URL
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 4. Signup URL
    path('signup/', views.SignUpView.as_view(), name='signup'), 

    # 5. Report issue
    path('report/', views.report_issue_view, name='report_issue'), 
    
    # 6. ADMIN HOME PAGE
    path('admin/home/', views.admin_home_page, name='admin_home'),

    # 7. USER PROFILE PAGE
    path('profile/', views.user_profile, name='profile'),

    # 8. ALL ISSUES LIST PAGE (Staff Only) - PATH AND NAME UPDATED
    path('admin/issues/', views.all_issues_list, name='all_issues_list'),
    
    # 8b. NEW: Status Update URL
    path('admin/issues/<int:issue_id>/status/update/', views.update_issue_status, name='update_issue_status'),

    # --- API Endpoints ---
    path('api/issue-data/', views.issue_data_api, name='issue_data_api'),
    
    # 9. Recent Issues API
    path('api/recent-issues/', views.recent_issues_api, name='recent_issues_api'),

    # 10. Issue Detail Page
    path('issue/<int:pk>/', views.issue_detail_view, name='issue_detail'),

]