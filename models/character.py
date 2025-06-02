from pymongo import MongoClient

# Không cần schema như Mongoose, pymongo sử dụng trực tiếp collection
def get_character_collection(db):
    return db.characters