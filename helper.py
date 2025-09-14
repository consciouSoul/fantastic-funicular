import os
import httpx
import asyncio
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

LOCAL = os.environ.get("LOCAL")
PASS = str(os.environ.get("PASS")).strip()


print(f"Pass len: {len(PASS)}")

ses = httpx.AsyncClient(
    timeout=10,
    follow_redirects=True,
)


def makeFolder(folderName: str):
    if not os.path.exists(folderName):
        os.makedirs(folderName)


def printIpAddress():
    r = httpx.get("https://contest-hive.vercel.app/api/others/stats", timeout=10).json()["ip"]
    print(f"IP: {r}\n\n")


def findLastSubmissionID():
    url = "https://toph.co/submissions"
    r = httpx.get(url, timeout=10)
    soup = BeautifulSoup(r.content, "lxml")
    soup = soup.find("tbody").find("tr", class_="syncer").find("td").text
    print(f"Last Submission ID: {soup}")
    return int(soup)


async def login():
    data = {
        "handle": "Immigrant",
        "password": PASS,
    }
    response = await ses.post("https://toph.co/login", data=data)
    status = response.status_code
    
    if data["handle"].lower() not in response.text.lower() and status != 429:
        status = 400
        
    print(
        "Logged in successfully" if status == 200 else "Failed to login",
        status,
    )
    if status != 200:
        raise Exception("Login failed. Exiting...")


async def getRequest(url: str):
    response = await ses.get(url)
    return response


async def makeBulkRequest(urls, per: int = 100, sleep: int = 0):
    total = len(urls)
    done = []
    while urls:
        tasks = [getRequest(url) for url in urls[:per]]
        urls = urls[per:]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        done.extend(responses)
        print(f"Done {len(done)}/{total}\r", end="")
        if sleep:
            await asyncio.sleep(sleep)
    print()

    return done
