from django import forms
from django.core.validators import RegexValidator


class OrderForm(forms.Form):
    """Форма для оформления заказа"""
    
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр разрешено."
    )
    
    first_name = forms.CharField(
        max_length=100, 
        label="Имя",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
    )
    last_name = forms.CharField(
        max_length=100, 
        label="Фамилия",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вашу фамилию'
        })
    )
    phone = forms.CharField(
        max_length=20, 
        label="Телефон",
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите полный адрес доставки'
        }), 
        label="Адрес доставки"
    )


class ContactForm(forms.Form):
    """Форма обратной связи"""
    
    name = forms.CharField(
        max_length=100, 
        label="Ваше имя",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Введите ваше сообщение'
        }), 
        label="Сообщение"
    )
    
    def clean_message(self):
        """Дополнительная валидация сообщения"""
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError("Сообщение должно содержать минимум 10 символов.")
        return message