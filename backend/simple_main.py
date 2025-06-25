"""
Simple FastAPI Application for Forex Trading Analysis Platform
Basic working version for deployment testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

# Create FastAPI application
app = FastAPI(
    title="Forex Trading Analysis Platform",
    description="Modular platform for analyzing forex trading data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint returning a basic HTML interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Forex Trading Analysis Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }
            .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
            .status { background: #27ae60; color: white; padding: 10px; border-radius: 5px; text-align: center; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 30px; }
            .feature { background: #ecf0f1; padding: 20px; border-radius: 8px; }
            .api-link { background: #3498db; color: white; padding: 10px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Forex Trading Analysis Platform</h1>
                <p>Modular platform for analyzing forex trading data with ML-powered insights</p>
            </div>
            
            <div class="status">
                ✅ Platform Successfully Deployed!
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>📊 Data Processing</h3>
                    <p>Upload and analyze MT5/MT4 trading history files</p>
                </div>
                <div class="feature">
                    <h3>🤖 ML Analysis</h3>
                    <p>Advanced pattern recognition and predictive modeling</p>
                </div>
                <div class="feature">
                    <h3>🔌 Plugin System</h3>
                    <p>Extensible architecture with custom analysis modules</p>
                </div>
                <div class="feature">
                    <h3>📱 Mobile Ready</h3>
                    <p>Responsive design optimized for all devices</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/health" class="api-link">Health Check</a>
                <a href="/api/docs" class="api-link">API Documentation</a>
                <a href="/api/v1/test" class="api-link">Test Endpoint</a>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>🔗 Next Steps:</h3>
                <ul>
                    <li>Upload your MT5/MT4 trading history CSV files</li>
                    <li>Access the API documentation for integration</li>
                    <li>Explore the plugin system for custom analysis</li>
                    <li>View ML-powered trading insights and recommendations</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "forex-analyzer",
        "version": "1.0.0",
        "environment": os.getenv("RENDER_SERVICE_NAME", "development")
    }

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint for API functionality"""
    return {
        "message": "Forex Trading Analysis Platform API is working!",
        "features": [
            "Data upload and processing",
            "ML-powered analysis",
            "Plugin system",
            "Trading insights generation"
        ],
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)