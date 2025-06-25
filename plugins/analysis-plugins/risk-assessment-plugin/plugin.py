"""
Risk Assessment Plugin - Advanced risk analysis with VaR and Monte Carlo simulations
Demonstrates the plugin architecture's extensibility
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import logging
from scipy import stats

# Import base plugin interface (this would be imported from the main application)
import sys
sys.path.append('../../../backend/app')
from core.plugin_manager import AnalysisPlugin, PluginManifest

logger = logging.getLogger(__name__)


class Plugin(AnalysisPlugin):
    """Advanced Risk Assessment Plugin"""
    
    def __init__(self, manifest: PluginManifest):
        super().__init__(manifest)
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.confidence_levels = [0.95, 0.99]
        self.monte_carlo_simulations = 10000
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration"""
        self.risk_free_rate = config.get('risk_free_rate', 0.02)
        self.confidence_levels = config.get('confidence_levels', [0.95, 0.99])
        self.monte_carlo_simulations = config.get('monte_carlo_simulations', 10000)
        
        logger.info(f"Risk Assessment Plugin initialized with {len(self.confidence_levels)} confidence levels")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform advanced risk analysis"""
        
        trades = data['trades']
        if not trades:
            return {"error": "No trades provided for risk analysis"}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(trades)
        
        # Ensure we have profit data
        if 'profit' not in df.columns:
            return {"error": "No profit data available for risk analysis"}
        
        # Convert profit to numeric
        df['profit'] = pd.to_numeric(df['profit'], errors='coerce')
        df = df.dropna(subset=['profit'])
        
        if len(df) < 10:
            return {"error": "Insufficient data for risk analysis (minimum 10 trades required)"}
        
        results = {}
        
        # Basic risk metrics
        results['basic_metrics'] = await self._calculate_basic_risk_metrics(df)
        
        # Value at Risk (VaR) analysis
        results['var_analysis'] = await self._calculate_var(df)
        
        # Monte Carlo simulation
        results['monte_carlo'] = await self._monte_carlo_simulation(df)
        
        # Risk-adjusted returns
        results['risk_adjusted_returns'] = await self._calculate_risk_adjusted_returns(df)
        
        # Tail risk analysis
        results['tail_risk'] = await self._analyze_tail_risk(df)
        
        # Risk attribution
        results['risk_attribution'] = await self._analyze_risk_attribution(df)
        
        return results
    
    async def get_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from risk analysis"""
        
        insights = []
        
        if 'var_analysis' in results:
            var_data = results['var_analysis']
            
            # VaR insights
            for confidence in self.confidence_levels:
                var_value = var_data.get(f'var_{int(confidence*100)}', 0)
                if abs(var_value) > 100:  # Significant VaR
                    insights.append({
                        "type": "warning",
                        "title": f"High Value at Risk ({int(confidence*100)}%)",
                        "description": f"Your {int(confidence*100)}% VaR is ${abs(var_value):.2f}, indicating potential for significant losses.",
                        "recommendation": "Consider reducing position sizes or implementing tighter stop-loss orders.",
                        "confidence": 0.85,
                        "impact": "high",
                        "category": "risk_management",
                        "data": {"var_value": var_value, "confidence_level": confidence}
                    })
        
        if 'tail_risk' in results:
            tail_data = results['tail_risk']
            
            # Tail risk insights
            if tail_data.get('extreme_loss_probability', 0) > 0.05:  # More than 5% chance
                insights.append({
                    "type": "critical",
                    "title": "High Extreme Loss Probability",
                    "description": f"There's a {tail_data['extreme_loss_probability']*100:.1f}% probability of extreme losses.",
                    "recommendation": "Implement portfolio diversification and consider position sizing based on Kelly Criterion.",
                    "confidence": 0.9,
                    "impact": "high",
                    "category": "risk_management",
                    "data": tail_data
                })
        
        if 'risk_adjusted_returns' in results:
            risk_adj = results['risk_adjusted_returns']
            
            # Sharpe ratio insights
            sharpe_ratio = risk_adj.get('sharpe_ratio', 0)
            if sharpe_ratio < 0.5:
                insights.append({
                    "type": "warning",
                    "title": "Low Risk-Adjusted Returns",
                    "description": f"Your Sharpe ratio of {sharpe_ratio:.2f} indicates poor risk-adjusted performance.",
                    "recommendation": "Focus on improving trade selection or reducing volatility through better risk management.",
                    "confidence": 0.8,
                    "impact": "medium",
                    "category": "performance",
                    "data": {"sharpe_ratio": sharpe_ratio}
                })
            elif sharpe_ratio > 1.0:
                insights.append({
                    "type": "success",
                    "title": "Excellent Risk-Adjusted Returns",
                    "description": f"Your Sharpe ratio of {sharpe_ratio:.2f} indicates strong risk-adjusted performance.",
                    "recommendation": "Maintain your current risk management approach.",
                    "confidence": 0.85,
                    "impact": "medium",
                    "category": "performance",
                    "data": {"sharpe_ratio": sharpe_ratio}
                })
        
        if 'monte_carlo' in results:
            mc_data = results['monte_carlo']
            
            # Monte Carlo insights
            probability_of_loss = mc_data.get('probability_of_loss', 0)
            if probability_of_loss > 0.3:  # More than 30% chance of loss
                insights.append({
                    "type": "warning",
                    "title": "High Probability of Future Losses",
                    "description": f"Monte Carlo simulation shows {probability_of_loss*100:.1f}% probability of losses in similar conditions.",
                    "recommendation": "Consider reducing risk exposure or implementing protective strategies.",
                    "confidence": 0.75,
                    "impact": "medium",
                    "category": "risk_management",
                    "data": mc_data
                })
        
        return insights
    
    async def _calculate_basic_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic risk metrics"""
        
        returns = df['profit']
        
        return {
            'volatility': float(returns.std()),
            'mean_return': float(returns.mean()),
            'skewness': float(returns.skew()),
            'kurtosis': float(returns.kurtosis()),
            'max_loss': float(returns.min()),
            'max_gain': float(returns.max()),
            'downside_deviation': float(returns[returns < 0].std()) if len(returns[returns < 0]) > 0 else 0,
            'upside_deviation': float(returns[returns > 0].std()) if len(returns[returns > 0]) > 0 else 0
        }
    
    async def _calculate_var(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Value at Risk using multiple methods"""
        
        returns = df['profit']
        var_results = {}
        
        for confidence in self.confidence_levels:
            alpha = 1 - confidence
            
            # Historical VaR
            historical_var = float(np.percentile(returns, alpha * 100))
            
            # Parametric VaR (assuming normal distribution)
            mean = returns.mean()
            std = returns.std()
            parametric_var = float(mean + std * stats.norm.ppf(alpha))
            
            # Modified VaR (Cornish-Fisher expansion)
            skew = returns.skew()
            kurt = returns.kurtosis()
            z_score = stats.norm.ppf(alpha)
            z_cf = z_score + (z_score**2 - 1) * skew / 6 + (z_score**3 - 3*z_score) * kurt / 24
            modified_var = float(mean + std * z_cf)
            
            var_results.update({
                f'var_{int(confidence*100)}_historical': historical_var,
                f'var_{int(confidence*100)}_parametric': parametric_var,
                f'var_{int(confidence*100)}_modified': modified_var,
                f'var_{int(confidence*100)}': historical_var  # Use historical as primary
            })
            
            # Conditional VaR (Expected Shortfall)
            conditional_var = float(returns[returns <= historical_var].mean()) if len(returns[returns <= historical_var]) > 0 else 0
            var_results[f'cvar_{int(confidence*100)}'] = conditional_var
        
        return var_results
    
    async def _monte_carlo_simulation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform Monte Carlo simulation for risk assessment"""
        
        returns = df['profit']
        mean = returns.mean()
        std = returns.std()
        
        # Generate random scenarios
        np.random.seed(42)  # For reproducible results
        simulated_returns = np.random.normal(mean, std, self.monte_carlo_simulations)
        
        # Calculate statistics
        probability_of_loss = float(np.mean(simulated_returns < 0))
        probability_of_profit = float(np.mean(simulated_returns > 0))
        
        # Expected values
        expected_loss = float(np.mean(simulated_returns[simulated_returns < 0])) if np.any(simulated_returns < 0) else 0
        expected_profit = float(np.mean(simulated_returns[simulated_returns > 0])) if np.any(simulated_returns > 0) else 0
        
        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = {f'p{p}': float(np.percentile(simulated_returns, p)) for p in percentiles}
        
        return {
            'simulations': self.monte_carlo_simulations,
            'probability_of_loss': probability_of_loss,
            'probability_of_profit': probability_of_profit,
            'expected_loss': expected_loss,
            'expected_profit': expected_profit,
            'percentiles': percentile_values,
            'worst_case_1pct': float(np.percentile(simulated_returns, 1)),
            'best_case_1pct': float(np.percentile(simulated_returns, 99))
        }
    
    async def _calculate_risk_adjusted_returns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate various risk-adjusted return metrics"""
        
        returns = df['profit']
        
        # Sharpe ratio
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = float(excess_returns.mean() / returns.std()) if returns.std() != 0 else 0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = float(excess_returns.mean() / downside_deviation) if downside_deviation != 0 else 0
        
        # Calmar ratio
        equity_curve = returns.cumsum()
        running_max = equity_curve.cummax()
        drawdown = equity_curve - running_max
        max_drawdown = abs(drawdown.min())
        calmar_ratio = float(returns.mean() / max_drawdown) if max_drawdown != 0 else 0
        
        # Information ratio
        benchmark_return = 0  # Assume benchmark is 0
        tracking_error = returns.std()
        information_ratio = float((returns.mean() - benchmark_return) / tracking_error) if tracking_error != 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'information_ratio': information_ratio,
            'max_drawdown': float(max_drawdown),
            'excess_return_mean': float(excess_returns.mean())
        }
    
    async def _analyze_tail_risk(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze tail risk characteristics"""
        
        returns = df['profit']
        
        # Define extreme loss threshold (bottom 5%)
        extreme_loss_threshold = np.percentile(returns, 5)
        extreme_losses = returns[returns <= extreme_loss_threshold]
        
        # Tail statistics
        tail_mean = float(extreme_losses.mean()) if len(extreme_losses) > 0 else 0
        tail_std = float(extreme_losses.std()) if len(extreme_losses) > 0 else 0
        extreme_loss_probability = float(len(extreme_losses) / len(returns))
        
        # Maximum loss runs
        consecutive_losses = 0
        max_consecutive_losses = 0
        loss_runs = []
        current_run = 0
        
        for profit in returns:
            if profit < 0:
                current_run += 1
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                if current_run > 0:
                    loss_runs.append(current_run)
                    current_run = 0
                consecutive_losses = 0
        
        avg_loss_run = float(np.mean(loss_runs)) if loss_runs else 0
        
        return {
            'extreme_loss_threshold': float(extreme_loss_threshold),
            'extreme_loss_probability': extreme_loss_probability,
            'tail_mean': tail_mean,
            'tail_std': tail_std,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_loss_run_length': avg_loss_run,
            'total_loss_runs': len(loss_runs)
        }
    
    async def _analyze_risk_attribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze risk attribution by different factors"""
        
        attribution = {}
        
        # Risk by symbol (if available)
        if 'symbol' in df.columns:
            symbol_risk = {}
            for symbol in df['symbol'].unique():
                symbol_data = df[df['symbol'] == symbol]['profit']
                symbol_risk[symbol] = {
                    'volatility': float(symbol_data.std()),
                    'var_95': float(np.percentile(symbol_data, 5)),
                    'contribution': float(len(symbol_data) / len(df))
                }
            attribution['by_symbol'] = symbol_risk
        
        # Risk by trade type (if available)
        if 'type' in df.columns:
            type_risk = {}
            for trade_type in df['type'].unique():
                type_data = df[df['type'] == trade_type]['profit']
                type_risk[trade_type] = {
                    'volatility': float(type_data.std()),
                    'var_95': float(np.percentile(type_data, 5)),
                    'contribution': float(len(type_data) / len(df))
                }
            attribution['by_type'] = type_risk
        
        # Risk by time periods (if time data available)
        if 'open_time' in df.columns:
            df['hour'] = pd.to_datetime(df['open_time']).dt.hour
            hourly_risk = {}
            
            for hour in df['hour'].unique():
                if pd.notna(hour):
                    hour_data = df[df['hour'] == hour]['profit']
                    hourly_risk[int(hour)] = {
                        'volatility': float(hour_data.std()),
                        'var_95': float(np.percentile(hour_data, 5)),
                        'contribution': float(len(hour_data) / len(df))
                    }
            attribution['by_hour'] = hourly_risk
        
        return attribution
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        logger.info("Risk Assessment Plugin cleanup completed")


# Plugin metadata for registration
PLUGIN_MANIFEST = {
    "name": "risk_assessment",
    "version": "1.0.0",
    "description": "Advanced risk assessment plugin with VaR, CVaR, and Monte Carlo simulations",
    "author": "Forex Analyzer Team",
    "api_version": "1.0"
}