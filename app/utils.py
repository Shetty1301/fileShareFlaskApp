# utils.py

import os
import datetime
import string
import random
from werkzeug.utils import secure_filename
from flask import current_app, url_for

def allowed_file(filename):
    """Check if file extension is allowed"""
    # Add or remove extensions as needed
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """Generate a unique filename for storage"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Keep the original file extension
    _, file_extension = os.path.splitext(original_filename)
    
    return f"{timestamp}_{random_str}{file_extension}"

def save_file(file):
    """Save file to the uploads directory"""
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        return unique_filename, original_filename, file_size, file_path
    
    return None, None, None, None

def remove_file(filename):
    """Remove a file from the uploads directory"""
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def generate_download_link(alias, password):
    """Generate a download link for a file"""
    base_url = "http://localhost:5000/"+alias+"?password="+password 
    return base_url

def is_alias_unique(db, alias):
    """Check if an alias is unique in the database"""
    existing_file = db.files.find_one({"alias": alias})
    return existing_file is None

def generate_random_alias(length=8):
    """Generate a random alias for a file"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def get_unique_alias(db, preferred_alias=None):
    """Get a unique alias, validate preferred alias or generate a random one"""
    if preferred_alias:
        # Clean up the preferred alias (alphanumeric and underscores only)
        clean_alias = ''.join(c for c in preferred_alias if c.isalnum() or c == '_')
        
        if clean_alias:
            # Check if the alias is already in use
            if not is_alias_unique(db, clean_alias):
                # If alias is taken, raise an exception instead of generating a random one
                raise ValueError("Alias already in use")
            return clean_alias
    
    # Generate a random alias only if no preferred alias was specified
    while True:
        random_alias = generate_random_alias()
        if is_alias_unique(db, random_alias):
            return random_alias