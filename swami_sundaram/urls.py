"""swami_sundaram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from home import views as home_views


urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('', include('home.urls')),
    path('register/', user_views.register, name="register"),
    path('activate/<uidb64>/<token>/', user_views.activate_account, name="activate_account"),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name="login"),
    path('logout/', user_views.logout_view, name="logout"),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'), name="password_reset"),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),name="password_reset_done"),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),name="password_reset_confirm"),
     path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name="password_reset_complete"),
    path('profile/', user_views.profile, name="profile"),
    path('profile_update/', user_views.profile_update, name="profile-update"),
    path('profile/favourites/', user_views.favourite_list, name="favourite_list"),
    path('fav/<int:id>/', home_views.favourite_add, name="favourite-add")
    ,
    path('admin-menu/', user_views.admin_menu, name='admin_menu'),
    path('admin-menu/songs/', user_views.mod_songs_list, name='mod_songs_list'),
    path('admin-menu/songs/create/', user_views.mod_song_create, name='mod_song_create'),
    path('admin-menu/songs/<int:pk>/edit/', user_views.mod_song_edit, name='mod_song_edit'),
    path('admin-menu/songs/<int:pk>/delete/', user_views.mod_song_delete, name='mod_song_delete'),
    path('admin-menu/reviews/', user_views.mod_reviews_list, name='mod_reviews_list'),
    path('admin-menu/reviews/create/', user_views.mod_review_create, name='mod_review_create'),
    path('admin-menu/reviews/<int:pk>/delete/', user_views.mod_review_delete, name='mod_review_delete'),
    path('admin-menu/contacts/', user_views.mod_contacts_list, name='mod_contacts_list'),
    path('admin-menu/contacts/<int:pk>/mark_replied/', user_views.mod_contact_mark_replied, name='mod_contact_mark_replied'),
    path('admin-menu/users/', user_views.mod_users_list, name='mod_users_list'),
    path('admin-menu/users/<int:pk>/edit/', user_views.mod_user_edit, name='mod_user_edit'),
    path('admin-menu/users/<int:pk>/toggle/', user_views.mod_user_toggle_active, name='mod_user_toggle_active'),
]

handler404 = 'home.views.error_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
