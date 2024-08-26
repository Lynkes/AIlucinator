import os
import sys
from colorama import Fore, Style

def check_env():
    # Check virtual env
    if os.environ.get('VIRTUAL_ENV'):
        print(Style.BRIGHT + Fore.GREEN + 'You are in a virtual environment:', os.environ['VIRTUAL_ENV'])
    elif sys.base_prefix != sys.prefix:
        print(Style.BRIGHT + Fore.BLUE + 'You are in a virtual environment:', sys.prefix)
    elif os.path.exists("python-embeded"):
        print(Style.BRIGHT + Fore.BLUE + 'You are in an embedded environment:', sys.prefix)
    else:
        print(Style.BRIGHT + Fore.RED + 'You are not in a virtual environment, we\'ll continue anyways')
