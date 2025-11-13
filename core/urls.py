# core/urls.py

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

    # 7b. NEW: User Status Update URL
    path('profile/issue/<int:issue_id>/status/update/', views.user_update_issue_status, name='user_update_issue_status'),

    # 7c. NEW: User Delete Issue URL
    path('profile/issue/<int:issue_id>/delete/', views.user_delete_issue, name='user_delete_issue'),
    
    # 7d. <<< NEW URL FOR RECENT COMPLAINTS >>>
    path('complaints/', views.recent_complaints_list, name='recent_complaints_list'),
    
    # 8. ALL ISSUES LIST PAGE (Staff Only)
    path('admin/issues/', views.all_issues_list, name='all_issues_list'),
    
    # 8b. Status Update URL (Admin)
    path('admin/issues/<int:issue_id>/status/update/', views.update_issue_status, name='update_issue_status'),

    # --- API Endpoints ---
    path('api/issue-data/', views.issue_data_api, name='issue_data_api'),
  
    # --- NEW API ENDPOINT ---
    # 10. API for a single issue's details
    path('api/issue-detail/<int:issue_id>/', views.api_issue_detail, name='api_issue_detail'),


    # 11. Issue Detail Page
    path('issue/<int:pk>/', views.issue_detail_view, name='issue_detail'),

]