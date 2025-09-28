import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Prefetch
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
import json
from .models import Category, Subcategory, Product, CartItem, Order, OrderItem, ContactMessage
from .forms import OrderForm, ContactForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

logger = logging.getLogger(__name__)

def category_list(request):
    """Главная страница: список всех активных категорий + поиск"""
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Поиск по товарам
        products = Product.objects.filter(
            name__icontains=search_query,
            is_active=True
        ).select_related('subcategory__category').prefetch_related('images')[:20]
        
        categories = Category.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Subcategory.objects.filter(is_active=True)
            )
        ).order_by('title')
        
        return render(request, 'appProducts/category_list.html', {
            'categories': categories,
            'search_query': search_query,
            'search_results': products,
            'search_count': products.count()
        })
    else:
        categories = Category.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Subcategory.objects.filter(is_active=True)
            )
        ).order_by('title')
        
        return render(request, 'appProducts/category_list.html', {
            'categories': categories
        })


def all_products(request):
    """Страница всех товаров с фильтрацией и сортировкой"""
    # Получаем параметры фильтрации
    category_filter = request.GET.get('category', '')
    subcategory_filter = request.GET.get('subcategory', '')
    sort_by = request.GET.get('sort', 'name')
    search_query = request.GET.get('search', '').strip()
    
    # Базовый queryset
    products = Product.objects.filter(is_active=True).select_related(
        'subcategory__category'
    ).prefetch_related('images')
    
    # Применяем фильтры
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    if category_filter:
        products = products.filter(subcategory__category__slug=category_filter)
    
    if subcategory_filter:
        products = products.filter(subcategory__slug=subcategory_filter)
    
    # Применяем сортировку
    sort_options = {
        'name': 'name',
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'popular': '-views_count',
    }
    
    if sort_by in sort_options:
        products = products.order_by(sort_options[sort_by])
    else:
        products = products.order_by('name')
    
    # Пагинация
    paginator = Paginator(products, 24)  # 24 товара на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем категории и подкатегории для фильтров
    categories = Category.objects.filter(is_active=True).order_by('title')
    subcategories = Subcategory.objects.filter(is_active=True).order_by('title')
    
    # Если выбрана категория, показываем только её подкатегории
    if category_filter:
        subcategories = subcategories.filter(category__slug=category_filter)
    
    # Получаем названия выбранных фильтров для отображения
    current_category_name = None
    current_subcategory_name = None
    
    if category_filter:
        try:
            current_category_obj = categories.get(slug=category_filter)
            current_category_name = current_category_obj.title
        except Category.DoesNotExist:
            pass
    
    if subcategory_filter:
        try:
            current_subcategory_obj = subcategories.get(slug=subcategory_filter)
            current_subcategory_name = current_subcategory_obj.title
        except Subcategory.DoesNotExist:
            pass
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
        'subcategories': subcategories,
        'current_category': category_filter,
        'current_subcategory': subcategory_filter,
        'current_category_name': current_category_name,
        'current_subcategory_name': current_subcategory_name,
        'current_sort': sort_by,
        'search_query': search_query,
        'total_products': products.count(),
    }
    
    return render(request, 'appProducts/all_products.html', context)

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

def home_view(request):
    """Главная страница с оптимизированными запросами"""
    new_products = Product.objects.filter(
        is_new=True, 
        is_active=True
    ).select_related(
        'subcategory__category'
    ).prefetch_related('images')[:6]
    
    # Получаем популярные категории для главной страницы
    popular_categories = Category.objects.filter(
        is_active=True
    ).prefetch_related('subcategories')[:9]  # Берем 9 категорий для сетки 3x3
    
    return render(request, 'home/home.html', {
        'new_products': new_products,
        'popular_categories': popular_categories
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
        
        # Если это AJAX запрос, возвращаем JSON ответ
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': True,
                'message': f"{product.name} добавлен в корзину!",
                'cart_count': CartItem.objects.filter(user=request.user).count()
            })
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину: {e}")
        
        # Если это AJAX запрос, возвращаем JSON ошибку
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'message': 'Произошла ошибка при добавлении товара в корзину'
            }, status=400)
            
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
        
        # Получаем данные из POST или JSON
        if request.headers.get('Content-Type') == 'application/json':
            import json
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        else:
            quantity = int(request.POST.get('quantity', 1))
            
        if quantity > 0:
            if quantity > 100:
                error_msg = "Максимальное количество: 100"
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'message': error_msg})
                messages.error(request, error_msg)
            else:
                cart_item.quantity = quantity
                cart_item.save()
                success_msg = "Количество товара обновлено"
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': True, 'message': success_msg})
                messages.success(request, success_msg)
        else:
            cart_item.delete()
            success_msg = "Товар удален из корзины"
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True, 'message': success_msg})
            messages.success(request, success_msg)
            
    except (ValueError, TypeError):
        error_msg = "Некорректное количество товара"
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    except Exception as e:
        logger.error(f"Ошибка при обновлении корзины: {e}")
        error_msg = "Произошла ошибка при обновлении корзины"
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': False, 'message': error_msg})
        messages.error(request, error_msg)
    
    # Обычный запрос - редирект
    return redirect('appProducts:cart')

@login_required
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        cart_item.delete()
        
        # Если это AJAX запрос, возвращаем JSON
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': True, 'message': 'Товар удален из корзины'})
        
        # Обычный запрос - редирект
        return redirect('appProducts:cart')
    except Exception as e:
        logger.error(f"Error removing item from cart: {e}")
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'message': 'Ошибка при удалении товара'})
        return redirect('appProducts:cart')

@login_required
@require_POST
def clear_cart(request):
    """Очистка всей корзины пользователя"""
    try:
        cart_items = CartItem.objects.filter(user=request.user)
        items_count = cart_items.count()
        cart_items.delete()
        
        # Если это AJAX запрос, возвращаем JSON
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'success': True, 
                'message': f'Корзина очищена. Удалено товаров: {items_count}'
            })
        
        messages.success(request, f'Корзина очищена. Удалено товаров: {items_count}')
        return redirect('appProducts:cart')
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': False, 'message': 'Ошибка при очистке корзины'})
        messages.error(request, 'Ошибка при очистке корзины')
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
                    phone=form.cleaned_data.get('phone', ''),
                    category=form.cleaned_data['category'],
                    subject=form.cleaned_data.get('subject', ''),
                    message=form.cleaned_data['message']
                )
                logger.info(f"Получено сообщение [{form.cleaned_data['category']}] от {form.cleaned_data['email']}")
                messages.success(request, "Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.")
                return redirect('appProducts:contact')
            except Exception as e:
                logger.error(f"Ошибка при сохранении сообщения: {e}")
                messages.error(request, "Произошла ошибка при отправке сообщения")
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = ContactForm()
    return render(request, 'appProducts/contact.html', {'form': form})