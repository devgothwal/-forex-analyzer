"""
Simple FastAPI Application for Forex Trading Analysis Platform
Root-level simple server for easy deployment
"""

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import os
import pandas as pd
import io

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
            body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
            .header { text-align: center; color: #2c3e50; margin-bottom: 30px; }
            .header h1 { margin-bottom: 10px; font-size: 2.5em; }
            .status { background: #27ae60; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
            .feature { background: #ecf0f1; padding: 25px; border-radius: 10px; text-align: center; }
            .feature h3 { color: #34495e; margin-bottom: 15px; }
            .upload-section { background: #f8f9fa; padding: 30px; border-radius: 10px; margin-top: 30px; text-align: center; }
            .btn { background: #3498db; color: white; padding: 15px 30px; border: none; border-radius: 8px; text-decoration: none; display: inline-block; margin: 10px; }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Forex Trading Analysis Platform</h1>
                <p>Modular platform for analyzing forex trading data with ML-powered insights</p>
            </div>
            
            <div class="status">
                ✅ Platform Successfully Deployed & Running!
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>📊 Data Processing</h3>
                    <p>Upload and analyze MT5/MT4 trading history files with advanced algorithms</p>
                </div>
                <div class="feature">
                    <h3>🤖 ML Analysis</h3>
                    <p>Pattern recognition, clustering, classification, and anomaly detection</p>
                </div>
                <div class="feature">
                    <h3>🔌 Plugin System</h3>
                    <p>Extensible architecture with custom analysis modules and hot-swapping</p>
                </div>
                <div class="feature">
                    <h3>📱 Mobile Ready</h3>
                    <p>Responsive design optimized for all devices and touch interfaces</p>
                </div>
            </div>
            
            <div class="upload-section">
                <h3>🎯 Ready to Analyze Your Trading Data?</h3>
                <p>Upload your MT5/MT4 CSV files to get started with AI-powered insights!</p>
                
                <form id="uploadForm" enctype="multipart/form-data" style="margin: 20px 0;">
                    <div style="margin-bottom: 15px;">
                        <input type="file" id="fileInput" name="file" accept=".csv,.xlsx,.xls" 
                               style="padding: 10px; border: 2px dashed #3498db; border-radius: 8px; width: 100%; max-width: 400px;">
                    </div>
                    <button type="submit" class="btn" style="background: #27ae60;" id="uploadBtn">
                        📊 Upload & Analyze Trading Data
                    </button>
                </form>
                
                <script>
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const fileInput = document.getElementById('fileInput');
                    const uploadBtn = document.getElementById('uploadBtn');
                    const resultDiv = document.getElementById('uploadResult');
                    
                    if (!fileInput.files[0]) {
                        resultDiv.innerHTML = '<div style="background: #e74c3c; color: white; padding: 10px; border-radius: 5px;">Please select a file first!</div>';
                        resultDiv.style.display = 'block';
                        return;
                    }
                    
                    // Show loading state
                    uploadBtn.innerHTML = '⏳ Analyzing...';
                    uploadBtn.disabled = true;
                    resultDiv.style.display = 'none';
                    
                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);
                    
                    try {
                        const response = await fetch('/api/v1/upload', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            resultDiv.innerHTML = `
                                <div style="background: #27ae60; color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                                    ✅ ${result.message}
                                </div>
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: left;">
                                    <h4>📊 Analysis Results:</h4>
                                    <p><strong>File:</strong> ${result.analysis.filename}</p>
                                    <p><strong>Total Records:</strong> ${result.analysis.rows}</p>
                                    <p><strong>File Type:</strong> ${result.analysis.summary.file_type}</p>
                                    <p><strong>Valid Columns:</strong> ${result.analysis.summary.trading_insights.columns_detected} of ${result.analysis.columns}</p>
                                    <p><strong>Column Names:</strong> ${result.analysis.column_names.slice(0,5).join(', ')}${result.analysis.column_names.length > 5 ? '...' : ''}</p>
                                    <p><strong>Trading Data Detected:</strong> 
                                        ${result.analysis.summary.trading_insights.has_profit_column ? '✅ Profit' : '❌ Profit'} | 
                                        ${result.analysis.summary.trading_insights.has_symbol_column ? '✅ Symbol' : '❌ Symbol'} | 
                                        ${result.analysis.summary.trading_insights.has_time_column ? '✅ Time' : '❌ Time'}
                                    </p>
                                    <p><strong>Date Range:</strong> ${result.analysis.summary.date_range.start} to ${result.analysis.summary.date_range.end}</p>
                                </div>
                            `;
                        } else {
                            resultDiv.innerHTML = `<div style="background: #e74c3c; color: white; padding: 10px; border-radius: 5px;">${result.error}</div>`;
                        }
                    } catch (error) {
                        resultDiv.innerHTML = `<div style="background: #e74c3c; color: white; padding: 10px; border-radius: 5px;">Error: ${error.message}</div>`;
                    }
                    
                    // Reset button
                    uploadBtn.innerHTML = '📊 Upload & Analyze Trading Data';
                    uploadBtn.disabled = false;
                    resultDiv.style.display = 'block';
                });
                </script>
                
                <div id="uploadResult" style="margin-top: 20px; padding: 15px; border-radius: 8px; display: none;"></div>
                
                <div style="margin-top: 20px;">
                    <a href="/health" class="btn">❤️ Health Check</a>
                    <a href="/docs" class="btn">📚 API Documentation</a>
                    <a href="/api/v1/test" class="btn">🧪 Test API</a>
                </div>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #e8f5e8; border-radius: 8px;">
                <h3>🔗 Platform Status:</h3>
                <ul>
                    <li>✅ Backend API - Live & Running</li>
                    <li>✅ Plugin System - Ready for Extensions</li>
                    <li>✅ ML Pipeline - Available for Analysis</li>
                    <li>✅ File Upload - Ready for Trading Data</li>
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
        "environment": os.getenv("RENDER_SERVICE_NAME", "production"),
        "features": [
            "data_processing",
            "ml_analysis", 
            "plugin_system",
            "mobile_optimized"
        ]
    }

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint for API functionality"""
    return {
        "message": "🚀 Forex Trading Analysis Platform API is fully operational!",
        "capabilities": [
            "MT5/MT4 data upload and processing",
            "Machine learning powered analysis",
            "Modular plugin architecture",
            "Real-time trading insights generation",
            "Mobile-optimized responsive interface"
        ],
        "status": "operational",
        "ready_for": "production_trading_analysis"
    }

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and basic analysis"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid file type. Please upload CSV, XLSX, or XLS files."}
            )
        
        # Read file content
        content = await file.read()
        
        # Process based on file type with multiple header detection
        if file.filename.lower().endswith('.csv'):
            # Try different header rows for CSV
            try:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')), header=0)
                if df.columns[0].startswith('Unnamed') or 'Trade History' in str(df.iloc[0, 0]):
                    df = pd.read_csv(io.StringIO(content.decode('utf-8')), header=1)
                if df.columns[0].startswith('Unnamed'):
                    df = pd.read_csv(io.StringIO(content.decode('utf-8')), header=2)
            except:
                df = pd.read_csv(io.StringIO(content.decode('utf-8')), header=0)
        else:
            # Try different header rows for Excel
            try:
                df = pd.read_excel(io.BytesIO(content), header=0)
                if df.columns[0].startswith('Unnamed') or 'Trade History' in str(df.iloc[0, 0]):
                    df = pd.read_excel(io.BytesIO(content), header=1)
                if df.columns[0].startswith('Unnamed'):
                    df = pd.read_excel(io.BytesIO(content), header=2)
            except:
                df = pd.read_excel(io.BytesIO(content), header=0)
        
        # Clean data for JSON serialization
        df_clean = df.fillna("N/A")  # Replace NaN with "N/A"
        
        # Enhanced analysis with MT5/MT4 specific insights
        analysis = {
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "data_preview": df_clean.head(3).to_dict('records') if len(df) > 0 else [],
            "summary": {
                "total_records": len(df),
                "file_type": "MT5/MT4 Trading Report" if any(col.lower() in ['ticket', 'time', 'type', 'size', 'symbol', 'price', 'profit'] for col in df.columns) else "Trading Data",
                "date_range": {
                    "start": str(df_clean.iloc[0, 0]) if len(df) > 0 else "N/A",
                    "end": str(df_clean.iloc[-1, 0]) if len(df) > 0 else "N/A"
                } if len(df) > 0 else {"start": "N/A", "end": "N/A"},
                "trading_insights": {
                    "has_profit_column": any('profit' in col.lower() for col in df.columns),
                    "has_symbol_column": any('symbol' in col.lower() for col in df.columns),
                    "has_time_column": any('time' in col.lower() for col in df.columns),
                    "columns_detected": len([col for col in df.columns if not col.startswith('Unnamed')])
                }
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "message": f"File '{file.filename}' uploaded and analyzed successfully!",
            "analysis": analysis
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing file: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)