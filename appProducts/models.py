from django.db import models
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from django.contrib.auth.models import User

class Category(models.Model):
    title = models.CharField(
        verbose_name='Название категории',
        max_length=255,
        unique=True
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
        verbose_name='Обложка категории',
        upload_to='categories/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        verbose_name='Активна',
        default=True
    )
    create_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    update_at = models.DateTimeField(
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
        blank=True
    )
    is_active = models.BooleanField(
        verbose_name='Активна',
        default=True
    )
    create_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    update_at = models.DateTimeField(
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
        upload_to='main/'
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
    create_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    update_at = models.DateTimeField(
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
        ordering = ['-create_at']


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Товар'
    )
    image = models.ImageField(
        upload_to='extra/',
        verbose_name='Изображение'
    )

    def __str__(self):
        return f"Изображение для {self.product.name}"

    class Meta:
        verbose_name = "Изображение продукта"
        verbose_name_plural = "изображения продуктов"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

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
    phone = models.CharField("Телефон", max_length=20)
    address = models.TextField("Адрес доставки")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    total_price = models.DecimalField("Итого", max_digits=10, decimal_places=2)
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
    price = models.DecimalField("Цена за ед.", max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказе"