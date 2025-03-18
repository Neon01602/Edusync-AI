from django.urls import path
from . import views


urlpatterns = [
    path('', views.main, name='base'),
    path('home/', views.home, name='home'),
    path('logout/', views.custom_logout, name='logout'),
    path("create_classroom/", views.create_classroom, name="create_classroom"),
    path("edit-class/<int:class_id>/", views.edit_classroom, name="edit_classroom"),
    path("join-class/<str:unique_code>/", views.join_classroom, name="join_classroom"),
    path("classrooms/", views.classroom_list, name="classroom_list"),
    path("get-user-classes/", views.get_user_classes, name="get_user_classes"),
    path("get-csrf-token/", views.get_csrf_token, name="get_csrf_token"),
    path("view-classroom/<str:class_code>/", views.view_classroom, name="view_classroom"), 
    path("delete-account/", views.delete_account, name="delete_account"),
    path('api/user-profile/', views.get_user_profile, name='get_user_profile'),
    path("join_class/", views.join_class, name="join_class"),
    path("get_joined_classes/", views.get_joined_classes, name="get_joined_classes"),
    path("leave-class/", views.leave_class, name="leave_class"),
    path('leave-class/<str:class_code>/', views.leave_class, name='leave_classroom'),
    path('classroom/<int:classroom_id>/add_work/', views.add_classwork, name='add_classwork'),
    path('classroom/<int:classroom_id>/view_work/', views.view_classwork, name='view_classwork'),
    path('api/get_class_students/<str:class_code>/', views.get_class_students, name='get_class_students'),
]


