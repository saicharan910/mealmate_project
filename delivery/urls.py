from django.urls import path
from . import views

urlpatterns = [
    # Auth & General
    path('', views.index, name='index'),
    path('open_signup/', views.open_signup, name="open_signup"),
    path('open_signin/', views.open_signin, name="open_signin"),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Restaurant Management
    path('add_restaurant/', views.add_restaurant, name='add_restaurant'),
    path('open_add_restaurant/', views.open_add_restaurant, name='open_add_restaurant'),
    path('open_show_restaurant/', views.open_show_restaurant, name='open_show_restaurant'),
    path('open_update_restaurant/<int:restaurant_id>/', views.open_update_restaurant, name='open_update_restaurant'),
    path('update_restaurant/<int:restaurant_id>/', views.update_restaurant, name='update_restaurant'),
    path('delete_restaurant/<int:restaurant_id>/', views.delete_restaurant, name='delete_restaurant'),

    # Menu Management
    path('open_update_menu/<int:restaurant_id>/', views.open_update_menu, name='open_update_menu'),
    path('update_menu/<int:restaurant_id>/', views.update_menu, name='update_menu'),
    path('view_menu/<int:restaurant_id>/<str:username>/', views.view_menu, name='view_menu'),
    path('add_to_cart/<int:item_id>/<str:username>/', views.add_to_cart, name='add_to_cart'),

    # User Features
    path('profile/<str:username>/', views.profile, name='profile'),
    path('profile/', views.profile_default, name='profile_default'),
    path('customer_home/<str:username>/', views.customer_home, name='customer_home'),
    path('show_cart/<str:username>/', views.show_cart, name='show_cart'),
    path('remove_from_cart/<str:username>/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/<str:username>/', views.checkout, name='checkout'),
    path('orders/<str:username>/', views.orders, name='orders'),
    path('save-profile/', views.save_profile, name='save_profile'),
    path('payment/', views.payment_view, name='payment'),
]