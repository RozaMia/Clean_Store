from django.db import models
from django.utils.text import slugify
from djmoney.models.fields import MoneyField

class Category(models.Model):
    title = models.CharField(
        verbose_name= 'Название',
        max_length=255,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Slug',
        unique=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

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
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='Категория'
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
        default_currency = 'RUB'
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
        return f"{self.name} ({self.category})"
    
    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Продукт'
    )
    image = models.ImageField(
        upload_to='extra/',
        verbose_name='Изображение'        
    )

    def __str__(self):
        return f"Изображение для {self.product.name}"

    class Meta:
        verbose_name = "Изображение продукта"
        verbose_name_plural = "Изображения продуктов"