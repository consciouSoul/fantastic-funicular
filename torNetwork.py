import os
from tornet import ma_ip, change_ip, initialize_environment
from database import db
from dotenv import load_dotenv

load_dotenv()
LOCAL = os.environ.get("LOCAL")


current_ip = None
changeCount = 0

if LOCAL:
    print("Using Tor")
    initialize_environment()
    current_ip = ma_ip()
    changeCount = 1    


def changeIP():
    global current_ip, changeCount
    current_ip = change_ip()
    while db.ipExists(current_ip):
        print(
            f"{changeCount:02}. IP: {current_ip} already exists in database, changing IP"
        )
        current_ip = change_ip()
        changeCount += 1
        print("Current IP:", current_ip)
