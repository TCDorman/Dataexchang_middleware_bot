@echo off
set TASK_NAME=Modula_quick_test_customer_Runtime

echo Removing startup task for Quick Test Customer runtime...
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

echo.
echo Startup task removed successfully.
echo.
pause
