@echo off
chcp 65001 > nul
title QuantumTrader Pro - MODO DESARROLLO

echo.
echo 🚀 QUANTUMTRADER PRO - MODO DESARROLLO
echo.

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 📊 Iniciando servidor de desarrollo...
echo 🌐 URL: http://localhost:8000
echo 👤 Usuario: admin
echo 🔑 Contraseña: admin123
echo.
echo 🐛 Modo debug activado
echo 📝 Los errores se mostrarán en pantalla
echo.

python main.py

pause