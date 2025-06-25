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

# Start the simple FastAPI server (fallback to complex if available)
if [ -f "simple_main.py" ]; then
    echo "Starting with simple_main.py..."
    python -m uvicorn simple_main:app --host 0.0.0.0 --port ${PORT:-8000}
else
    echo "Starting with app.main..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi