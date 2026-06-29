@echo off
set TASK_NAME=Modula_xml_test_customer_Agent

echo Installing startup task for XML Test Customer...
echo.

schtasks /Create ^
    /TN "%TASK_NAME%" ^
    /SC ONLOGON ^
    /RL HIGHEST ^
    /TR "python \"%~dp0run_xml_test_customer_local_agent.py\" --watch --poll-seconds 10" ^
    /F

echo.
echo Startup task installed successfully.
echo The local agent will start automatically when this Windows user logs in.
echo.
pause
