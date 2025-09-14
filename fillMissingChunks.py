from helper import findLastSubmissionID, login, getRequest, printIpAddress
import sqlite3
import asyncio
import time
import os

from scraper import getSubmissionData


MAX_TIME = 5 * 60
folder = "dataFiles"
os.makedirs(folder, exist_ok=True)


class LocalSQLite:
    def __init__(self, dbFilePath: str = "submissions/data"):
        self.conn = None
        self.cur = None
        self.dbFilePath = dbFilePath
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.dbFilePath)
        self.cur = self.conn.cursor()
        self.cur.execute("PRAGMA synchronous = OFF")
        self.cur.execute("PRAGMA journal_mode = MEMORY")
        self.cur.execute("PRAGMA cache_size = 10000")
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

    def addSubmission(self, data):
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())
        self.cur.execute(
            f"INSERT OR REPLACE INTO submissions ({columns}) VALUES ({placeholders})",
            values,
        )
        self.conn.commit()
        print(f"Stored ID: {data['id']}\r", end="")

    def addSubmissionsBatch(self, data_list):
        if not data_list:
            return
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?" for _ in data_list[0]])
        values_list = [tuple(data.values()) for data in data_list]
        self.cur.executemany(
            f"INSERT OR REPLACE INTO submissions ({columns}) VALUES ({placeholders})",
            values_list,
        )
        self.conn.commit()

    def getSubmission(self, id):
        self.cur.execute("SELECT * FROM submissions WHERE id = ?", (id,))
        row = self.cur.fetchone()
        return row

    def getSubmissions(self, ids):
        placeholders = ", ".join(["?" for _ in ids])
        self.cur.execute(f"SELECT * FROM submissions WHERE id IN ({placeholders})", ids)
        return self.cur.fetchall()

    def getAllIDs(self):
        self.cur.execute("SELECT id FROM submissions")
        present_ids = [row[0] for row in self.cur.fetchall()]
        return present_ids

    def getTotalLength(self):
        self.cur.execute("SELECT COUNT(*) FROM submissions")
        count = self.cur.fetchone()[0]
        return count

    def getLastID(self):
        self.cur.execute("SELECT MAX(id) FROM submissions")
        last_id = self.cur.fetchone()[0]
        return last_id

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


def makeData(values):
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


maxPerFile = 100_000


async def main():
    files = [f for f in os.listdir(folder) if f.endswith(".db")]
    if not files:
        lastDBNumber = 1
        print("No database files found! Starting with 1.db")
    else:
        try:
            lastDBNumber = max(int(i.split(".")[0]) for i in files)
            print(f"Last DB: {lastDBNumber}.db")
        except ValueError:
            print("Error: Invalid database file names found!")
            return

    try:
        printIpAddress()
        await login()
        print("Login successful!")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    try:
        n = findLastSubmissionID()
    except Exception as e:
        print(f"Error getting latest submission ID: {e}")
        return

    print()
    db = LocalSQLite(f"{folder}/{lastDBNumber}.db")
    try:
        lastStoredID = db.getLastID()
        if lastStoredID is None:
            lastStoredID = 0
        print(f"Last stored ID: {lastStoredID}")
    except Exception as e:
        print(f"Error getting last stored ID: {e}")
        db.close()
        return

    if lastStoredID >= n:
        print("Database is already up to date!")
        db.close()
        return

    missing = list(range(lastStoredID + 1, n + 1))
    print(f"Missing submissions: {len(missing)} ({lastStoredID + 1} to {n})")

    sTime = time.time()

    def getDelTime():
        return f"{(time.time() - sTime)/60:.2f}"

    errCount = 0
    processedCount = 0

    for sub in missing:
        if errCount > 2:
            print(f"\nStopping: Too many errors ({errCount})")
            break

        if time.time() - sTime > MAX_TIME:
            print(f"\nStopping: Time limit reached ({getDelTime()} min)")
            break

        try:
            res = await getRequest(f"https://toph.co/s/{sub}")
            data = getSubmissionData(res)
            data = makeData(data)
            if "queued" in data['status'].lower():
                print("Reached to a `queued` submission. Exiting...")
                break
            
            db.addSubmission(data)
            processedCount += 1

            if db.getTotalLength() >= maxPerFile:
                db.close()
                lastDBNumber += 1
                db = LocalSQLite(f"{folder}/{lastDBNumber}.db")
                print(f"\nNew DB created: {lastDBNumber}.db")

            await asyncio.sleep(0.3)
            print(
                f"{getDelTime()}m | Progress: {processedCount}/{len(missing)} | Added: {data['id']}"
            )
            errCount = 0

        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            errCount += 1
            print(f"\nError processing ID {sub}: {e}")
            print(f"DelTime: {getDelTime()}m | ErrCount: {errCount}")

            if errCount <= 2:
                await asyncio.sleep(1)

    db.close()
    print(
        f"\nCompleted! Processed: {processedCount}/{len(missing)} | Time: {getDelTime()}m"
    )


if __name__ == "__main__":
    asyncio.run(main())
