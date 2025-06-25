"""
Analysis Engine - Core trading data analysis with pattern recognition
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

from app.models.trading_data import TradingData, Trade
from app.core.event_system import event_manager

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Core engine for trading data analysis and pattern recognition"""
    
    def __init__(self):
        self.trading_sessions = {
            'Sydney': {'start': 21, 'end': 6},    # 21:00 - 06:00 GMT
            'Tokyo': {'start': 23, 'end': 8},     # 23:00 - 08:00 GMT
            'London': {'start': 7, 'end': 16},    # 07:00 - 16:00 GMT
            'New York': {'start': 12, 'end': 21}  # 12:00 - 21:00 GMT
        }
    
    async def analyze_time_patterns(self, data: TradingData, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze time-based trading patterns"""
        
        if not data.trades:
            return {"error": "No trades to analyze"}
        
        params = params or {}
        granularity = params.get('granularity', 'hour')
        include_sessions = params.get('sessions', True)
        
        # Convert trades to DataFrame for easier analysis
        df = self._trades_to_dataframe(data.trades)
        
        results = {}
        
        # Hour of day analysis
        if granularity in ['hour', 'all']:
            results['hourly_performance'] = await self._analyze_hourly_patterns(df)
        
        # Day of week analysis
        if granularity in ['day', 'week', 'all']:
            results['daily_performance'] = await self._analyze_daily_patterns(df)
        
        # Monthly analysis
        if granularity in ['month', 'all']:
            results['monthly_performance'] = await self._analyze_monthly_patterns(df)
        
        # Trading session analysis
        if include_sessions:
            results['session_performance'] = await self._analyze_session_patterns(df)
        
        # Time-based insights
        results['insights'] = await self._generate_time_insights(results)
        
        await event_manager.emit("analysis_time_patterns_completed", {
            "patterns_found": len(results),
            "granularity": granularity
        })
        
        return results
    
    async def analyze_risk_metrics(self, data: TradingData, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze risk metrics and drawdown"""
        
        if not data.trades:
            return {"error": "No trades to analyze"}
        
        params = params or {}
        confidence_level = params.get('confidence_level', 0.95)
        rolling_window = params.get('rolling_window', 30)
        
        df = self._trades_to_dataframe(data.trades)
        
        results = {}
        
        # Basic risk metrics
        results['basic_metrics'] = await self._calculate_basic_risk_metrics(df, confidence_level)
        
        # Drawdown analysis
        results['drawdown_analysis'] = await self._analyze_drawdown(df)
        
        # Rolling metrics
        results['rolling_metrics'] = await self._calculate_rolling_metrics(df, rolling_window)
        
        # Risk-adjusted returns
        results['risk_adjusted_returns'] = await self._calculate_risk_adjusted_returns(df)
        
        # Risk insights
        results['insights'] = await self._generate_risk_insights(results)
        
        return results
    
    async def calculate_performance_metrics(self, data: TradingData) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        
        if not data.trades:
            return {"error": "No trades to analyze"}
        
        df = self._trades_to_dataframe(data.trades)
        
        # Basic statistics
        total_trades = len(df)
        winning_trades = len(df[df['profit'] > 0])
        losing_trades = len(df[df['profit'] < 0])
        
        # Performance ratios
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        profits = df[df['profit'] > 0]['profit']
        losses = df[df['profit'] < 0]['profit']
        
        avg_win = profits.mean() if len(profits) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        profit_factor = abs(profits.sum() / losses.sum()) if losses.sum() != 0 else float('inf')
        
        # Risk metrics
        total_profit = df['profit'].sum()
        equity_curve = df['profit'].cumsum()
        
        # Maximum drawdown
        running_max = equity_curve.cummax()
        drawdown = equity_curve - running_max
        max_drawdown = drawdown.min()
        max_drawdown_pct = (max_drawdown / running_max.max() * 100) if running_max.max() != 0 else 0
        
        # Sharpe ratio (simplified)
        returns = df['profit']
        sharpe_ratio = returns.mean() / returns.std() if returns.std() != 0 else 0
        
        # Recovery factor
        recovery_factor = total_profit / abs(max_drawdown) if max_drawdown != 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate * 100, 2),
            'total_profit': round(total_profit, 2),
            'average_win': round(avg_win, 2),
            'average_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'largest_win': round(df['profit'].max(), 2),
            'largest_loss': round(df['profit'].min(), 2),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'recovery_factor': round(recovery_factor, 2),
            'expectancy': round((win_rate * avg_win) + ((1 - win_rate) * avg_loss), 2)
        }
    
    def _trades_to_dataframe(self, trades: List[Trade]) -> pd.DataFrame:
        """Convert trades to pandas DataFrame for analysis"""
        
        data = []
        for trade in trades:
            data.append({
                'ticket': trade.ticket,
                'open_time': pd.to_datetime(trade.open_time),
                'close_time': pd.to_datetime(trade.close_time) if trade.close_time else None,
                'type': trade.type,
                'size': trade.size,
                'symbol': trade.symbol,
                'open_price': trade.open_price,
                'close_price': trade.close_price,
                'profit': trade.profit,
                'commission': trade.commission,
                'swap': trade.swap,
                'duration': trade.duration,
                'pips': trade.pips
            })
        
        df = pd.DataFrame(data)
        
        # Add calculated fields
        if not df.empty:
            df['hour'] = df['open_time'].dt.hour
            df['day_of_week'] = df['open_time'].dt.day_name()
            df['month'] = df['open_time'].dt.month_name()
            df['date'] = df['open_time'].dt.date
            
            # Add trading session
            df['session'] = df['hour'].apply(self._get_trading_session)
        
        return df
    
    def _get_trading_session(self, hour: int) -> str:
        """Determine trading session based on hour"""
        
        for session, times in self.trading_sessions.items():
            start, end = times['start'], times['end']
            
            if start > end:  # Session spans midnight
                if hour >= start or hour < end:
                    return session
            else:  # Normal session
                if start <= hour < end:
                    return session
        
        return 'Other'
    
    async def _analyze_hourly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by hour of day"""
        
        hourly_stats = df.groupby('hour').agg({
            'profit': ['count', 'sum', 'mean'],
            'type': lambda x: (x == 'buy').sum()
        }).round(2)
        
        hourly_stats.columns = ['trade_count', 'total_profit', 'avg_profit', 'buy_count']
        hourly_stats['sell_count'] = hourly_stats['trade_count'] - hourly_stats['buy_count']
        hourly_stats['win_rate'] = df.groupby('hour')['profit'].apply(lambda x: (x > 0).mean() * 100).round(2)
        
        # Find best and worst hours
        best_hour = hourly_stats['total_profit'].idxmax()
        worst_hour = hourly_stats['total_profit'].idxmin()
        
        return {
            'hourly_breakdown': hourly_stats.to_dict('index'),
            'best_hour': int(best_hour),
            'worst_hour': int(worst_hour),
            'best_hour_profit': float(hourly_stats.loc[best_hour, 'total_profit']),
            'worst_hour_profit': float(hourly_stats.loc[worst_hour, 'total_profit'])
        }
    
    async def _analyze_daily_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by day of week"""
        
        daily_stats = df.groupby('day_of_week').agg({
            'profit': ['count', 'sum', 'mean'],
            'type': lambda x: (x == 'buy').sum()
        }).round(2)
        
        daily_stats.columns = ['trade_count', 'total_profit', 'avg_profit', 'buy_count']
        daily_stats['win_rate'] = df.groupby('day_of_week')['profit'].apply(lambda x: (x > 0).mean() * 100).round(2)
        
        # Order by weekday
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_stats = daily_stats.reindex([day for day in day_order if day in daily_stats.index])
        
        best_day = daily_stats['total_profit'].idxmax()
        worst_day = daily_stats['total_profit'].idxmin()
        
        return {
            'daily_breakdown': daily_stats.to_dict('index'),
            'best_day': best_day,
            'worst_day': worst_day,
            'best_day_profit': float(daily_stats.loc[best_day, 'total_profit']),
            'worst_day_profit': float(daily_stats.loc[worst_day, 'total_profit'])
        }
    
    async def _analyze_monthly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by month"""
        
        monthly_stats = df.groupby('month').agg({
            'profit': ['count', 'sum', 'mean']
        }).round(2)
        
        monthly_stats.columns = ['trade_count', 'total_profit', 'avg_profit']
        monthly_stats['win_rate'] = df.groupby('month')['profit'].apply(lambda x: (x > 0).mean() * 100).round(2)
        
        best_month = monthly_stats['total_profit'].idxmax()
        worst_month = monthly_stats['total_profit'].idxmin()
        
        return {
            'monthly_breakdown': monthly_stats.to_dict('index'),
            'best_month': best_month,
            'worst_month': worst_month
        }
    
    async def _analyze_session_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by trading session"""
        
        session_stats = df.groupby('session').agg({
            'profit': ['count', 'sum', 'mean']
        }).round(2)
        
        session_stats.columns = ['trade_count', 'total_profit', 'avg_profit']
        session_stats['win_rate'] = df.groupby('session')['profit'].apply(lambda x: (x > 0).mean() * 100).round(2)
        
        best_session = session_stats['total_profit'].idxmax()
        worst_session = session_stats['total_profit'].idxmin()
        
        return {
            'session_breakdown': session_stats.to_dict('index'),
            'best_session': best_session,
            'worst_session': worst_session
        }
    
    async def _calculate_basic_risk_metrics(self, df: pd.DataFrame, confidence_level: float) -> Dict[str, Any]:
        """Calculate basic risk metrics"""
        
        returns = df['profit']
        
        # Value at Risk
        var = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Conditional Value at Risk (Expected Shortfall)
        cvar = returns[returns <= var].mean()
        
        # Maximum consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        
        for profit in returns:
            if profit < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        return {
            'value_at_risk': round(var, 2),
            'conditional_var': round(cvar, 2),
            'max_consecutive_losses': max_consecutive_losses,
            'volatility': round(returns.std(), 2),
            'skewness': round(returns.skew(), 2),
            'kurtosis': round(returns.kurtosis(), 2)
        }
    
    async def _analyze_drawdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze drawdown patterns"""
        
        equity_curve = df['profit'].cumsum()
        running_max = equity_curve.cummax()
        drawdown = equity_curve - running_max
        
        # Find drawdown periods
        in_drawdown = drawdown < 0
        drawdown_periods = []
        
        if in_drawdown.any():
            start_idx = None
            for i, is_dd in enumerate(in_drawdown):
                if is_dd and start_idx is None:
                    start_idx = i
                elif not is_dd and start_idx is not None:
                    drawdown_periods.append({
                        'start': start_idx,
                        'end': i - 1,
                        'duration': i - start_idx,
                        'depth': drawdown.iloc[start_idx:i].min()
                    })
                    start_idx = None
        
        return {
            'max_drawdown': round(drawdown.min(), 2),
            'max_drawdown_pct': round((drawdown.min() / running_max.max() * 100), 2) if running_max.max() != 0 else 0,
            'drawdown_periods': len(drawdown_periods),
            'avg_drawdown_duration': round(np.mean([dd['duration'] for dd in drawdown_periods]), 2) if drawdown_periods else 0,
            'current_drawdown': round(drawdown.iloc[-1], 2) if not drawdown.empty else 0
        }
    
    async def _calculate_rolling_metrics(self, df: pd.DataFrame, window: int) -> Dict[str, Any]:
        """Calculate rolling performance metrics"""
        
        returns = df['profit']
        rolling_profit = returns.rolling(window=window).sum()
        rolling_win_rate = returns.rolling(window=window).apply(lambda x: (x > 0).mean())
        
        return {
            'rolling_profit_mean': round(rolling_profit.mean(), 2),
            'rolling_profit_std': round(rolling_profit.std(), 2),
            'rolling_win_rate_mean': round(rolling_win_rate.mean() * 100, 2),
            'rolling_win_rate_std': round(rolling_win_rate.std() * 100, 2),
            'best_period_profit': round(rolling_profit.max(), 2),
            'worst_period_profit': round(rolling_profit.min(), 2)
        }
    
    async def _calculate_risk_adjusted_returns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk-adjusted return metrics"""
        
        returns = df['profit']
        
        # Sharpe ratio
        sharpe = returns.mean() / returns.std() if returns.std() != 0 else 0
        
        # Sortino ratio (using downside deviation)
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino = returns.mean() / downside_deviation if downside_deviation != 0 else 0
        
        # Calmar ratio (annual return / max drawdown)
        equity_curve = returns.cumsum()
        running_max = equity_curve.cummax()
        drawdown = equity_curve - running_max
        max_drawdown = abs(drawdown.min())
        calmar = returns.sum() / max_drawdown if max_drawdown != 0 else 0
        
        return {
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'calmar_ratio': round(calmar, 2),
            'downside_deviation': round(downside_deviation, 2)
        }
    
    async def _generate_time_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from time pattern analysis"""
        
        insights = []
        
        # Hourly insights
        if 'hourly_performance' in results:
            hourly = results['hourly_performance']
            best_hour = hourly['best_hour']
            worst_hour = hourly['worst_hour']
            
            insights.append(f"Best trading hour: {best_hour}:00 GMT (${hourly['best_hour_profit']:.2f} profit)")
            insights.append(f"Worst trading hour: {worst_hour}:00 GMT (${hourly['worst_hour_profit']:.2f} profit)")
            
            # Check for significant differences
            profit_diff = hourly['best_hour_profit'] - hourly['worst_hour_profit']
            if profit_diff > 100:  # Significant difference
                insights.append(f"Consider avoiding trading at {worst_hour}:00 GMT - ${profit_diff:.2f} difference from best hour")
        
        # Daily insights
        if 'daily_performance' in results:
            daily = results['daily_performance']
            insights.append(f"Best trading day: {daily['best_day']} (${daily['best_day_profit']:.2f} profit)")
            insights.append(f"Worst trading day: {daily['worst_day']} (${daily['worst_day_profit']:.2f} profit)")
        
        # Session insights
        if 'session_performance' in results:
            session = results['session_performance']
            insights.append(f"Most profitable session: {session['best_session']}")
            insights.append(f"Least profitable session: {session['worst_session']}")
        
        return insights
    
    async def _generate_risk_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from risk analysis"""
        
        insights = []
        
        if 'basic_metrics' in results:
            metrics = results['basic_metrics']
            
            if metrics['max_consecutive_losses'] > 5:
                insights.append(f"High consecutive loss streak: {metrics['max_consecutive_losses']} trades. Consider position sizing adjustments.")
            
            if metrics['volatility'] > 50:
                insights.append("High volatility detected. Consider reducing position sizes during volatile periods.")
        
        if 'drawdown_analysis' in results:
            dd = results['drawdown_analysis']
            
            if abs(dd['max_drawdown_pct']) > 20:
                insights.append(f"Maximum drawdown of {dd['max_drawdown_pct']:.1f}% is high. Implement stricter risk management.")
            
            if dd['current_drawdown'] < -50:
                insights.append("Currently in significant drawdown. Consider reducing trading activity.")
        
        return insights