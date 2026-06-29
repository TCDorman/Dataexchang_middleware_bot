@echo off
set TASK_NAME=Modula_quick_test_customer_Runtime

echo Installing startup task for Quick Test Customer runtime...
echo.

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /SC ONLOGON ^
    /RL HIGHEST ^
    /TR "\"%~dp0start_runtime.bat\"" ^
    /F

echo.
echo Startup task installed successfully.
echo The runtime will start automatically when this Windows user logs in.
echo.
pause
