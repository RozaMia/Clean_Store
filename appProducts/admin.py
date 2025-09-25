from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Category, Subcategory, Product, ProductImage

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
    list_display = ['title', 'slug', 'is_active', 'create_at']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SubcategoryInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'image', 'is_active')
        }),
    )
    ordering = ['-create_at']

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
    list_display = ['title', 'category', 'is_active', 'create_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'category__title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-create_at']

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
    list_display = ['name', 'subcategory', 'price', 'is_active', 'create_at']
    list_display_links = ['name']
    list_editable = ['price', 'is_active']
    list_filter = ['subcategory__category', 'subcategory', 'is_active', 'create_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    exclude = ['create_at', 'update_at']
    ordering = ['-create_at']

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