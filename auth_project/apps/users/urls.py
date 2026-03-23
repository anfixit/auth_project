from django.urls import path

from apps.users.views import (
    delete_account_view,
    profile_view,
    register_view,
    update_profile_view,
)

urlpatterns = [
    path("register/", register_view, name="user-register"),
    path("me/", profile_view, name="user-profile"),
    path(
        "me/update/",
        update_profile_view,
        name="user-update",
    ),
    path(
        "me/delete/",
        delete_account_view,
        name="user-delete",
    ),
]
