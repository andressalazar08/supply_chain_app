@echo off
REM Script de inicio rápido para Windows
REM Ejecutar: .\start.bat

echo ========================================
echo   ERP Educativo - Supply Chain
echo   Script de Inicio Rapido
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
    echo      OK - Entorno virtual creado
) else (
    echo [1/4] Entorno virtual encontrado
)

echo.
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat

echo.
echo [3/4] Instalando/Verificando dependencias...
pip install -r requirements.txt --quiet

echo.
echo [4/4] Verificando base de datos...
if not exist "supply_chain.db" (
    echo      Base de datos no encontrada. Inicializando...
    python init_db.py
) else (
    echo      Base de datos encontrada
)

echo.
echo ========================================
echo   Iniciando aplicacion...
echo   URL: http://localhost:5000
echo   Presiona Ctrl+C para detener
echo ========================================
echo.

python app.py
