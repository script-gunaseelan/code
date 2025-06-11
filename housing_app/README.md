# Housing Application Portal

This folder contains a minimal Flask application that demonstrates a simple affordable housing application portal.

## Features
- User signup and login
- Submit a housing application with a file upload
- Submitted data and files are sent to a configured webhook

## Running
1. Create a virtual environment and install the requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Set the `WEBHOOK_URL` environment variable to the endpoint that should receive the application data.
3. Run the application:
   ```bash
   python app.py
   ```
4. Access `http://localhost:5000` in your browser.

Uploaded files are stored in the `uploads/` directory. The SQLite database file `housing.db` is created automatically.
