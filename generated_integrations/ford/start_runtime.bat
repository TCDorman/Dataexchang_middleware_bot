@echo off
cd /d "%~dp0"

echo ==================================================
echo MODULA MIDDLEWARE RUNTIME
echo Customer: Ford
echo ==================================================
echo.
echo Watching folder:
echo runtime\customer_input
echo.
echo Converted Modula XML output:
echo runtime\modula_output
echo.

python always_on_runtime.py

pause
