"""
Валидаторы для приложения appProducts
"""
import os
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_image_size(image):
    """Валидатор размера изображения - максимум 5MB"""
    max_size = 5 * 1024 * 1024  # 5MB
    if image.size > max_size:
        raise ValidationError(
            f"Размер файла слишком большой. Максимум: {max_size // (1024*1024)}MB. "
            f"Текущий размер: {image.size // (1024*1024)}MB"
        )


def validate_image_extension(image):
    """Валидатор расширения изображения"""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"Недопустимое расширение файла: {ext}. "
            f"Разрешенные: {', '.join(allowed_extensions)}"
        )


def validate_quantity(value):
    """Валидатор количества товара"""
    if value < 1:
        raise ValidationError("Количество должно быть больше 0")
    if value > 100:
        raise ValidationError("Количество не может быть больше 100")


def validate_positive_price(value):
    """Валидатор положительной цены"""
    if value <= 0:
        raise ValidationError("Цена должна быть больше нуля")


# Общий валидатор телефона для использования в моделях и формах
phone_validator = RegexValidator(
    regex=r'^\+?[1-9]\d{8,14}$',
    message="Номер телефона должен быть в формате: '+999999999'. От 9 до 15 цифр."
)
