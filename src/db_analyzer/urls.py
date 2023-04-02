"""db_analyzer URL Configuration

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
from django.urls import path
from .view import schedual

urlpatterns = [
    path('', schedual.index),
    path('schedual/', schedual.sched_idx),
    path('schedual/add/', schedual.sched_add),
    path('schedual/del/', schedual.sched_del),
    path('schedual/search/', schedual.sched_search),
    path('schedual/resume_stop/', schedual.sched_resume_stop),
    path('schedual/go_run/', schedual.sched_go_run),
    path('schedual/cron_reset/', schedual.sched_cron_reset),
]
