"""
Insight Generator - AI-powered trading insights and recommendations
"""

import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.models.trading_data import TradingData, Trade, Insight
from app.services.analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generate actionable insights from trading data analysis"""
    
    def __init__(self):
        self.analysis_engine = AnalysisEngine()
        self.insight_templates = self._load_insight_templates()
    
    async def generate_comprehensive_insights(self, data: TradingData) -> List[Insight]:
        """Generate comprehensive insights from trading data"""
        
        insights = []
        
        # Performance insights
        performance_insights = await self._generate_performance_insights(data)
        insights.extend(performance_insights)
        
        # Time pattern insights
        time_insights = await self._generate_time_pattern_insights(data)
        insights.extend(time_insights)
        
        # Risk management insights
        risk_insights = await self._generate_risk_insights(data)
        insights.extend(risk_insights)
        
        # Symbol-specific insights
        symbol_insights = await self._generate_symbol_insights(data)
        insights.extend(symbol_insights)
        
        # Behavioral insights
        behavioral_insights = await self._generate_behavioral_insights(data)
        insights.extend(behavioral_insights)
        
        # Strategy insights
        strategy_insights = await self._generate_strategy_insights(data)
        insights.extend(strategy_insights)
        
        # Sort by priority (impact + confidence)
        insights.sort(key=lambda x: self._calculate_priority_score(x), reverse=True)
        
        return insights
    
    async def _generate_performance_insights(self, data: TradingData) -> List[Insight]:
        """Generate performance-related insights"""
        
        insights = []
        summary = data.get_summary_stats()
        
        # Win rate insights
        win_rate = summary.get('win_rate', 0)
        if win_rate < 0.4:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="critical",
                title="Low Win Rate Detected",
                description=f"Your win rate is {win_rate:.1%}, which is below the recommended minimum of 40%.",
                recommendation="Focus on improving trade selection criteria and consider reducing trade frequency.",
                confidence=0.9,
                impact="high",
                category="performance",
                data={"win_rate": win_rate, "threshold": 0.4}
            ))
        elif win_rate > 0.7:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="success",
                title="Excellent Win Rate",
                description=f"Your win rate of {win_rate:.1%} is excellent and above industry averages.",
                recommendation="Maintain your current trade selection approach.",
                confidence=0.85,
                impact="medium",
                category="performance",
                data={"win_rate": win_rate}
            ))
        
        # Profit factor insights
        profit_factor = summary.get('profit_factor', 0)
        if profit_factor < 1.2:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="Low Profit Factor",
                description=f"Your profit factor of {profit_factor:.2f} indicates poor risk-reward management.",
                recommendation="Increase take profit targets or reduce stop loss distances to improve profit factor.",
                confidence=0.8,
                impact="high",
                category="performance",
                data={"profit_factor": profit_factor, "target": 1.5}
            ))
        
        # Average win vs loss insights
        avg_win = summary.get('average_win', 0)
        avg_loss = abs(summary.get('average_loss', 0))
        
        if avg_loss > 0 and avg_win / avg_loss < 1.5:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="Poor Risk-Reward Ratio",
                description=f"Your average win (${avg_win:.2f}) vs average loss (${avg_loss:.2f}) ratio is suboptimal.",
                recommendation="Aim for a minimum 1.5:1 reward-to-risk ratio on your trades.",
                confidence=0.75,
                impact="medium",
                category="risk_management",
                data={"avg_win": avg_win, "avg_loss": avg_loss, "ratio": avg_win/avg_loss if avg_loss > 0 else 0}
            ))
        
        return insights
    
    async def _generate_time_pattern_insights(self, data: TradingData) -> List[Insight]:
        """Generate time-based pattern insights"""
        
        insights = []
        
        # Analyze hourly patterns
        df = self._trades_to_dataframe(data.trades)
        if df.empty:
            return insights
        
        # Hour analysis
        hourly_profit = df.groupby('hour')['profit'].sum()
        best_hour = hourly_profit.idxmax()
        worst_hour = hourly_profit.idxmin()
        
        if hourly_profit[best_hour] - hourly_profit[worst_hour] > 100:  # Significant difference
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="info",
                title="Optimal Trading Hours Identified",
                description=f"You perform best at {best_hour}:00 GMT (${hourly_profit[best_hour]:.2f}) and worst at {worst_hour}:00 GMT (${hourly_profit[worst_hour]:.2f}).",
                recommendation=f"Focus trading activity around {best_hour}:00 GMT and avoid {worst_hour}:00 GMT.",
                confidence=0.7,
                impact="medium",
                category="timing",
                data={"best_hour": int(best_hour), "worst_hour": int(worst_hour), "profit_diff": float(hourly_profit[best_hour] - hourly_profit[worst_hour])}
            ))
        
        # Day of week analysis
        daily_profit = df.groupby('day_of_week')['profit'].sum()
        if not daily_profit.empty:
            best_day = daily_profit.idxmax()
            worst_day = daily_profit.idxmin()
            
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="info",
                title="Weekly Performance Pattern",
                description=f"Your best trading day is {best_day} (${daily_profit[best_day]:.2f}) and worst is {worst_day} (${daily_profit[worst_day]:.2f}).",
                recommendation=f"Consider increasing position sizes on {best_day} and reducing activity on {worst_day}.",
                confidence=0.65,
                impact="low",
                category="timing",
                data={"best_day": best_day, "worst_day": worst_day}
            ))
        
        return insights
    
    async def _generate_risk_insights(self, data: TradingData) -> List[Insight]:
        """Generate risk management insights"""
        
        insights = []
        df = self._trades_to_dataframe(data.trades)
        
        if df.empty:
            return insights
        
        # Consecutive losses analysis
        consecutive_losses = 0
        max_consecutive_losses = 0
        
        for profit in df['profit']:
            if profit < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        if max_consecutive_losses > 5:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="High Consecutive Loss Streak",
                description=f"You experienced {max_consecutive_losses} consecutive losses, indicating potential overtrading.",
                recommendation="Implement position sizing rules and consider taking breaks after 3-4 consecutive losses.",
                confidence=0.8,
                impact="high",
                category="risk_management",
                data={"max_consecutive_losses": max_consecutive_losses}
            ))
        
        # Drawdown analysis
        equity_curve = df['profit'].cumsum()
        running_max = equity_curve.cummax()
        drawdown = equity_curve - running_max
        max_drawdown_pct = (drawdown.min() / running_max.max() * 100) if running_max.max() != 0 else 0
        
        if abs(max_drawdown_pct) > 20:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="critical",
                title="Excessive Drawdown Risk",
                description=f"Your maximum drawdown of {abs(max_drawdown_pct):.1f}% is dangerously high.",
                recommendation="Reduce position sizes and implement stricter risk management rules.",
                confidence=0.9,
                impact="high",
                category="risk_management",
                data={"max_drawdown_pct": float(max_drawdown_pct)}
            ))
        
        return insights
    
    async def _generate_symbol_insights(self, data: TradingData) -> List[Insight]:
        """Generate currency pair specific insights"""
        
        insights = []
        df = self._trades_to_dataframe(data.trades)
        
        if df.empty:
            return insights
        
        # Symbol performance analysis
        symbol_stats = df.groupby('symbol').agg({
            'profit': ['sum', 'mean', 'count'],
            'profit': lambda x: (x > 0).mean()  # win rate
        })
        
        symbol_stats.columns = ['total_profit', 'avg_profit', 'trade_count', 'win_rate']
        
        # Find best and worst performing symbols
        if len(symbol_stats) > 1:
            best_symbol = symbol_stats['total_profit'].idxmax()
            worst_symbol = symbol_stats['total_profit'].idxmin()
            
            best_profit = symbol_stats.loc[best_symbol, 'total_profit']
            worst_profit = symbol_stats.loc[worst_symbol, 'total_profit']
            
            if best_profit > abs(worst_profit):
                insights.append(Insight(
                    id=str(uuid.uuid4()),
                    type="success",
                    title="Strong Symbol Performance",
                    description=f"{best_symbol} is your most profitable pair with ${best_profit:.2f} profit from {symbol_stats.loc[best_symbol, 'trade_count']} trades.",
                    recommendation=f"Consider increasing allocation to {best_symbol} while maintaining proper risk management.",
                    confidence=0.75,
                    impact="medium",
                    category="symbols",
                    data={"symbol": best_symbol, "profit": float(best_profit), "trade_count": int(symbol_stats.loc[best_symbol, 'trade_count'])}
                ))
            
            if worst_profit < -50:  # Significant losses
                insights.append(Insight(
                    id=str(uuid.uuid4()),
                    type="warning",
                    title="Underperforming Symbol",
                    description=f"{worst_symbol} is causing losses with ${worst_profit:.2f} total loss.",
                    recommendation=f"Review your strategy for {worst_symbol} or consider avoiding this pair.",
                    confidence=0.7,
                    impact="medium",
                    category="symbols",
                    data={"symbol": worst_symbol, "profit": float(worst_profit)}
                ))
        
        return insights
    
    async def _generate_behavioral_insights(self, data: TradingData) -> List[Insight]:
        """Generate insights about trading behavior patterns"""
        
        insights = []
        df = self._trades_to_dataframe(data.trades)
        
        if df.empty:
            return insights
        
        # Trade duration analysis
        if 'duration_minutes' in df.columns and df['duration_minutes'].notna().any():
            avg_duration = df['duration_minutes'].mean()
            
            # Analyze duration vs profit correlation
            short_trades = df[df['duration_minutes'] <= 60]  # Less than 1 hour
            long_trades = df[df['duration_minutes'] > 240]   # More than 4 hours
            
            if len(short_trades) > 5 and len(long_trades) > 5:
                short_profit_rate = (short_trades['profit'] > 0).mean()
                long_profit_rate = (long_trades['profit'] > 0).mean()
                
                if long_profit_rate > short_profit_rate + 0.2:  # 20% difference
                    insights.append(Insight(
                        id=str(uuid.uuid4()),
                        type="info",
                        title="Patience Pays Off",
                        description=f"Longer trades (>4h) have {long_profit_rate:.1%} win rate vs {short_profit_rate:.1%} for short trades (<1h).",
                        recommendation="Consider holding profitable positions longer and avoid scalping strategies.",
                        confidence=0.65,
                        impact="medium",
                        category="behavior",
                        data={"long_win_rate": float(long_profit_rate), "short_win_rate": float(short_profit_rate)}
                    ))
        
        # Overtrading analysis
        daily_trade_count = df.groupby(df['open_time'].dt.date)['profit'].count()
        avg_daily_trades = daily_trade_count.mean()
        
        if avg_daily_trades > 10:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="Potential Overtrading",
                description=f"You average {avg_daily_trades:.1f} trades per day, which may indicate overtrading.",
                recommendation="Focus on quality over quantity. Reduce trade frequency and improve selection criteria.",
                confidence=0.7,
                impact="medium",
                category="behavior",
                data={"avg_daily_trades": float(avg_daily_trades)}
            ))
        
        return insights
    
    async def _generate_strategy_insights(self, data: TradingData) -> List[Insight]:
        """Generate strategy-specific insights"""
        
        insights = []
        df = self._trades_to_dataframe(data.trades)
        
        if df.empty:
            return insights
        
        # Trade size consistency
        size_std = df['size'].std()
        size_mean = df['size'].mean()
        
        if size_std / size_mean > 0.5:  # High variation in trade sizes
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="info",
                title="Inconsistent Position Sizing",
                description="Your trade sizes vary significantly, which may indicate emotional trading.",
                recommendation="Implement consistent position sizing rules based on account risk percentage.",
                confidence=0.6,
                impact="medium",
                category="strategy",
                data={"size_variation": float(size_std / size_mean)}
            ))
        
        # Buy vs Sell performance
        buy_trades = df[df['type'] == 'buy']
        sell_trades = df[df['type'] == 'sell']
        
        if len(buy_trades) > 5 and len(sell_trades) > 5:
            buy_profit = buy_trades['profit'].sum()
            sell_profit = sell_trades['profit'].sum()
            
            if abs(buy_profit - sell_profit) > 100:  # Significant difference
                better_direction = "buying" if buy_profit > sell_profit else "selling"
                worse_direction = "selling" if buy_profit > sell_profit else "buying"
                
                insights.append(Insight(
                    id=str(uuid.uuid4()),
                    type="info",
                    title="Directional Bias Performance",
                    description=f"You perform significantly better when {better_direction} (${max(buy_profit, sell_profit):.2f}) vs {worse_direction} (${min(buy_profit, sell_profit):.2f}).",
                    recommendation=f"Consider focusing more on {better_direction} opportunities or review your {worse_direction} strategy.",
                    confidence=0.65,
                    impact="low",
                    category="strategy",
                    data={"buy_profit": float(buy_profit), "sell_profit": float(sell_profit)}
                ))
        
        return insights
    
    def _trades_to_dataframe(self, trades: List[Trade]) -> pd.DataFrame:
        """Convert trades to pandas DataFrame"""
        
        data = []
        for trade in trades:
            data.append({
                'open_time': pd.to_datetime(trade.open_time),
                'profit': trade.profit,
                'size': trade.size,
                'symbol': trade.symbol,
                'type': trade.type,
                'duration_minutes': trade.duration,
                'hour': pd.to_datetime(trade.open_time).hour if trade.open_time else 0,
                'day_of_week': pd.to_datetime(trade.open_time).day_name() if trade.open_time else 'Unknown'
            })
        
        return pd.DataFrame(data)
    
    def _calculate_priority_score(self, insight: Insight) -> float:
        """Calculate priority score for insight ranking"""
        
        impact_weights = {'high': 3, 'medium': 2, 'low': 1}
        type_weights = {'critical': 4, 'warning': 3, 'info': 2, 'success': 1}
        
        impact_score = impact_weights.get(insight.impact, 1)
        type_score = type_weights.get(insight.type, 1)
        confidence_score = insight.confidence
        
        return (impact_score * 0.4) + (type_score * 0.3) + (confidence_score * 0.3)
    
    def _load_insight_templates(self) -> Dict[str, Any]:
        """Load insight templates for consistent messaging"""
        
        return {
            "performance": {
                "low_win_rate": "Your win rate of {win_rate:.1%} is below optimal levels",
                "high_drawdown": "Maximum drawdown of {drawdown:.1f}% exceeds recommended limits"
            },
            "timing": {
                "best_hour": "Peak performance occurs at {hour}:00 GMT",
                "session_preference": "You perform best during {session} trading session"
            },
            "risk": {
                "consecutive_losses": "Maximum consecutive losses: {count} trades",
                "position_sizing": "Consider implementing 1-2% risk per trade rule"
            }
        }