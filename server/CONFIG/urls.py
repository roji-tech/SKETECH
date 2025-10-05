from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# from djoser.views import UserViewSet


# router = routers.DefaultRouter()
# router.register("api/v1/auth/users/", UserViewSet)


urlpatterns = [
    path("djangoadmin/", admin.site.urls),

    path("api/v1/auth/", include("djoser.urls")),

    path("", include("main.urls")),
    # path("library/", include("library.urls")),
    # path("myquiz/", include("myquiz.urls")),
    # path("report/", include("report.urls")),
    path("api/v1/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
