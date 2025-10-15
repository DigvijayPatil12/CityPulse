# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    # 1. USER HOME Page (Default destination after user login)
    path('', views.home_page, name='home'), 
    
    # 2. CONSOLIDATED LOGIN VIEW (Handles both user and admin paths)
    # The view will be renamed to just LoginView
    path('login/', views.LoginView.as_view(), name='login'), 
    
    # 💥 REMOVE THIS LINE: path('admin/login/', views.AdminLoginView.as_view(), name='admin_login'), 💥

    # 3. Logout URL
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 4. Signup URL
    path('signup/', views.SignUpView.as_view(), name='signup'), 

    # 5. Report issue
    path('report/', views.report_issue_view, name='report_issue'), 
    
    # 6. ADMIN HOME PAGE (Target for Admin login)
    path('admin/home/', views.admin_home_page, name='admin_home'),

     # 7. USER PROFILE PAGE (ADD THIS NEW LINE)
    path('profile/', views.user_profile, name='profile'),

]