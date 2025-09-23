from django.contrib import admin
from unfold.admin import ModelAdmin
from djmoney.admin import MoneyField
from .models import Category, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "Дополнительное изображение"
    verbose_name_plural = "Дополнительные изображения"

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'category', 'price', 'create_at', 'update_at', 'is_active']
    list_display_links = ['category', 'create_at', 'update_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    exclude = ['create_at', 'update_at']
    list_editable = ['price']

    def is_active(self, obj):
        return True
    is_active.boolean = True
    is_active.short_description = 'Активен'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image']
    list_filter = ['product']
    search_fields = ['product__name']