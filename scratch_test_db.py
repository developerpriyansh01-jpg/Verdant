import os
from pymongo import MongoClient

# Parse .env
def load_env():
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

uri = os.environ.get("MONGODB_URI", "mongodb+srv://dinesh:mehukon@cluster0.rksaqdu.mongodb.net/?appName=Cluster0")
print("Connecting to:", uri)
try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    db = client.get_database("VerdantDB")
    print("Databases:", client.list_database_names())
    print("Users count:", db.users.count_documents({}))
    print("Success!")
except Exception as e:
    print("Failed to connect:", e)
