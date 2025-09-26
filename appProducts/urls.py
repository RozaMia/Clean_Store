from django.urls import path
from . import views

app_name = 'appProducts'

urlpatterns = [
    path('', views.category_list, name='category_list'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('contact/', views.contact_view, name='contact'),
    path('order/success/', views.order_success, name='order_success'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    path('<slug:category_slug>/', views.subcategory_list, name='subcategory_list'),
    path('<slug:category_slug>/<slug:subcategory_slug>/', views.product_list, name='product_list'),
    path('<slug:category_slug>/<slug:subcategory_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
]