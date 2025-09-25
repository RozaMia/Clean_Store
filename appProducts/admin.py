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
    list_display = ['title', 'parent', 'slug']
    list_filter = ['parent']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['title']
    autocomplete_fields = ['parent']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(parent__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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