#!/usr/bin/env python3
"""
Скрипт для проверки структуры CSS модулей
"""

import os
import re

def check_css_structure():
    """Проверяет структуру CSS модулей"""
    
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    expected_modules = [
        '01-base.css',
        '02-header.css', 
        '03-components.css',
        '04-footer.css',
        '05-home.css',
        '06-catalog.css',
        '07-cart.css',
        '08-responsive.css',
        '09-product-detail.css',
        '10-contact.css',
        '11-auth.css',
        '12-checkout.css'
    ]
    
    print("🔍 Проверка структуры CSS модулей...")
    print("=" * 50)
    
    # Проверяем наличие всех модулей
    missing_modules = []
    for module in expected_modules:
        module_path = os.path.join(modules_dir, module)
        if os.path.exists(module_path):
            size = os.path.getsize(module_path)
            print(f"✅ {module} - {size} байт")
        else:
            missing_modules.append(module)
            print(f"❌ {module} - ОТСУТСТВУЕТ")
    
    # Проверяем главный файл
    main_file = os.path.join(os.path.dirname(modules_dir), 'style-modular.css')
    if os.path.exists(main_file):
        size = os.path.getsize(main_file)
        print(f"✅ style-modular.css - {size} байт")
    else:
        print(f"❌ style-modular.css - ОТСУТСТВУЕТ")
    
    # Проверяем README
    readme_file = os.path.join(modules_dir, 'README.md')
    if os.path.exists(readme_file):
        size = os.path.getsize(readme_file)
        print(f"✅ README.md - {size} байт")
    else:
        print(f"❌ README.md - ОТСУТСТВУЕТ")
    
    print("=" * 50)
    
    if missing_modules:
        print(f"❌ Отсутствуют модули: {', '.join(missing_modules)}")
        return False
    else:
        print("✅ Все модули на месте!")
        return True

def check_imports():
    """Проверяет импорты в главном файле"""
    
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(os.path.dirname(modules_dir), 'style-modular.css')
    
    if not os.path.exists(main_file):
        print("❌ Главный файл не найден")
        return False
    
    print("\n🔍 Проверка импортов...")
    print("=" * 50)
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем все импорты
    imports = re.findall(r"@import url\('modules/([^']+)'\);", content)
    
    expected_imports = [
        '01-base.css',
        '02-header.css',
        '03-components.css', 
        '04-footer.css',
        '05-home.css',
        '06-catalog.css',
        '07-cart.css',
        '08-responsive.css',
        '09-product-detail.css',
        '10-contact.css',
        '11-auth.css',
        '12-checkout.css'
    ]
    
    for imp in expected_imports:
        if imp in imports:
            print(f"✅ Импорт {imp}")
        else:
            print(f"❌ Отсутствует импорт {imp}")
    
    print("=" * 50)
    
    if len(imports) == len(expected_imports):
        print("✅ Все импорты на месте!")
        return True
    else:
        print(f"❌ Количество импортов не совпадает: {len(imports)}/{len(expected_imports)}")
        return False

def get_statistics():
    """Получает статистику по модулям"""
    
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n📊 Статистика модулей...")
    print("=" * 50)
    
    total_lines = 0
    total_size = 0
    
    for filename in sorted(os.listdir(modules_dir)):
        if filename.endswith('.css'):
            filepath = os.path.join(modules_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            size = os.path.getsize(filepath)
            
            total_lines += lines
            total_size += size
            
            print(f"{filename:20} - {lines:4} строк, {size:6} байт")
    
    print("-" * 50)
    print(f"{'ИТОГО':20} - {total_lines:4} строк, {total_size:6} байт")
    print("=" * 50)

if __name__ == "__main__":
    print("🚀 Проверка CSS модулей Clean Store")
    print("=" * 50)
    
    structure_ok = check_css_structure()
    imports_ok = check_imports()
    get_statistics()
    
    if structure_ok and imports_ok:
        print("\n🎉 Все проверки пройдены успешно!")
        exit(0)
    else:
        print("\n❌ Обнаружены проблемы!")
        exit(1)
