from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Category, Subcategory, Product, CartItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def category_list(request):
    """Главная страница: список всех активных категорий"""
    categories = Category.objects.filter(is_active=True).prefetch_related(
        'subcategories'
    )
    return render(request, 'appProducts/category_list.html', {
        'categories': categories
    })

def subcategory_list(request, category_slug):
    """Список подкатегорий в выбранной категории"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategories = category.subcategories.filter(is_active=True)
    return render(request, 'appProducts/subcategory_list.html', {
        'category': category,
        'subcategories': subcategories
    })

def product_list(request, category_slug, subcategory_slug):
    """Список товаров в выбранной подкатегории"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(
        Subcategory,
        slug=subcategory_slug,
        category=category,
        is_active=True
    )
    products = Product.objects.filter(
        subcategory=subcategory,
        is_active=True
    ).select_related('subcategory__category').prefetch_related('images')

    # Пагинация (по 12 товаров на страницу)
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'appProducts/product_list.html', {
        'category': category,
        'subcategory': subcategory,
        'page_obj': page_obj
    })

def product_detail(request, category_slug, subcategory_slug, product_slug):
    """Страница отдельного товара"""
    product = get_object_or_404(
        Product,
        slug=product_slug,
        subcategory__slug=subcategory_slug,
        subcategory__category__slug=category_slug,
        is_active=True
    )
    extra_images = product.images.all()

    return render(request, 'appProducts/product_detail.html', {
        'product': product,
        'extra_images': extra_images
    })

def home_view(request):
    return render(request, 'home/home.html')

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.name} добавлен в корзину!")
    return redirect('appProducts:product_detail',
                    category_slug=product.subcategory.category.slug,
                    subcategory_slug=product.subcategory.slug,
                    product_slug=product.slug)