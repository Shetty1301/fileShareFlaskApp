# routes.py

from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_jwt_extended import (
    jwt_required, create_access_token, 
    get_jwt_identity
)
from app import db
from app.models import User, File
from app.utils import (
    save_file, remove_file,
    generate_download_link, get_unique_alias
)
import os
from bson.objectid import ObjectId
import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def home():
    """Home route"""
    return jsonify({"message": "Welcome to the File Upload API!"}), 200

@main_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['username', 'email', 'password']):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if user already exists
    existing_user = User.get_by_email(db, data['email'])
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409
    
    # Create new user
    try:
        user = User.create(db, data['username'], data['email'], data['password'])
        
        # Generate access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "email": user['email']
            }
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['email', 'password']):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if user exists
    user = User.get_by_email(db, data['email'])
    if not user or not User.check_password(user, data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Generate access token
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user['_id']),
            "username": user['username'],
            "email": user['email']
        }
    }), 200

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file with or without user authentication"""
    # Check if user is authenticated
    user_id = None
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        try:
            from flask_jwt_extended import decode_token
            token = auth_header.split(' ')[1]
            user_claims = decode_token(token)
            user_id = user_claims['sub']  # User ID from JWT
        except Exception:
            # If token is invalid, proceed as anonymous upload
            pass
    
    # Check if file is included in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Get form data
    alias = request.form.get('alias', '')
    password = request.form.get('password', '')
    email = request.form.get('email', '')
    download_limit = request.form.get('downloadLimit', 10)
    
    try:
        download_limit = int(download_limit)
    except ValueError:
        download_limit = 10  # Default if invalid
    
    # Save file to uploads directory
    unique_filename, original_filename, file_size, file_path = save_file(file)
    
    if not unique_filename:
        return jsonify({"error": "Invalid file type"}), 400
    
    # Get a unique alias - modified to handle the exception
    try:
        alias = get_unique_alias(db, alias)
    except ValueError as e:
        # If the alias is already in use, delete the uploaded file and return an error
        if unique_filename:
            remove_file(unique_filename)
        return jsonify({"error": str(e)}), 409  # 409 Conflict is appropriate for this case
    
    # Create file record in database
    try:
        user_id_obj = ObjectId(user_id) if user_id else None
        file_record = File.create(
            db, 
            unique_filename,
            original_filename,
            file_size,
            alias,
            password,  # Store password as plaintext as requested
            download_limit,
            user_id_obj,
            email  # Added email parameter
        )
        
        # Generate download link
        download_link = generate_download_link(alias,password)
        
        return jsonify({
            "message": "File uploaded successfully",
            "download_link": download_link,
            "alias": alias,
            "original_filename": original_filename,
            "download_limit": download_limit,
            "expires_at": file_record["expires_at"].isoformat()
        }), 201
    except Exception as e:
        # Remove file if database operation fails
        if unique_filename:
            remove_file(unique_filename)
        return jsonify({"error": str(e)}), 500

@main_bp.route('/<alias>', methods=['GET'])
def download_file(alias):
    """Download a file using its alias and password"""
    # Get password from query parameter
    password = request.args.get('password', '')
    
    # Get file record from database
    file_record = File.get_by_alias(db, alias)
    
    if not file_record:
        return jsonify({"error": "File not found"}), 404
    
    # Check if file has reached download limit
    if file_record['download_count'] >= file_record['download_limit']:
        # Remove file from storage
        remove_file(file_record['filename'])
        # Delete record from database
        File.delete(db, file_record['_id'])
        return jsonify({"error": "Download limit reached"}), 404
    
    # Check if file has expired
    if datetime.datetime.utcnow() > file_record['expires_at']:
        # Remove file from storage
        remove_file(file_record['filename'])
        # Delete record from database
        File.delete(db, file_record['_id'])
        return jsonify({"error": "File has expired"}), 404
    
    # Verify password (direct comparison as requested)
    if file_record['password'] != password:
        return jsonify({"error": "Incorrect password"}), 401
    
    # Increment download count
    updated_file = File.increment_download_count(db, file_record['_id'])
    
    # Check if this download has reached the limit
    if updated_file['download_count'] >= updated_file['download_limit']:
        # Schedule file for deletion in a real app
        pass
    
    # Serve the file directly
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            file_record['filename'],
            as_attachment=True,
            download_name=file_record['original_filename']
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/my-uploads', methods=['GET'])
@jwt_required()
def get_user_uploads():
    """Get all files uploaded by the authenticated user"""
    user_id = get_jwt_identity()
    
    try:
        files = File.get_user_files(db, user_id)
        
        # Format files for response
        formatted_files = []
        for file in files:
            formatted_files.append({
                "id": str(file['_id']),
                "alias": file['alias'],
                "original_filename": file['original_filename'],
                "download_count": file['download_count'],
                "download_limit": file['download_limit'],
                "file_size": file['file_size'],
                "created_at": file['created_at'].isoformat(),
                "expires_at": file['expires_at'].isoformat(),
                "download_link": generate_download_link(file['alias'])
            })
        
        return jsonify({"files": formatted_files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/delete-by-email/<file_id>', methods=['DELETE'])
def delete_file_by_email(file_id):
    """Delete a file uploaded with a specific email"""
    email = request.args.get('email', '')
    
    if not email:
        return jsonify({"error": "Email parameter is required"}), 400
    
    try:
        # Get file record
        file_record = db.files.find_one({
            "_id": ObjectId(file_id),
            "email": email
        })
        
        if not file_record:
            return jsonify({"error": "File not found or not authorized"}), 404
        
        # Remove file from storage
        remove_file(file_record['filename'])
        
        # Delete record from database
        File.delete(db, file_id)
        
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/my-uploads/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_user_upload(file_id):
    """Delete a file uploaded by the authenticated user"""
    user_id = get_jwt_identity()
    
    try:
        # Get file record
        file_record = db.files.find_one({
            "_id": ObjectId(file_id),
            "user_id": ObjectId(user_id)
        })
        
        if not file_record:
            return jsonify({"error": "File not found or not authorized"}), 404
        
        # Remove file from storage
        remove_file(file_record['filename'])
        
        # Delete record from database
        File.delete(db, file_id)
        
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/files-by-email', methods=['GET'])
def get_files_by_email():
    """Get all files uploaded with a specific email"""
    email = request.args.get('email', '')
    
    if not email:
        return jsonify({"error": "Email parameter is required"}), 400
    
    try:
        # Find files with the specified email
        files = list(db.files.find({"email": email}))
        
        # Format files for response
        formatted_files = []
        for file in files:
            formatted_files.append({
                "id": str(file['_id']),
                "alias": file['alias'],
                "original_filename": file['original_filename'],
                "download_count": file['download_count'],
                "download_limit": file['download_limit'],
                "created_at": file['created_at'].isoformat(),
                "expires_at": file['expires_at'].isoformat(),
                "download_link": generate_download_link(file['alias'])
            })
        
        return jsonify({"files": formatted_files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/cleanup', methods=['POST'])
def cleanup_expired_files():
    """Admin route to clean up expired files"""
    # In a real app, this would be protected by admin authentication
    # or triggered by a scheduled job
    
    try:
        expired_files = File.delete_expired_files(db)
        
        # Delete files from storage
        for file in expired_files:
            remove_file(file['filename'])
        
        return jsonify({
            "message": f"Cleaned up {len(expired_files)} expired files"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500