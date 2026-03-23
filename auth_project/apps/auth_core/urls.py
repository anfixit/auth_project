from django.urls import path

from apps.auth_core.views import (
    login_view,
    logout_view,
    refresh_view,
)

urlpatterns = [
    path('login/', login_view, name='auth-login'),
    path('logout/', logout_view, name='auth-logout'),
    path('refresh/', refresh_view, name='auth-refresh'),
]
