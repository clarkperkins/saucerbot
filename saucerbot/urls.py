# -*- coding: utf-8 -*-
"""
saucerbot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", include("saucerbot.core.urls", namespace="core")),
    path("", include("saucerbot.discord.urls", namespace="discord")),
    path("", include("saucerbot.groupme.urls", namespace="groupme")),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="core:api-root")),
]
