"""
URL configuration for tasks app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Task Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/generate/', views.template_generate, name='template_generate'),

    # Auto-complete Rules
    path('autocomplete/', views.autocomplete_list, name='autocomplete_list'),
    path('autocomplete/create/', views.autocomplete_create, name='autocomplete_create'),

    # Task Watchers
    path('watchers/add/', views.watcher_add, name='watcher_add'),
    path('watchers/<int:watcher_id>/remove/', views.watcher_remove, name='watcher_remove'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),

    # Task Actions
    path('tasks/<str:task_id>/complete/', views.task_complete, name='task_complete'),
]
