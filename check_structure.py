# debug_templates.py
import os
import sys

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'app', 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'app', 'static')

print("🔍 DIAGNÓSTICO DE TEMPLATES")
print(f"📁 Directorio actual: {BASE_DIR}")
print(f"📁 Templates configurado: {TEMPLATES_DIR}")
print(f"📁 Static configurado: {STATIC_DIR}")

# Verificar si existen los directorios
print(f"\n✅ Directorio templates existe: {os.path.exists(TEMPLATES_DIR)}")
print(f"✅ Directorio static existe: {os.path.exists(STATIC_DIR)}")

if os.path.exists(TEMPLATES_DIR):
    templates = os.listdir(TEMPLATES_DIR)
    print(f"📂 Archivos en templates/: {templates}")
else:
    print("❌ NO EXISTE el directorio templates/")

if os.path.exists(STATIC_DIR):
    static_files = os.listdir(STATIC_DIR)
    print(f"📂 Archivos en static/: {static_files}")
else:
    print("❌ NO EXISTE el directorio static/")

# Verificar rutas absolutas de templates específicos
templates_to_check = ['base.html', 'index.html', 'login.html', 'dashboard.html']
print(f"\n🔎 Verificando templates específicos:")
for template in templates_to_check:
    template_path = os.path.join(TEMPLATES_DIR, template)
    exists = os.path.exists(template_path)
    print(f"   {template}: {'✅ EXISTE' if exists else '❌ NO EXISTE'} - {template_path}")