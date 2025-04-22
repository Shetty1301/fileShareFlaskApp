

# Flask File Sharing Application

A secure file sharing application built with Flask and MongoDB that allows users to upload files with password protection and download limits.

## Features

- Upload files with or without user authentication
- Set custom aliases for files
- Password protect file downloads
- Set download limits for files
- Automatic file expiration after 3 days
- User registration and login system
- View and manage your uploaded files

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- MongoDB Atlas account
- pip (Python package installer)

### Environment Setup

1. Clone the repository:

```
git clone <repository-url>
cd flask_file_share
```

2. Create a virtual environment:

```
python -m venv venv
```

3. Activate the virtual environment:

- On Windows:
```
venv\Scripts\activate
```

- On macOS/Linux:
```
source venv/bin/activate
```

4. Install dependencies:

```
pip install -r requirements.txt
```

### MongoDB Atlas Configuration

1. Create a MongoDB Atlas account if you don't have one
2. Create a new cluster
3. Create a database user with read/write permissions
4. Get your MongoDB connection string

### Application Configuration

1. Create a `.env` file in the project root directory:

```
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key
MONGO_URI=your_mongodb_connection_string
```

Replace `your_secret_key`, `your_jwt_secret_key`, and `your_mongodb_connection_string` with your actual values.

### Running the Application

1. Run the application:

```
python run.py
```

2. The Flask server will start at `http://localhost:5000`

## API Endpoints

### Authentication

- `POST /api/register` - Register a new user
- `POST /api/login` - Login a user

### File Operations

- `POST /api/upload` - Upload a file (with or without authentication)
- `GET /api/download/<alias>` - Get file information by alias
- `POST /api/download/<alias>` - Verify password and prepare for download
- `GET /api/download/<alias>/file?token=<token>` - Download the file with a valid token
- `GET /api/my-uploads` - Get all files uploaded by the authenticated user
- `DELETE /api/my-uploads/<file_id>` - Delete a file uploaded by the authenticated user

### Maintenance

- `POST /api/cleanup` - Clean up expired files (admin/scheduled job)

## Frontend Integration

This backend is designed to work with a ReactJS frontend. All API endpoints return JSON responses that can be easily consumed by the React application.

## Security Considerations

- File passwords are securely hashed using bcrypt
- JWT authentication for protected routes
- File size limits to prevent server overload
- Automatic cleanup of expired files