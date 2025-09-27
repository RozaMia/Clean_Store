from django.db import models
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .validators import (
    validate_image_size,
    validate_image_extension,
    validate_quantity,
    validate_positive_price,
    phone_validator
)

class Category(models.Model):
    title = models.CharField(
        verbose_name='Название категории',
        max_length=255,
        unique=True,
        db_index=True
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        blank=True,
        db_index=True
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    image = models.ImageField(
        verbose_name='Обложка категории',
        upload_to='categories/',
        blank=True,
        null=True,
        validators=[validate_image_size, validate_image_extension]
    )
    is_active = models.BooleanField(
        verbose_name='Активна',
        default=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Дата изменения',
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "категории"
        ordering = ['title']
        indexes = [
            models.Index(fields=['is_active', 'title']),
            models.Index(fields=['created_at']),
        ]


class Subcategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='Основная категория'
    )
    title = models.CharField(
        verbose_name='Название подкатегории',
        max_length=255
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        blank=True
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    image = models.ImageField(
        verbose_name='Изображение подкатегории',
        upload_to='subcategories/',
        blank=True,
        null=True,
        validators=[validate_image_size, validate_image_extension]
    )
    is_active = models.BooleanField(
        verbose_name='Активна',
        default=True
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Дата изменения',
        auto_now=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.title} {self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} → {self.title}"

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "подкатегории"
        ordering = ['category', 'title']

class Product(models.Model):
    name = models.CharField(
        verbose_name='Название продукта',
        max_length=255
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        blank=True
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        verbose_name='Подкатегория'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    main_image = models.ImageField(
        verbose_name='Загрузите фото продукта',
        upload_to='main/',
        validators=[validate_image_size, validate_image_extension]
    )
    price = MoneyField(
        verbose_name='Цена',
        max_digits=14,
        decimal_places=2,
        default_currency='RUB'
    )
    is_active = models.BooleanField(
        verbose_name='Активен',
        default=True,
        help_text='Снимите галочку, чтобы скрыть товар из магазина'
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='Дата изменения',
        auto_now=True
    )
    is_new = models.BooleanField("Новинка", default=False)
    is_hit = models.BooleanField("Хит продаж", default=False)
    is_sale = models.BooleanField("Распродажа", default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # исправлено: self.name, а не self.title
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.subcategory})"

    class Meta:
        verbose_name = "Товар для продажи"
        verbose_name_plural = "товары для продажи"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_new']),
            models.Index(fields=['subcategory', 'is_active']),
            models.Index(fields=['is_hit', 'is_active']),
            models.Index(fields=['is_sale', 'is_active']),
            models.Index(fields=['-created_at']),
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(
        upload_to='extra/',
        verbose_name='Изображение',
        validators=[validate_image_size, validate_image_extension]
    )

    def __str__(self):
        return f"Изображение для {self.product.name}"

    class Meta:
        verbose_name = "Изображение продукта"
        verbose_name_plural = "изображения продуктов"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(
        default=1, 
        verbose_name='Количество',
        validators=[validate_quantity]
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    phone = models.CharField("Телефон", max_length=20, validators=[phone_validator])
    address = models.TextField("Адрес доставки")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = MoneyField("Итого", max_digits=10, decimal_places=2, default_currency='RUB')
    created_at = models.DateTimeField("Дата заказа", auto_now_add=True)

    def __str__(self):
        return f"Заказ №{self.id} от {self.created_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField("Количество", default=1)
    price = MoneyField("Цена за ед.", max_digits=10, decimal_places=2, default_currency='RUB')

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"

class ContactMessage(models.Model):
    name = models.CharField("Имя", max_length=100)
    email = models.EmailField("Email")
    message = models.TextField("Сообщение")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Сообщение от {self.name}"

    class Meta:
        verbose_name = "Сообщение с сайта"
        verbose_name_plural = "Сообщения с сайта"