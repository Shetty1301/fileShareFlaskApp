# models.py

import datetime
from pymongo import IndexModel, ASCENDING, DESCENDING

def create_indexes(db):
    """Create necessary indexes for MongoDB collections"""
    # User collection indexes
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True)
    
    # Files collection indexes
    db.files.create_index([("alias", ASCENDING)], unique=True)
    db.files.create_index([("user_id", ASCENDING)])
    db.files.create_index([("created_at", ASCENDING)])
    db.files.create_index([("email", ASCENDING)])  # Add index for email search
    
class User:
    """User model for authentication and file ownership"""
    
    @staticmethod
    def create(db, username, email, password):
        """Create a new user"""
        user = {
            "username": username,
            "email": email,
            "password": password,  # Store password as plaintext as requested
            "created_at": datetime.datetime.utcnow()
        }
        
        result = db.users.insert_one(user)
        user["_id"] = result.inserted_id
        
        return user
    
    @staticmethod
    def get_by_email(db, email):
        """Get user by email"""
        return db.users.find_one({"email": email})
    
    @staticmethod
    def get_by_id(db, user_id):
        """Get user by ID"""
        from bson.objectid import ObjectId
        return db.users.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def check_password(user, password):
        """Verify password"""
        return user['password'] == password  # Direct comparison as requested


class File:
    """File model for uploaded files"""
    
    @staticmethod
    def create(db, filename, original_filename, file_size, alias, password, download_limit, user_id=None, email=None):
        """Create a new file record"""
        expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=3)
        
        file = {
            "filename": filename,
            "original_filename": original_filename,
            "file_size": file_size,
            "alias": alias,
            "password": password,  # Store password as plaintext as requested
            "download_limit": download_limit,
            "download_count": 0,
            "user_id": user_id,
            "email": email,  # Store email for later retrieval
            "created_at": datetime.datetime.utcnow(),
            "expires_at": expiration_date
        }
        
        result = db.files.insert_one(file)
        file["_id"] = result.inserted_id
        
        return file
    
    @staticmethod
    def get_by_alias(db, alias):
        """Get file by alias"""
        return db.files.find_one({"alias": alias})
    
    @staticmethod
    def get_user_files(db, user_id):
        """Get all files uploaded by a user"""
        from bson.objectid import ObjectId
        return list(db.files.find({"user_id": ObjectId(user_id)}))
    
    @staticmethod
    def get_by_email(db, email):
        """Get all files uploaded with a specific email"""
        return list(db.files.find({"email": email}))
    
    @staticmethod
    def increment_download_count(db, file_id):
        """Increment download count for a file"""
        from bson.objectid import ObjectId
        db.files.update_one(
            {"_id": ObjectId(file_id)},
            {"$inc": {"download_count": 1}}
        )
        return db.files.find_one({"_id": ObjectId(file_id)})
    
    @staticmethod
    def delete(db, file_id):
        """Delete a file record"""
        from bson.objectid import ObjectId
        return db.files.delete_one({"_id": ObjectId(file_id)})
    
    @staticmethod
    def delete_expired_files(db):
        """Delete files that have reached download limit or expired"""
        # Find files that have reached download limit or expired
        expired_files = list(db.files.find({
            "$or": [
                {"download_count": {"$gte": "$download_limit"}},
                {"expires_at": {"$lt": datetime.datetime.utcnow()}}
            ]
        }))
        
        # Delete the files from database
        file_ids = [file["_id"] for file in expired_files]
        if file_ids:
            db.files.delete_many({"_id": {"$in": file_ids}})
        
        return expired_files