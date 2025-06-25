"""
Analysis Endpoints - ML-powered trading analysis with plugin support
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from app.core.plugin_manager import plugin_manager
from app.core.event_system import event_manager
from app.core.config import settings
from app.models.trading_data import AnalysisRequest, AnalysisResult, TradingData
from app.services.analysis_engine import AnalysisEngine
from app.services.ml_pipeline import MLPipeline

router = APIRouter()

# Global analysis engine and ML pipeline
analysis_engine = AnalysisEngine()
ml_pipeline = MLPipeline()


@router.post("/run", response_model=AnalysisResult)
async def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Run analysis on trading data using specified algorithms
    Supports both built-in and plugin-based analysis
    """
    
    try:
        # Load trading data
        trading_data = await _load_trading_data(request.data_id)
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Emit analysis start event
        await event_manager.emit("analysis_started", {
            "analysis_id": analysis_id,
            "data_id": request.data_id,
            "analysis_type": request.analysis_type
        })
        
        start_time = datetime.now()
        
        # Run analysis based on type
        if request.analysis_type == "comprehensive":
            results = await _run_comprehensive_analysis(trading_data, request.parameters)
        elif request.analysis_type == "time_patterns":
            results = await _run_time_pattern_analysis(trading_data, request.parameters)
        elif request.analysis_type == "risk_analysis":
            results = await _run_risk_analysis(trading_data, request.parameters)
        elif request.analysis_type == "ml_clustering":
            results = await _run_ml_clustering(trading_data, request.parameters)
        elif request.analysis_type == "ml_classification":
            results = await _run_ml_classification(trading_data, request.parameters)
        else:
            # Try plugin-based analysis
            results = await _run_plugin_analysis(request.analysis_type, trading_data, request.parameters)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Create analysis result
        analysis_result = AnalysisResult(
            analysis_id=analysis_id,
            analysis_type=request.analysis_type,
            timestamp=datetime.now(),
            data=results,
            metadata={
                "data_id": request.data_id,
                "parameters": request.parameters,
                "execution_time": execution_time,
                "trade_count": len(trading_data.trades)
            },
            execution_time=execution_time,
            status="completed"
        )
        
        # Save analysis result (in production, save to database)
        await _save_analysis_result(analysis_result)
        
        # Emit analysis completed event
        await event_manager.emit("analysis_completed", {
            "analysis_id": analysis_id,
            "execution_time": execution_time,
            "status": "completed"
        })
        
        return analysis_result
        
    except Exception as e:
        # Emit analysis error event
        await event_manager.emit("analysis_error", {
            "data_id": request.data_id,
            "analysis_type": request.analysis_type,
            "error": str(e)
        })
        
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/results")
async def list_analysis_results(
    data_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 50
):
    """List analysis results with optional filtering"""
    
    # In production, this would query database
    # For now, return mock results
    results = await _get_analysis_results(data_id, analysis_type, limit)
    
    return {
        "results": results,
        "total": len(results),
        "limit": limit
    }


