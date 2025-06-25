#!/bin/bash

# Simple start script for Render deployment
echo "Starting Forex Analyzer Platform..."

# Check if we're in the right directory
pwd
ls -la

# Start the backend server directly (skip frontend build for now)
echo "Starting FastAPI server..."
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}