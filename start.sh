#!/bin/bash

# Render deployment start script
echo "Starting Forex Analyzer Platform..."
echo "Current directory: $(pwd)"
echo "Contents:"
ls -la

# Change to backend directory and start server
cd backend
echo "Now in backend directory: $(pwd)"
echo "Backend contents:"
ls -la

# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}