@router.get("/results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get specific analysis result"""
    
    result = await _load_analysis_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    return result


@router.delete("/results/{analysis_id}")
async def delete_analysis_result(analysis_id: str):
    """Delete analysis result"""
    
    success = await _delete_analysis_result(analysis_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    
    await event_manager.emit("analysis_deleted", {"analysis_id": analysis_id})
    
    return {"message": f"Analysis result {analysis_id} deleted successfully"}


@router.get("/types")
async def get_analysis_types():
    """Get available analysis types including plugins"""
    
    built_in_types = [
        {
            "name": "comprehensive",
            "description": "Complete analysis including all available metrics",
            "parameters": {
                "include_ml": {"type": "boolean", "default": True},
                "include_patterns": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "time_patterns",
            "description": "Time-based performance pattern analysis",
            "parameters": {
                "granularity": {"type": "string", "default": "hour", "options": ["hour", "day", "week"]},
                "sessions": {"type": "boolean", "default": True}
            }
        },
        {
            "name": "risk_analysis",
            "description": "Risk metrics and drawdown analysis",
            "parameters": {
                "confidence_level": {"type": "number", "default": 0.95},
                "rolling_window": {"type": "integer", "default": 30}
            }
        },
        {
            "name": "ml_clustering",
            "description": "Machine learning trade clustering",
            "parameters": {
                "n_clusters": {"type": "integer", "default": 5},
                "algorithm": {"type": "string", "default": "kmeans", "options": ["kmeans", "dbscan"]}
            }
        },
        {
            "name": "ml_classification",
            "description": "Trade outcome prediction using ML",
            "parameters": {
                "model": {"type": "string", "default": "random_forest", "options": ["random_forest", "decision_tree", "xgboost"]},
                "cross_validation": {"type": "boolean", "default": True}
            }
        }
    ]
    
    # Add plugin-based analysis types
    plugin_types = []
    analysis_plugins = plugin_manager.get_plugins_by_type("AnalysisPlugin")
    
    for plugin in analysis_plugins:
        plugin_types.append({
            "name": plugin.manifest.name,
            "description": plugin.manifest.description,
            "version": plugin.manifest.version,
            "type": "plugin"
        })
    
    return {
        "built_in": built_in_types,
        "plugins": plugin_types
    }


# Helper functions
async def _load_trading_data(data_id: str) -> TradingData:
    """Load trading data from storage"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Trading data not found")
    
    with open(data_file_path, 'r') as f:
        return TradingData.parse_raw(f.read())


async def _run_comprehensive_analysis(data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run comprehensive analysis"""
    results = {}
    
    # Basic statistics
    results["summary"] = data.get_summary_stats()
    
    # Time patterns if requested
    if params.get("include_patterns", True):
        results["time_patterns"] = await analysis_engine.analyze_time_patterns(data)
    
    # ML analysis if requested
    if params.get("include_ml", True):
        results["ml_insights"] = await ml_pipeline.run_quick_analysis(data)
    
    # Performance metrics
    results["performance"] = await analysis_engine.calculate_performance_metrics(data)
    
    return results


async def _run_time_pattern_analysis(data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run time-based pattern analysis"""
    return await analysis_engine.analyze_time_patterns(data, params)


async def _run_risk_analysis(data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run risk analysis"""
    return await analysis_engine.analyze_risk_metrics(data, params)


async def _run_ml_clustering(data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run ML clustering analysis"""
    return await ml_pipeline.run_clustering_analysis(data, params)


async def _run_ml_classification(data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run ML classification analysis"""
    return await ml_pipeline.run_classification_analysis(data, params)


async def _run_plugin_analysis(analysis_type: str, data: TradingData, params: Dict[str, Any]) -> Dict[str, Any]:
    """Run plugin-based analysis"""
    plugin = plugin_manager.get_plugin(analysis_type)
    if not plugin:
        raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")
    
    # Convert TradingData to dict format for plugin
    data_dict = {
        "trades": [trade.dict() for trade in data.trades],
        "metadata": data.metadata.dict()
    }
    
    return await plugin.analyze(data_dict)


async def _save_analysis_result(result: AnalysisResult):
    """Save analysis result to storage"""
    # In production, save to database
    # For now, save to file
    cache_path = settings.get_cache_path()
    result_file = cache_path / f"analysis_{result.analysis_id}.json"
    
    with open(result_file, 'w') as f:
        f.write(result.json())


async def _load_analysis_result(analysis_id: str) -> Optional[AnalysisResult]:
    """Load analysis result from storage"""
    cache_path = settings.get_cache_path()
    result_file = cache_path / f"analysis_{analysis_id}.json"
    
    if not result_file.exists():
        return None
    
    with open(result_file, 'r') as f:
        return AnalysisResult.parse_raw(f.read())


async def _delete_analysis_result(analysis_id: str) -> bool:
    """Delete analysis result from storage"""
    cache_path = settings.get_cache_path()
    result_file = cache_path / f"analysis_{analysis_id}.json"
    
    if result_file.exists():
        result_file.unlink()
        return True
    return False


async def _get_analysis_results(data_id: Optional[str], analysis_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Get analysis results with filtering"""
    cache_path = settings.get_cache_path()
    results = []
    
    for result_file in cache_path.glob("analysis_*.json"):
        try:
            with open(result_file, 'r') as f:
                result = AnalysisResult.parse_raw(f.read())
            
            # Apply filters
            if data_id and result.metadata.get("data_id") != data_id:
                continue
            if analysis_type and result.analysis_type != analysis_type:
                continue
            
            results.append({
                "analysis_id": result.analysis_id,
                "analysis_type": result.analysis_type,
                "timestamp": result.timestamp,
                "execution_time": result.execution_time,
                "status": result.status,
                "metadata": result.metadata
            })
            
            if len(results) >= limit:
                break
                
        except Exception:
            continue  # Skip corrupted files
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return results