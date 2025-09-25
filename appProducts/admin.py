from django.contrib import admin
from unfold.admin import ModelAdmin
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
    ordering = ['title']

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_active', 'create_at']
    list_display_links = ['name']
    list_editable = ['price', 'is_active']
    list_filter = ['category', 'is_active', 'create_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    exclude = ['create_at', 'update_at']
    ordering = ['-create_at']

@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ['product', 'image']
    list_filter = ['product']
    search_fields = ['product__name']
    ordering = ['product']