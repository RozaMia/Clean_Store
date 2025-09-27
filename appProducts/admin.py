from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from .models import Category, Subcategory, Product, ProductImage, OrderItem, Order

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    verbose_name = "Дополнительное изображение"
    verbose_name_plural = "Дополнительные изображения"

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    verbose_name = "Подкатегория"
    verbose_name_plural = "Подкатегории"

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['title', 'image_preview', 'subcategory_count', 'is_active', 'created_at']
    list_display_links = ['title']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SubcategoryInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview_large'),
            'description': 'Загрузите красивое изображение для категории. Рекомендуемый размер: 400x300 пикселей.'
        }),
    )
    readonly_fields = ['image_preview_large']
    ordering = ['-created_at']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;">',
                obj.image.url
            )
        return '🖼️ Без изображения'
    image_preview.short_description = 'Превью'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; object-fit: cover; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">',
                obj.image.url
            )
        return format_html(
            '<div style="padding: 20px; background: #f5f5f5; border-radius: 10px; text-align: center; color: #666;">🖼️<br>Изображение не загружено</div>'
        )
    image_preview_large.short_description = 'Предпросмотр изображения'
    
    def subcategory_count(self, obj):
        count = obj.subcategories.count()
        return f'{count} подкатегорий'
    subcategory_count.short_description = 'Подкатегории'

    # Переопределяем change_view, чтобы показать вкладки "General" и "Подкатегории"
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Редактирование категории'
        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        # Можно добавить кастомные URL, если нужно
        return urls


@admin.register(Subcategory)
class SubcategoryAdmin(ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'category__title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_at']

    # Добавим ссылку "Назад к категории"
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        subcategory = self.get_object(request, object_id)
        if subcategory:
            extra_context['subtitle'] = f"Подкатегория: {subcategory.title}"
            extra_context['back_url'] = f"/admin/appProducts/category/{subcategory.category.id}/change/"
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'subcategory', 'price', 'is_active', 'created_at']
    list_display_links = ['name']
    list_editable = ['price', 'is_active']
    list_filter = ['subcategory__category', 'subcategory', 'is_active', 'created_at', 'is_new', 'is_hit', 'is_sale']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    exclude = ['created_at', 'updated_at']
    ordering = ['-created_at']

    # Показываем поле subcategory вместо category
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subcategory":
            # Можно фильтровать по активным подкатегориям
            kwargs["queryset"] = Subcategory.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(ProductImage)
class ProductImageAdmin(ModelAdmin):
    list_display = ['product', 'image']
    list_filter = ['product']
    search_fields = ['product__name']
    ordering = ['product']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'status', 'total_price', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['user', 'first_name', 'last_name', 'phone', 'address', 'total_price', 'created_at']