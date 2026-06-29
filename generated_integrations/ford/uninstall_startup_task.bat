@echo off
set TASK_NAME=Modula_ford_Runtime

echo Removing startup task for Ford runtime...
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

echo.
echo Startup task removed successfully.
echo.
pause
