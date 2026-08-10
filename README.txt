Run this code in the terminal to download the contents
from requirements.txt

cd C:\Projects (whatever your project root will be)

git clone https://github.com/TCDorman/Dataexchang_middleware_bot.git new-project-name

cd new-project-name

git switch middleware-update

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
