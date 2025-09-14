from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

from dotenv import load_dotenv
import os, json

load_dotenv()

uri = os.getenv("MONGOURI")


class Database:
    def __init__(self, ver: str = None):
        client = MongoClient(uri, server_api=ServerApi("1"))
        db = client.subs_local
        self.stats = db.stats
        self.submissions = db.submissions

    def addSubmission(self, data: dict):
        subID = data[0]
        self.submissions.insert_one({"_id": subID, "d": data})

if __name__ == "__main__":
    db = Database()
    print(db.stats.find_one())