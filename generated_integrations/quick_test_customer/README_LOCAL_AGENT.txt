LOCAL CUSTOMER AGENT PACKAGE

Customer:
Quick Test Customer

Source Type:
file

Main Runtime:
always_on_runtime.py

Launcher:
start_runtime.bat

Runtime Input Folder:
runtime\customer_input

Runtime Modula XML Output Folder:
runtime\modula_output

Runtime Processed Folder:
runtime\processed

Runtime Error Folder:
runtime\errors

Runtime Profiles Folder:
runtime\profiles

Customer Profile:
configs/customers/ford_profile.json

Legacy Runner:
run_quick_test_customer_local_agent.py

Legacy Run Once:
python run_quick_test_customer_local_agent.py --once

Legacy Watch:
python run_quick_test_customer_local_agent.py --watch

Install automatic startup task:
Double-click install_startup_task.bat

Uninstall automatic startup task:
Double-click uninstall_startup_task.bat

Logs:
generated_integrations\quick_test_customer\logs