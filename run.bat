@echo off
chcp 65001 > nul
title QuantumTrader Pro

echo.
echo ========================================
echo    QUANTUMTRADER PRO - TRADING SYSTEM
echo ========================================
echo.

echo Iniciando servidor...
echo.
echo Dashboard: http://localhost:8000
echo Usuario: admin
echo Password: admin123
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Verifica que todos los archivos de modelos esten presentes
    echo.
)

pause