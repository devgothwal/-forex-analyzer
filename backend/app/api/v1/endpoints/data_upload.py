"""
Data Upload Endpoints - Handle MT5/MT4 trading data import with plugin support
"""

import os
import uuid
import pandas as pd
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.plugin_manager import plugin_manager
from app.core.event_system import event_manager
from app.models.trading_data import TradingData, UploadResponse, DataMetadata, Trade
from app.services.data_processor import DataProcessor
from app.services.data_validator import DataValidator

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_trading_data(
    file: UploadFile = File(...),
    source: str = "MT5",
    account: Optional[str] = None
):
    """
    Upload and process trading data file (CSV, Excel)
    Supports multiple formats through plugin system
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        # Generate unique data ID
        data_id = str(uuid.uuid4())
        
        # Read file content
        file_content = await file.read()
        
        # Emit upload start event
        await event_manager.emit("data_upload_started", {
            "data_id": data_id,
            "filename": file.filename,
            "size": len(file_content),
            "source": source
        })
        
        # Try plugin-based parsing first
        parsed_data = None
        data_source_plugins = plugin_manager.get_plugins_by_type("DataSourcePlugin")
        
        for plugin in data_source_plugins:
            try:
                if await plugin.validate(file_content):
                    parsed_data = await plugin.parse(file_content)
                    source = plugin.manifest.name
                    break
            except Exception as e:
                continue  # Try next plugin
        
        # Fallback to built-in parser
        if not parsed_data:
            processor = DataProcessor()
            parsed_data = await processor.process_file(file_content, file.filename, source)
        
        # Validate data
        validator = DataValidator()
        validation_result = await validator.validate_trading_data(parsed_data)
        
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Data validation failed",
                    "errors": validation_result["errors"]
                }
            )
        
        # Save processed data (in production, save to database)
        upload_path = settings.get_upload_path()
        data_file_path = upload_path / f"{data_id}.json"
        
        # Convert to serializable format and save
        trading_data = TradingData(**parsed_data)
        with open(data_file_path, 'w') as f:
            f.write(trading_data.json())
        
        # Calculate summary statistics
        summary_stats = trading_data.get_summary_stats()
        
        # Create response
        response = UploadResponse(
            data_id=data_id,
            filename=file.filename,
            size=len(file_content),
            records_count=len(trading_data.trades),
            validation_status="valid",
            validation_errors=[],
            summary_stats=summary_stats
        )
        
        # Emit upload completed event
        await event_manager.emit("data_upload_completed", {
            "data_id": data_id,
            "filename": file.filename,
            "records_count": len(trading_data.trades),
            "summary_stats": summary_stats
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Emit upload error event
        await event_manager.emit("data_upload_error", {
            "filename": file.filename,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/datasets")
async def list_datasets():
    """List all uploaded datasets"""
    upload_path = settings.get_upload_path()
    datasets = []
    
    for file_path in upload_path.glob("*.json"):
        try:
            # Load dataset metadata
            with open(file_path, 'r') as f:
                data = TradingData.parse_raw(f.read())
            
            datasets.append({
                "data_id": file_path.stem,
                "metadata": data.metadata.dict(),
                "summary_stats": data.get_summary_stats(),
                "upload_time": datetime.fromtimestamp(file_path.stat().st_mtime)
            })
        except Exception as e:
            continue  # Skip corrupted files
    
    return {"datasets": datasets}


@router.get("/datasets/{data_id}")
async def get_dataset(data_id: str):
    """Get detailed information about a dataset"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        with open(data_file_path, 'r') as f:
            trading_data = TradingData.parse_raw(f.read())
        
        return {
            "data_id": data_id,
            "metadata": trading_data.metadata.dict(),
            "summary_stats": trading_data.get_summary_stats(),
            "trade_count": len(trading_data.trades),
            "date_range": {
                "start": min(trade.open_time for trade in trading_data.trades),
                "end": max(trade.close_time or trade.open_time for trade in trading_data.trades)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset: {str(e)}")


@router.delete("/datasets/{data_id}")
async def delete_dataset(data_id: str):
    """Delete a dataset"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        data_file_path.unlink()
        
        # Emit deletion event
        await event_manager.emit("data_deleted", {"data_id": data_id})
        
        return {"message": f"Dataset {data_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting dataset: {str(e)}")


@router.get("/datasets/{data_id}/preview")
async def preview_dataset(data_id: str, limit: int = 10):
    """Get a preview of dataset trades"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        with open(data_file_path, 'r') as f:
            trading_data = TradingData.parse_raw(f.read())
        
        # Return first N trades
        preview_trades = trading_data.trades[:limit]
        
        return {
            "data_id": data_id,
            "total_trades": len(trading_data.trades),
            "preview_count": len(preview_trades),
            "trades": [trade.dict() for trade in preview_trades]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dataset preview: {str(e)}")


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats and data sources"""
    formats = {
        "built_in": {
            "extensions": settings.ALLOWED_EXTENSIONS,
            "sources": ["MT5", "MT4", "Generic CSV"]
        },
        "plugins": []
    }
    
    # Add plugin-supported formats
    data_source_plugins = plugin_manager.get_plugins_by_type("DataSourcePlugin")
    for plugin in data_source_plugins:
        try:
            schema = await plugin.get_schema()
            formats["plugins"].append({
                "name": plugin.manifest.name,
                "description": plugin.manifest.description,
                "schema": schema
            })
        except Exception:
            continue
    
    return formats