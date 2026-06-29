@echo off
set TASK_NAME=Modula_xml_test_customer_Agent

echo Removing startup task for XML Test Customer...
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

echo.
echo Startup task removed successfully.
echo.
pause
