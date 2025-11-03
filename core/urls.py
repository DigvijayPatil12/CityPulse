# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    # 1. USER HOME Page (Default destination after user login)
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

    # 8. ALL ISSUES LIST PAGE (Staff Only)
    path('issues/', views.all_issues_list, name='all_issues'),

    # --- API Endpoints ---
    path('api/issue-data/', views.issue_data_api, name='issue_data_api'),
    
    # 9. --- THIS IS THE NEW LINE ---
    path('api/recent-issues/', views.recent_issues_api, name='recent_issues_api'),

    # 10. (Placeholder) Issue Detail Page
    # If you don't have this, the 'Recent Complaints' link won't work
    # We can create this page next if you want.
    # path('issue/<int:pk>/', views.issue_detail_view, name='issue_detail'),

    # 10. --- ADD THIS NEW LINE for the Detail Page ---
    path('issue/<int:pk>/', views.issue_detail_view, name='issue_detail'),

]