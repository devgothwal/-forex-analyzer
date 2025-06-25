"""
Insights Endpoints - AI-generated trading insights and recommendations
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.trading_data import Insight, TradingData
from app.services.insight_generator import InsightGenerator

router = APIRouter()

# Global insight generator
insight_generator = InsightGenerator()


@router.post("/generate/{data_id}")
async def generate_insights(data_id: str) -> List[Insight]:
    """Generate AI-powered insights for trading data"""
    
    try:
        # Load trading data
        trading_data = await _load_trading_data(data_id)
        
        # Generate insights
        insights = await insight_generator.generate_comprehensive_insights(trading_data)
        
        # Save insights for future reference
        await _save_insights(data_id, insights)
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/{data_id}")
async def get_insights(data_id: str) -> List[Insight]:
    """Get previously generated insights for a dataset"""
    
    insights = await _load_insights(data_id)
    if not insights:
        raise HTTPException(status_code=404, detail="No insights found for this dataset")
    
    return insights


@router.get("/{data_id}/categories")
async def get_insight_categories(data_id: str) -> Dict[str, List[Insight]]:
    """Get insights grouped by category"""
    
    insights = await _load_insights(data_id)
    if not insights:
        raise HTTPException(status_code=404, detail="No insights found for this dataset")
    
    # Group by category
    categories = {}
    for insight in insights:
        category = insight.category
        if category not in categories:
            categories[category] = []
        categories[category].append(insight)
    
    return categories


@router.get("/{data_id}/priority")
async def get_priority_insights(
    data_id: str,
    min_confidence: float = 0.7,
    max_results: int = 10
) -> List[Insight]:
    """Get high-priority insights based on confidence and impact"""
    
    insights = await _load_insights(data_id)
    if not insights:
        raise HTTPException(status_code=404, detail="No insights found for this dataset")
    
    # Filter by confidence and sort by impact
    priority_insights = [
        insight for insight in insights 
        if insight.confidence >= min_confidence
    ]
    
    # Sort by impact (high -> medium -> low) and confidence
    impact_order = {'high': 3, 'medium': 2, 'low': 1}
    priority_insights.sort(
        key=lambda x: (impact_order.get(x.impact, 0), x.confidence),
        reverse=True
    )
    
    return priority_insights[:max_results]


async def _load_trading_data(data_id: str) -> TradingData:
    """Load trading data from storage"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Trading data not found")
    
    with open(data_file_path, 'r') as f:
        return TradingData.parse_raw(f.read())


async def _save_insights(data_id: str, insights: List[Insight]):
    """Save insights to storage"""
    cache_path = settings.get_cache_path()
    insights_file = cache_path / f"insights_{data_id}.json"
    
    # Convert insights to JSON
    insights_data = [insight.dict() for insight in insights]
    
    import json
    with open(insights_file, 'w') as f:
        json.dump(insights_data, f, default=str, indent=2)


async def _load_insights(data_id: str) -> Optional[List[Insight]]:
    """Load insights from storage"""
    cache_path = settings.get_cache_path()
    insights_file = cache_path / f"insights_{data_id}.json"
    
    if not insights_file.exists():
        return None
    
    import json
    with open(insights_file, 'r') as f:
        insights_data = json.load(f)
    
    return [Insight(**insight_dict) for insight_dict in insights_data]