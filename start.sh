#!/bin/bash

# Full-stack start script for Render deployment
echo "Starting Forex Analyzer Platform..."

# Frontend dependencies should already be installed by Render's Node.js detection
# Build frontend
echo "Building frontend..."
cd frontend
npm run build

# Copy built frontend to backend static directory
echo "Setting up static files..."
mkdir -p ../backend/static
cp -r build/* ../backend/static/

# Start the backend server (which will also serve the frontend)
echo "Starting server..."
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}