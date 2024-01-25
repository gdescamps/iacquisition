#!/bin/bash
# Navigate to the subfolder where the FastAPI application is located
cd projet

# Install the Python dependencies from the requirements.txt file
#pip install -r requirements.txt

# Start Gunicorn with Uvicorn workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --preload
