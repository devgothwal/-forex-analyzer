"""
Visualization Endpoints - Generate chart data for frontend visualization
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np

from app.core.config import settings
from app.models.trading_data import TradingData, VisualizationData

router = APIRouter()


@router.get("/{data_id}/performance-chart")
async def get_performance_chart(data_id: str) -> VisualizationData:
    """Generate equity curve visualization data"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Calculate equity curve
    df = df.sort_values('open_time')
    df['cumulative_profit'] = df['profit'].cumsum()
    df['trade_number'] = range(1, len(df) + 1)
    
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            'x': row['trade_number'],
            'y': row['cumulative_profit'],
            'date': row['open_time'].isoformat(),
            'profit': row['profit']
        })
    
    return VisualizationData(
        type="chart",
        config={
            "type": "line",
            "title": "Equity Curve",
            "xAxis": {"title": "Trade Number"},
            "yAxis": {"title": "Cumulative Profit ($)"}
        },
        data=chart_data
    )


@router.get("/{data_id}/hourly-heatmap")
async def get_hourly_heatmap(data_id: str) -> VisualizationData:
    """Generate hourly performance heatmap"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Create hourly and daily breakdown
    df['hour'] = df['open_time'].dt.hour
    df['day_of_week'] = df['open_time'].dt.day_name()
    
    # Calculate profit by hour and day
    heatmap_data = df.groupby(['day_of_week', 'hour'])['profit'].sum().reset_index()
    
    chart_data = []
    for _, row in heatmap_data.iterrows():
        chart_data.append({
            'x': row['hour'],
            'y': row['day_of_week'],
            'value': row['profit']
        })
    
    return VisualizationData(
        type="heatmap",
        config={
            "title": "Performance by Hour and Day",
            "xAxis": {"title": "Hour (GMT)"},
            "yAxis": {"title": "Day of Week"}
        },
        data=chart_data
    )


@router.get("/{data_id}/symbol-performance")
async def get_symbol_performance(data_id: str) -> VisualizationData:
    """Generate symbol performance chart"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Calculate performance by symbol
    symbol_stats = df.groupby('symbol').agg({
        'profit': ['sum', 'count'],
        'profit': lambda x: (x > 0).mean()
    }).round(2)
    
    symbol_stats.columns = ['total_profit', 'trade_count', 'win_rate']
    symbol_stats = symbol_stats.reset_index()
    
    chart_data = []
    for _, row in symbol_stats.iterrows():
        chart_data.append({
            'symbol': row['symbol'],
            'profit': row['total_profit'],
            'trades': row['trade_count'],
            'winRate': row['win_rate'] * 100
        })
    
    return VisualizationData(
        type="chart",
        config={
            "type": "bar",
            "title": "Performance by Symbol",
            "xAxis": {"title": "Currency Pair"},
            "yAxis": {"title": "Total Profit ($)"}
        },
        data=chart_data
    )


@router.get("/{data_id}/drawdown-chart")
async def get_drawdown_chart(data_id: str) -> VisualizationData:
    """Generate drawdown analysis chart"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Calculate drawdown
    df = df.sort_values('open_time')
    df['cumulative_profit'] = df['profit'].cumsum()
    df['running_max'] = df['cumulative_profit'].cummax()
    df['drawdown'] = df['cumulative_profit'] - df['running_max']
    df['trade_number'] = range(1, len(df) + 1)
    
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            'x': row['trade_number'],
            'y': row['drawdown'],
            'date': row['open_time'].isoformat()
        })
    
    return VisualizationData(
        type="chart",
        config={
            "type": "area",
            "title": "Drawdown Analysis",
            "xAxis": {"title": "Trade Number"},
            "yAxis": {"title": "Drawdown ($)"},
            "fill": "tonexty"
        },
        data=chart_data
    )


@router.get("/{data_id}/monthly-performance")
async def get_monthly_performance(data_id: str) -> VisualizationData:
    """Generate monthly performance chart"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Monthly aggregation
    df['year_month'] = df['open_time'].dt.to_period('M')
    monthly_stats = df.groupby('year_month').agg({
        'profit': ['sum', 'count'],
        'profit': lambda x: (x > 0).mean()
    }).round(2)
    
    monthly_stats.columns = ['total_profit', 'trade_count', 'win_rate']
    monthly_stats = monthly_stats.reset_index()
    monthly_stats['year_month'] = monthly_stats['year_month'].astype(str)
    
    chart_data = []
    for _, row in monthly_stats.iterrows():
        chart_data.append({
            'month': row['year_month'],
            'profit': row['total_profit'],
            'trades': row['trade_count'],
            'winRate': row['win_rate'] * 100
        })
    
    return VisualizationData(
        type="chart",
        config={
            "type": "bar",
            "title": "Monthly Performance",
            "xAxis": {"title": "Month"},
            "yAxis": {"title": "Profit ($)"}
        },
        data=chart_data
    )


@router.get("/{data_id}/risk-metrics")
async def get_risk_metrics_chart(data_id: str) -> VisualizationData:
    """Generate risk metrics visualization"""
    
    trading_data = await _load_trading_data(data_id)
    df = _trades_to_dataframe(trading_data.trades)
    
    # Calculate rolling risk metrics
    window = min(30, len(df) // 3)  # 30-trade rolling window or 1/3 of data
    
    df = df.sort_values('open_time')
    df['rolling_profit'] = df['profit'].rolling(window=window).sum()
    df['rolling_volatility'] = df['profit'].rolling(window=window).std()
    df['rolling_sharpe'] = df['rolling_profit'] / df['rolling_volatility']
    df['trade_number'] = range(1, len(df) + 1)
    
    # Remove NaN values
    df = df.dropna()
    
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            'x': row['trade_number'],
            'profit': row['rolling_profit'],
            'volatility': row['rolling_volatility'],
            'sharpe': row['rolling_sharpe'] if not np.isnan(row['rolling_sharpe']) and not np.isinf(row['rolling_sharpe']) else 0
        })
    
    return VisualizationData(
        type="chart",
        config={
            "type": "line",
            "title": f"Rolling Risk Metrics ({window}-trade window)",
            "xAxis": {"title": "Trade Number"},
            "yAxis": {"title": "Value"}
        },
        data=chart_data
    )


async def _load_trading_data(data_id: str) -> TradingData:
    """Load trading data from storage"""
    upload_path = settings.get_upload_path()
    data_file_path = upload_path / f"{data_id}.json"
    
    if not data_file_path.exists():
        raise HTTPException(status_code=404, detail="Trading data not found")
    
    with open(data_file_path, 'r') as f:
        return TradingData.parse_raw(f.read())


def _trades_to_dataframe(trades) -> pd.DataFrame:
    """Convert trades to pandas DataFrame"""
    data = []
    for trade in trades:
        data.append({
            'open_time': pd.to_datetime(trade.open_time),
            'profit': trade.profit,
            'size': trade.size,
            'symbol': trade.symbol,
            'type': trade.type
        })
    
    return pd.DataFrame(data)