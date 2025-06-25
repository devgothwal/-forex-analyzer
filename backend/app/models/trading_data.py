"""
Trading Data Models - Pydantic models for data validation and serialization
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class TradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CurrencyPair(str, Enum):
    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    USDCHF = "USDCHF"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"
    EURJPY = "EURJPY"
    GBPJPY = "GBPJPY"
    EURGBP = "EURGBP"
    CUSTOM = "CUSTOM"  # For any other pairs


class Trade(BaseModel):
    """Individual trade record"""
    ticket: str = Field(..., description="Unique trade identifier")
    open_time: datetime = Field(..., description="Trade opening time")
    close_time: Optional[datetime] = Field(None, description="Trade closing time")
    type: TradeType = Field(..., description="Trade type (buy/sell)")
    size: float = Field(..., gt=0, description="Trade size in lots")
    symbol: str = Field(..., description="Currency pair symbol")
    open_price: float = Field(..., gt=0, description="Opening price")
    close_price: Optional[float] = Field(None, gt=0, description="Closing price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    commission: float = Field(default=0.0, description="Commission paid")
    swap: float = Field(default=0.0, description="Swap/rollover fee")
    profit: float = Field(..., description="Trade profit/loss")
    
    # Calculated fields
    duration: Optional[int] = Field(None, description="Trade duration in minutes")
    pips: Optional[float] = Field(None, description="Pips gained/lost")
    risk_reward_ratio: Optional[float] = Field(None, description="Risk/reward ratio")
    
    @validator('close_time')
    def validate_close_time(cls, v, values):
        if v and 'open_time' in values and v < values['open_time']:
            raise ValueError('Close time must be after open time')
        return v
    
    @validator('duration', always=True)
    def calculate_duration(cls, v, values):
        if 'open_time' in values and 'close_time' in values and values['close_time']:
            delta = values['close_time'] - values['open_time']
            return int(delta.total_seconds() / 60)  # Duration in minutes
        return v
    
    @validator('pips', always=True)
    def calculate_pips(cls, v, values):
        if ('open_price' in values and 'close_price' in values and 
            values['close_price'] and 'symbol' in values):
            symbol = values['symbol']
            open_price = values['open_price']
            close_price = values['close_price']
            trade_type = values.get('type')
            
            # Determine pip value based on currency pair
            if 'JPY' in symbol or 'HUF' in symbol:
                pip_multiplier = 100  # 2 decimal places
            else:
                pip_multiplier = 10000  # 4 decimal places
            
            if trade_type == TradeType.BUY:
                return (close_price - open_price) * pip_multiplier
            else:
                return (open_price - close_price) * pip_multiplier
        return v


class DataMetadata(BaseModel):
    """Metadata about the trading data"""
    source: str = Field(..., description="Data source (MT5, MT4, etc.)")
    account: str = Field(..., description="Trading account identifier")
    currency: str = Field(..., description="Account base currency")
    leverage: int = Field(..., gt=0, description="Account leverage")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    date_range: Dict[str, datetime] = Field(..., description="Date range of data")
    balance_start: Optional[float] = Field(None, description="Starting balance")
    balance_end: Optional[float] = Field(None, description="Ending balance")
    equity_high: Optional[float] = Field(None, description="Highest equity")
    equity_low: Optional[float] = Field(None, description="Lowest equity")


class TradingData(BaseModel):
    """Complete trading dataset"""
    trades: List[Trade] = Field(..., description="List of all trades")
    metadata: DataMetadata = Field(..., description="Dataset metadata")
    
    @validator('trades')
    def validate_trades(cls, v):
        if not v:
            raise ValueError('At least one trade is required')
        return v
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        if not self.trades:
            return {}
        
        profits = [trade.profit for trade in self.trades]
        winning_trades = [p for p in profits if p > 0]
        losing_trades = [p for p in profits if p < 0]
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(self.trades) if self.trades else 0,
            "total_profit": sum(profits),
            "average_win": sum(winning_trades) / len(winning_trades) if winning_trades else 0,
            "average_loss": sum(losing_trades) / len(losing_trades) if losing_trades else 0,
            "profit_factor": abs(sum(winning_trades) / sum(losing_trades)) if losing_trades else float('inf'),
            "largest_win": max(profits) if profits else 0,
            "largest_loss": min(profits) if profits else 0,
        }


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoints"""
    data_id: str = Field(..., description="ID of uploaded data")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")
    plugins: List[str] = Field(default_factory=list, description="Specific plugins to use")


class AnalysisResult(BaseModel):
    """Analysis result model"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_type: str = Field(..., description="Type of analysis performed")
    timestamp: datetime = Field(..., description="Analysis execution time")
    data: Dict[str, Any] = Field(..., description="Analysis results")
    metadata: Dict[str, Any] = Field(..., description="Analysis metadata")
    execution_time: float = Field(..., description="Execution time in seconds")
    status: str = Field(..., description="Analysis status")


class Insight(BaseModel):
    """AI-generated insight model"""
    id: str = Field(..., description="Unique insight identifier")
    type: str = Field(..., description="Insight type (warning, success, info, critical)")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    recommendation: Optional[str] = Field(None, description="Actionable recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    impact: str = Field(..., description="Impact level (high, medium, low)")
    category: str = Field(..., description="Insight category")
    data: Optional[Dict[str, Any]] = Field(None, description="Supporting data")
    created_at: datetime = Field(default_factory=datetime.now)


class VisualizationData(BaseModel):
    """Visualization data model"""
    type: str = Field(..., description="Visualization type")
    config: Dict[str, Any] = Field(..., description="Chart configuration")
    data: List[Dict[str, Any]] = Field(..., description="Chart data")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class UploadResponse(BaseModel):
    """File upload response model"""
    data_id: str = Field(..., description="Unique identifier for uploaded data")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    records_count: int = Field(..., description="Number of records parsed")
    validation_status: str = Field(..., description="Validation status")
    validation_errors: List[str] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(..., description="Basic summary statistics")
    upload_time: datetime = Field(default_factory=datetime.now)