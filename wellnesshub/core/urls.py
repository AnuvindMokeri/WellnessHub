from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Auth
    path('signup/', views.customer_signup, name='customer_signup'),
    path('vendor/signup/', views.vendor_signup, name='vendor_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('vendor/pending/', views.vendor_pending_view, name='vendor_pending'),

    # Customer
    path('profile/', views.customer_profile, name='customer_profile'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.my_orders, name='my_orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('complaints/', views.my_complaints, name='my_complaints'),

    # Vendor
    path('vendor/', views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/profile/', views.vendor_profile, name='vendor_profile'),
    path('vendor/products/', views.vendor_products, name='vendor_products'),
    path('vendor/products/add/', views.add_product, name='add_product'),
    path('vendor/products/<int:pk>/edit/', views.edit_product, name='edit_product'),
    path('vendor/products/<int:pk>/delete/', views.delete_product, name='delete_product'),
    path('vendor/orders/', views.vendor_orders, name='vendor_orders'),
    path('vendor/orders/<int:item_id>/status/', views.update_order_item_status, name='update_order_item_status'),
    path('vendor/sales-report/', views.vendor_sales_report, name='vendor_sales_report'),
    path('vendor/reviews/', views.vendor_reviews, name='vendor_reviews'),

    # Admin
    path('control/', views.admin_dashboard, name='admin_dashboard'),
    path('control/users/', views.manage_users, name='manage_users'),
    path('control/users/<int:user_id>/toggle/', views.toggle_user_active, name='toggle_user_active'),
    path('control/vendors/', views.manage_vendors, name='manage_vendors'),
    path('control/vendors/<int:vendor_id>/status/', views.update_vendor_status, name='update_vendor_status'),
    path('control/products/', views.manage_products, name='manage_products'),
    path('control/products/<int:pk>/remove/', views.admin_remove_product, name='admin_remove_product'),
    path('control/categories/', views.manage_categories, name='manage_categories'),
    path('control/orders/', views.manage_orders, name='manage_orders'),
    path('control/sales-report/', views.admin_sales_report, name='admin_sales_report'),
    path('control/complaints/', views.manage_complaints, name='manage_complaints'),
    path('control/complaints/<int:pk>/reply/', views.reply_complaint, name='reply_complaint'),
]
