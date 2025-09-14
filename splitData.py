import sqlite3
import os
import time
import json

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
        self.cur.execute(f"INSERT OR REPLACE INTO submissions ({columns}) VALUES ({placeholders})", values)
        self.conn.commit()
        print(f"Stored ID: {data['id']}\r", end="")
    
    def addSubmissionsBatch(self, data_list):
        if not data_list:
            return
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?" for _ in data_list[0]])
        values_list = [tuple(data.values()) for data in data_list]
        self.cur.executemany(f"INSERT OR REPLACE INTO submissions ({columns}) VALUES ({placeholders})", values_list)
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
batchSize = 1000
dbCount = 1
subCount = 0

db = LocalSQLite()
currentIDs = db.getAllIDs()
newDB = LocalSQLite(f"{folder}/test_{dbCount}.db")

startTime = time.time()
lastTime = startTime
totalRecords = len(currentIDs)

for i in range(0, len(currentIDs), batchSize):
    batchIds = currentIDs[i:i + batchSize]
    batchValues = db.getSubmissions(batchIds)
    batchData = [makeData(values) for values in batchValues]
    
    newDB.addSubmissionsBatch(batchData)
    subCount += len(batchData)
    
    currentTime = time.time()
    if currentTime - lastTime >= 1.0:
        elapsed = currentTime - startTime
        rate = subCount / elapsed if elapsed > 0 else 0
        print(f"DB: {dbCount}, Stored: {subCount}, Rate: {rate:.0f}/sec")
        lastTime = currentTime
    
    if subCount >= maxPerFile * dbCount:
        dbCount += 1
        newDB.close()
        newDB = LocalSQLite(f"{folder}/test_{dbCount}.db")
        print(f"New DB created. DB Count: {dbCount}, Sub Count: {subCount}")

db.close()
newDB.close()

endTime = time.time()
totalTime = endTime - startTime
finalRate = subCount / totalTime if totalTime > 0 else 0
print(f"Completed! Total: {subCount}, Time: {totalTime:.2f}s, Rate: {finalRate:.0f}/sec")