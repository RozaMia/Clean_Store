from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Category, Subcategory, Product, CartItem, Order, OrderItem, ContactMessage
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms

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
    new_products = Product.objects.filter(is_new=True, is_active=True)[:6]
    return render(request, 'home/home.html', {'new_products': new_products})

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

@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum(item.product.price.amount * item.quantity for item in cart_items)
    return render(request, 'appProducts/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('appProducts:cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return redirect('appProducts:cart')



class OrderForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="Имя")
    last_name = forms.CharField(max_length=100, label="Фамилия")
    phone = forms.CharField(max_length=20, label="Телефон")
    address = forms.CharField(widget=forms.Textarea, label="Адрес")

@login_required
def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    if not cart_items:
        return redirect('appProducts:cart')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
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
            return redirect('appProducts:order_success')
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
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Сохранить в БД или отправить email
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            messages.success(request, "Ваше сообщение отправлено! Мы свяжемся с вами.")
            return redirect('appProducts:contact')
    else:
        form = ContactForm()
    return render(request, 'appProducts/contact.html', {'form': form})

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, label="Ваше имя")
    email = forms.EmailField(label="Email")
    message = forms.CharField(widget=forms.Textarea, label="Сообщение")