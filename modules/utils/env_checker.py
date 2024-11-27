import os
import sys
from colorama import Fore, Style

def check_env():
    # Check virtual env
    if os.environ.get('VIRTUAL_ENV'):
        checkenvfile()
        print(Style.BRIGHT + Fore.GREEN + 'You are in a virtual environment:', os.environ['VIRTUAL_ENV'])
    elif sys.base_prefix != sys.prefix:
        checkenvfile()
        print(Style.BRIGHT + Fore.BLUE + 'You are in a virtual environment:', sys.prefix)
    elif os.path.exists("python-embedded"):
        checkenvfile()
        print(Style.BRIGHT + Fore.BLUE + 'You are in an embedded environment:', sys.prefix)
    else:
        print(Style.BRIGHT + Fore.RED + 'You are not in a virtual environment')

def checkenvfile():
    # If user didn't rename example.env
    if os.path.exists("example.env") and not os.path.exists(".env"):
        os.rename("example.env", ".env")
        print(Style.BRIGHT + Fore.RED + "Renamed example.env to .env")
    elif os.path.exists(".env"):
        print(Fore.LIGHTGREEN_EX + "***AI Starting***")
        print("Loading .env")
    else:
        print("ERROR")
