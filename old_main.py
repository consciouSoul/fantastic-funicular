import os
import asyncio
import time
import sys
import json
from pymongo.errors import DuplicateKeyError
from database import Database

from helper import login, getRequest, printIpAddress
from scraper import getSubmissionData


pythonVersion = f"{sys.version_info.major}.{sys.version_info.minor}"  # e.g., 3.10
db = Database(ver=pythonVersion)
START = 1
END = 1800000
BATCH_SIZE = 1
PROGRESS_FILE = "data/metadata_progress.json"


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_processed", START)

    return START


def save_progress(last_processed: int):
    os.makedirs("data", exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_processed": last_processed}, f)


async def fetch():
    START = load_progress() + 1
    print(f"Fetching from {START} to {END}, ({END - START} submissions)")

    
    for i in range(START, END+1):
        url = f"https://toph.co/s/{i}"
        res = await getRequest(url)
        data = getSubmissionData(res)
        try:
            db.addSubmission(data)
        except DuplicateKeyError as e:
            print(f"Duplicate entry for submission ID {data[0]}, skipping.")
            
        save_progress(i)
        time.sleep(0.1)
        print(f"Fetched {i} submissions", end="\r")

    startTime = time.time()

    endTime = time.time()

    print(f"\nTime taken: {endTime - startTime:.2f}s")


async def fetchNewSubmissions():
    printIpAddress()
    while 1:
        try:
            await login()
            await fetch()
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)


async def main():
    print(f"Python Version: {pythonVersion}")
    await fetchNewSubmissions()


if __name__ == "__main__":
    asyncio.run(main())
