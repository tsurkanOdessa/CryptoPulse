"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

from django.contrib.auth.views import LoginView
from crypto_pulse.controllers.home_page_controller import home_page_view, portfolio_api


def debug_urls(request):
    from django.urls import get_resolver
    urls = []
    for url_pattern in get_resolver().url_patterns:
        urls.append(str(url_pattern.pattern))
    return HttpResponse("<br>".join(urls))


urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Grappelli
    path('grappelli/', include('grappelli.urls')),

    # Кастомные URL
    path('', home_page_view, name='home'),
    path('api/portfolio/', portfolio_api, name='portfolio_api'),

    # Перенаправления для совместимости
    #path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True)),
    #path('accounts/logout/', RedirectView.as_view(url='/logout/', permanent=True)),
    path('login/', LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', LoginView.as_view(template_name='auth/logout.html'), name='logout'),
    # Allauth URLs
    #path('', include('allauth.urls')),

]
