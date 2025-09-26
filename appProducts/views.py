import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Prefetch
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods, require_POST
from .models import Category, Subcategory, Product, CartItem, Order, OrderItem, ContactMessage
from .forms import OrderForm, ContactForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

@cache_page(60 * 15)  # Кэшируем на 15 минут
def category_list(request):
    """Главная страница: список всех активных категорий"""
    categories = Category.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'subcategories',
            queryset=Subcategory.objects.filter(is_active=True)
        )
    ).order_by('title')
    
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

    tag = request.GET.get('tag')
    if tag == 'new':
        products = products.filter(is_new=True)
    elif tag == 'hit':
        products = products.filter(is_hit=True)
    elif tag == 'sale':
        products = products.filter(is_sale=True)

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

@cache_page(60 * 30)  # Кэшируем на 30 минут
def home_view(request):
    """Главная страница с оптимизированными запросами"""
    new_products = Product.objects.filter(
        is_new=True, 
        is_active=True
    ).select_related(
        'subcategory__category'
    ).prefetch_related('images')[:6]
    
    return render(request, 'home/home.html', {
        'new_products': new_products
    })

@login_required
@require_POST
def add_to_cart(request, product_id):
    """Добавление товара в корзину с валидацией"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Получаем количество из POST
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
            
        # Валидация количества
        if quantity < 1 or quantity > 100:
            messages.error(request, "Количество должно быть от 1 до 100")
            return redirect('appProducts:product_detail',
                            category_slug=product.subcategory.category.slug,
                            subcategory_slug=product.subcategory.slug,
                            product_slug=product.slug)
        
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Проверяем, не превысим ли лимит
            new_quantity = cart_item.quantity + quantity
            if new_quantity > 100:
                messages.error(request, "Максимальное количество товара в корзине: 100")
                return redirect('appProducts:product_detail',
                                category_slug=product.subcategory.category.slug,
                                subcategory_slug=product.subcategory.slug,
                                product_slug=product.slug)
            cart_item.quantity = new_quantity
            cart_item.save()
            
        messages.success(request, f"{product.name} добавлен в корзину (количество: {quantity})!")
        logger.info(f"Пользователь {request.user.username} добавил {quantity} x {product.name} в корзину")
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}")
        messages.error(request, "Произошла ошибка при добавлении товара в корзину")
        return redirect('appProducts:category_list')
    
    return redirect('appProducts:product_detail',
                    category_slug=product.subcategory.category.slug,
                    subcategory_slug=product.subcategory.slug,
                    product_slug=product.slug)

@login_required
def cart_view(request):
    """Корзина с оптимизированными запросами"""
    cart_items = CartItem.objects.filter(user=request.user).select_related(
        'product__subcategory__category'
    ).prefetch_related('product__images')
    
    # Используем агрегацию для вычисления суммы
    total_data = cart_items.aggregate(
        total=Sum(F('product__price') * F('quantity'))
    )
    total = total_data['total'] or 0
    
    return render(request, 'appProducts/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
@require_POST
def update_cart(request, item_id):
    """Обновление количества товара в корзине с валидацией"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            messages.error(request, "Некорректное количество товара")
            return redirect('appProducts:cart')
            
        if quantity > 0:
            if quantity > 100:
                messages.error(request, "Максимальное количество: 100")
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Количество товара обновлено")
        else:
            cart_item.delete()
            messages.success(request, "Товар удален из корзины")
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении корзины: {e}")
        messages.error(request, "Произошла ошибка при обновлении корзины")
    
    return redirect('appProducts:cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('appProducts:cart')




@login_required
def checkout(request):
    """Оформление заказа с транзакционной безопасностью"""
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        messages.warning(request, "Ваша корзина пуста")
        return redirect('appProducts:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    total = sum(item.product.price.amount * item.quantity for item in cart_items)
                    order = Order.objects.create(
                        user=request.user,
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        phone=form.cleaned_data['phone'],
                        address=form.cleaned_data['address'],
                        total_price=total
                    )
                    for item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price.amount
                        )
                    cart_items.delete()  # очистить корзину
                    logger.info(f"Заказ #{order.id} создан пользователем {request.user.username}")
                    messages.success(request, f"Заказ #{order.id} успешно создан!")
                    return redirect('appProducts:order_success')
            except ValidationError as e:
                messages.error(request, f"Ошибка валидации: {e}")
            except Exception as e:
                logger.error(f"Ошибка при создании заказа: {e}")
                messages.error(request, "Произошла ошибка при оформлении заказа. Попробуйте еще раз.")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = OrderForm()

    total = sum(item.product.price.amount * item.quantity for item in cart_items)
    return render(request, 'appProducts/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total': total
    })

def order_success(request):
    return render(request, 'appProducts/order_success.html')

def contact_view(request):
    """Обработка формы обратной связи"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                ContactMessage.objects.create(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    message=form.cleaned_data['message']
                )
                logger.info(f"Получено сообщение от {form.cleaned_data['email']}")
                messages.success(request, "Ваше сообщение отправлено! Мы свяжемся с вами.")
                return redirect('appProducts:contact')
            except Exception as e:
                logger.error(f"Ошибка при сохранении сообщения: {e}")
                messages.error(request, "Произошла ошибка при отправке сообщения")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = ContactForm()
    return render(request, 'appProducts/contact.html', {'form': form})