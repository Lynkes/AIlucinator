import os
from colorama import Fore, Style

def load_env():
    # If user didn't rename example.env
    if os.path.exists("example.env") and not os.path.exists(".env"):
        os.rename("example.env", ".env")
        print(Style.BRIGHT + Fore.RED + "Renamed example.env to .env")
    elif os.path.exists(".env"):
        print(Fore.LIGHTGREEN_EX + "***AI Starting***")
        print("Loading .env")
    else:
        print("ERROR")

    # # Load settings from .env file
    # with open('.env') as f:
    #     for line in f:
    #         line = line.strip()
    #         if not line or line.startswith("#"):
    #             continue
    #         key, value = line.split('=', 1)
    #         os.environ[key] = value
