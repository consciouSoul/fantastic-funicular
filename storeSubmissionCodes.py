import httpx
import asyncio
import json
import os
from typing import Tuple
from localDB import LocalSQLite
from tqdm.asyncio import tqdm
from dotenv import load_dotenv

START = 1
END = 1791585
PROGRESS_FILE = "data/progress.json"
PASS = str(os.environ.get("PASS")).strip()


db = LocalSQLite("3.19")


def load_progress():
    last_db_id = db.getLastSubmissionId()
    if last_db_id:
        return last_db_id
    
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_processed", START - 1)
    return START - 1


def save_progress(last_processed):
    os.makedirs("data", exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_processed": last_processed}, f)


async def login(c: httpx.AsyncClient) -> bool:
    data = {
        "handle": "Immigrant",
        "password": PASS,
    }
    r = await c.post("https://toph.co/login", data=data)
    status = r.status_code
    print(
        "Logged in successfully" if status == 200 else "Failed to login",
        status,
    )
    return status == 200


async def fetch_submission(c: httpx.AsyncClient, i: int) -> Tuple[int, str, bool]:
    url = f"https://toph.co/s/{i}/source"
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            r = await c.get(url)
            
            if r.status_code == 429:
                print(f"Rate limit hit for submission {i}. Exiting.")
                exit(1)

            if r.status_code == 200:
                return i, r.text, True
            else:
                return i, "", False
                
        except httpx.HTTPError as e:
            if attempt < max_retries - 1:
                print(f"\nNetwork error for submission {i}, attempt {attempt + 1}/{max_retries}. Error: {e}")
                print(f"Waiting {retry_delay} seconds before retrying...")
                await asyncio.sleep(retry_delay)
                continue
            else:
                print(f"\nMax retries reached for submission {i}. Network error: {e}")
                return i, "", False


async def main():
    os.makedirs("submissions", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    last_processed = load_progress()
    resume_start = last_processed + 1

    if resume_start > START:
        print(f"Resuming from submission {resume_start}")

    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

    total_submissions = END - max(START, resume_start) + 1

    async with httpx.AsyncClient(
        timeout=timeout, limits=limits, follow_redirects=True
    ) as c:
        if not await login(c):
            return

        failed = []

        pbar = tqdm(
            range(max(START, resume_start), END + 1),
            desc="Processing submissions",
            unit="submission",
            total=total_submissions,
        )

        try:
            for i in pbar:
                while True:
                    try:
                        submission_id, content, success = await fetch_submission(c, i)
                        
                        if success:
                            db.storeCode(submission_id, content)
                        else:
                            failed.append(submission_id)
                        
                        save_progress(i)
                        pbar.set_postfix({"current": i, "failed": len(failed)})
                        break
                        
                    except Exception as e:
                        print(f"\nRetrying submission {i} due to error: {e}")
                        await asyncio.sleep(5)

                await asyncio.sleep(0.35)

        except KeyboardInterrupt:
            print(f"\nInterrupted. Progress saved. Resume from {i}")
        except Exception as e:
            print(f"\nError: {e}. Progress saved. Resume from {i}")

        if failed:
            with open("data/failed_submissions.json", "w") as f:
                json.dump(failed, f)


if __name__ == "__main__":
    asyncio.run(main())