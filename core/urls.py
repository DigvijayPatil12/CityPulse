# core/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  

urlpatterns = [
    # 1. ROOT/HOME Page
    path('', views.home_page, name='home'), 
    
    # 2. Login Page URL
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),

    # 3. Logout URL
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 4. Signup URL
    path('signup/', views.SignUpView.as_view(), name='signup'), 

    # 5 Report issue( Mridul)
    path('report/', views.report_issue, name='report_issue'), 

    # heatmap page
    # path('heatmap/', views.heatmap_view, name='heatmap'),
]