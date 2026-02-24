from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    # Documents
    path('documents/', views.document_list, name='document_list'),
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/classify/', views.document_classify, name='document_classify'),
    path('documents/<int:pk>/assign/', views.document_assign, name='document_assign'),
    path('documents/<int:pk>/process/', views.document_process, name='document_process'),
    path('documents/<int:pk>/review/', views.document_review, name='document_review'),
    path('documents/<int:pk>/esign/', views.document_esign, name='document_esign'),
    path('documents/<int:pk>/route/', views.document_route_decision, name='document_route_decision'),
    path('documents/<int:pk>/notify/', views.document_notify, name='document_notify'),
    # Admin
    path('admin-panel/users/', views.manage_users, name='manage_users'),
    path('admin-panel/users/<int:pk>/role/', views.assign_role, name='assign_role'),
    path('admin-panel/departments/', views.manage_departments, name='manage_departments'),
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/count/', views.notifications_count, name='notifications_count'),
]
