from helper import findLastSubmissionID, login, getRequest, printIpAddress
import sqlite3
import asyncio
import time
import os

from scraper import getSubmissionData


MAX_TIME = 5 * 60  # 5 minutes
os.makedirs("submissions", exist_ok=True)

class LocalSQLite:
    def __init__(self):
        self.conn = None
        self.cur = None

    def __enter__(self):
        self.conn = sqlite3.connect("submissions/data")
        self.cur = self.conn.cursor()
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY,
                time INTEGER NOT NULL,
                user TEXT NOT NULL,
                problem TEXT NOT NULL,
                language TEXT NOT NULL,
                status TEXT NOT NULL,
                exTime TEXT NOT NULL,
                memoryUsage TEXT NOT NULL,
                sourceSize TEXT NOT NULL
            )
            """
        )
        self.conn.commit()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def addSubmission(self, data: dict):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())
        self.cur.execute(
            f"INSERT OR REPLACE INTO submissions ({columns}) VALUES ({placeholders})",
            values,
        )
        self.conn.commit()
        print(f"Stored ID: {data['id']}\r", end="")

    def getSubmission(self, id: int):
        self.cur.execute("SELECT * FROM submissions WHERE id = ?", (id,))
        row = self.cur.fetchone()
        return row

    def getAllIDs(self):
        self.cur.execute("SELECT id FROM submissions")
        present_ids = {row[0] for row in self.cur.fetchall()}
        return present_ids

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


def makeData(values: list):
    id, xtime, user, problem, language, status, exTime, memoryUsage, sourceSize = values
    d = {
        "id": id,
        "time": xtime,
        "user": user,
        "problem": problem,
        "language": language,
        "status": status,
        "exTime": exTime,
        "memoryUsage": memoryUsage,
        "sourceSize": sourceSize,
    }
    return d


async def main(missing: list[int], db: LocalSQLite):
    sTime = time.time()

    printIpAddress()
    try:
        await login()
    except Exception as e:
        if "login failed" in str(e).lower():
            print(f"Login Failed. Exiting...")
            exit(1)

    def getDelTime():
        return f"{(time.time() - sTime)/60:.2f}"

    errCount = 0
    for sub in missing:
        if (errCount > 2) or (time.time() - sTime > MAX_TIME):
            return "Meow. End"

        try:
            res = await getRequest(f"https://toph.co/s/{sub}")
            data = getSubmissionData(res)
            data = makeData(data)
            db.addSubmission(data)
            time.sleep(0.3)
            print(f"{getDelTime()} Added submission: {data['id']}")

        except Exception as e:
            print()
            print("Exiting...")
            print(f"Error: {e}\n")
            print(f"DelTime : {getDelTime()} minutes")
            print(f"ErrCount: {errCount}")
            errCount += 1


with LocalSQLite() as db:
    n = findLastSubmissionID()
    currentIDs = set(db.getAllIDs())
    missing = [i for i in range(1, n + 1) if i not in currentIDs]
    asyncio.run(main(missing, db))


