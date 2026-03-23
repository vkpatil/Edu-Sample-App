from django.contrib import admin
from django.urls import include, path

from users.views import access_guide_view, dashboard_view, home_view

admin.site.site_header = "EduSys Administration"
admin.site.site_title = "EduSys Admin"
admin.site.index_title = "Platform Management"

urlpatterns = [
    path("", home_view, name="home"),
    path("access/", access_guide_view, name="access_guide"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("admin/", admin.site.urls),
    path("accounts/", include("users.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("school/", include("school.urls")),
]
