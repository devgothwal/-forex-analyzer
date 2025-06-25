"""
Data Validator Service - Validate and quality-check trading data
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate trading data integrity and quality"""
    
    def __init__(self):
        self.min_trade_size = 0.01
        self.max_trade_size = 1000
        self.min_price = 0.0001
        self.max_price = 100000
        self.valid_trade_types = ['buy', 'sell']
        
    async def validate_trading_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive validation of trading data"""
        
        errors = []
        warnings = []
        
        # Validate structure
        structure_errors = await self._validate_structure(data)
        errors.extend(structure_errors)
        
        if not errors:  # Only continue if structure is valid
            # Validate trades
            trade_errors, trade_warnings = await self._validate_trades(data['trades'])
            errors.extend(trade_errors)
            warnings.extend(trade_warnings)
            
            # Validate metadata
            metadata_errors = await self._validate_metadata(data['metadata'])
            errors.extend(metadata_errors)
            
            # Validate data consistency
            consistency_errors = await self._validate_consistency(data)
            errors.extend(consistency_errors)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validation_summary': {
                'total_trades': len(data.get('trades', [])),
                'error_count': len(errors),
                'warning_count': len(warnings)
            }
        }
    
    async def _validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validate data structure"""
        errors = []
        
        # Check required top-level fields
        if 'trades' not in data:
            errors.append("Missing 'trades' field")
        elif not isinstance(data['trades'], list):
            errors.append("'trades' must be a list")
        elif len(data['trades']) == 0:
            errors.append("No trades found in data")
        
        if 'metadata' not in data:
            errors.append("Missing 'metadata' field")
        elif not isinstance(data['metadata'], dict):
            errors.append("'metadata' must be a dictionary")
        
        return errors
    
    async def _validate_trades(self, trades: List[Dict[str, Any]]) -> tuple[List[str], List[str]]:
        """Validate individual trades"""
        errors = []
        warnings = []
        
        required_fields = ['ticket', 'open_time', 'type', 'size', 'symbol', 'open_price', 'profit']
        
        for i, trade in enumerate(trades):
            trade_prefix = f"Trade {i+1}"
            
            # Check required fields
            for field in required_fields:
                if field not in trade or trade[field] is None:
                    errors.append(f"{trade_prefix}: Missing required field '{field}'")
            
            # Validate trade type
            if 'type' in trade and trade['type'] not in self.valid_trade_types:
                errors.append(f"{trade_prefix}: Invalid trade type '{trade['type']}'. Must be 'buy' or 'sell'")
            
            # Validate size
            if 'size' in trade and trade['size'] is not None:
                if not isinstance(trade['size'], (int, float)):
                    errors.append(f"{trade_prefix}: Trade size must be numeric")
                elif trade['size'] < self.min_trade_size:
                    errors.append(f"{trade_prefix}: Trade size too small ({trade['size']})")
                elif trade['size'] > self.max_trade_size:
                    warnings.append(f"{trade_prefix}: Very large trade size ({trade['size']})")
            
            # Validate prices
            price_fields = ['open_price', 'close_price', 'stop_loss', 'take_profit']
            for field in price_fields:
                if field in trade and trade[field] is not None:
                    if not isinstance(trade[field], (int, float)):
                        errors.append(f"{trade_prefix}: {field} must be numeric")
                    elif trade[field] < self.min_price:
                        errors.append(f"{trade_prefix}: {field} too low ({trade[field]})")
                    elif trade[field] > self.max_price:
                        warnings.append(f"{trade_prefix}: Very high {field} ({trade[field]})")
            
            # Validate times
            if 'open_time' in trade and trade['open_time']:
                try:
                    open_time = datetime.fromisoformat(trade['open_time'].replace('Z', '+00:00'))
                    if open_time > datetime.now():
                        warnings.append(f"{trade_prefix}: Open time is in the future")
                except (ValueError, TypeError):
                    errors.append(f"{trade_prefix}: Invalid open_time format")
            
            if 'close_time' in trade and trade['close_time']:
                try:
                    close_time = datetime.fromisoformat(trade['close_time'].replace('Z', '+00:00'))
                    if 'open_time' in trade and trade['open_time']:
                        open_time = datetime.fromisoformat(trade['open_time'].replace('Z', '+00:00'))
                        if close_time < open_time:
                            errors.append(f"{trade_prefix}: Close time before open time")
                except (ValueError, TypeError):
                    errors.append(f"{trade_prefix}: Invalid close_time format")
            
            # Validate profit consistency
            if all(field in trade and trade[field] is not None for field in ['open_price', 'close_price', 'size', 'type']):
                calculated_profit = await self._calculate_expected_profit(trade)
                actual_profit = trade.get('profit', 0)
                
                # Allow for some tolerance due to spreads, commissions, etc.
                tolerance = abs(calculated_profit * 0.1)  # 10% tolerance
                if abs(actual_profit - calculated_profit) > max(tolerance, 1.0):
                    warnings.append(f"{trade_prefix}: Profit inconsistency. Expected ~{calculated_profit:.2f}, got {actual_profit:.2f}")
            
            # Validate symbol format
            if 'symbol' in trade and trade['symbol']:
                symbol = str(trade['symbol']).upper()
                if len(symbol) < 6 or len(symbol) > 8:
                    warnings.append(f"{trade_prefix}: Unusual symbol format '{symbol}'")
                if not symbol.replace('/', '').replace('.', '').isalpha():
                    warnings.append(f"{trade_prefix}: Symbol contains non-alphabetic characters")
        
        return errors, warnings
    
    async def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata"""
        errors = []
        
        required_fields = ['source', 'total_trades', 'date_range']
        
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing metadata field '{field}'")
        
        # Validate date range
        if 'date_range' in metadata:
            date_range = metadata['date_range']
            if not isinstance(date_range, dict):
                errors.append("date_range must be a dictionary")
            else:
                if 'start' not in date_range or 'end' not in date_range:
                    errors.append("date_range must contain 'start' and 'end' fields")
                else:
                    try:
                        start = datetime.fromisoformat(date_range['start'].replace('Z', '+00:00'))
                        end = datetime.fromisoformat(date_range['end'].replace('Z', '+00:00'))
                        if start > end:
                            errors.append("date_range start is after end")
                    except (ValueError, TypeError, AttributeError):
                        errors.append("Invalid date format in date_range")
        
        # Validate numeric fields
        numeric_fields = ['total_trades', 'leverage']
        for field in numeric_fields:
            if field in metadata and metadata[field] is not None:
                if not isinstance(metadata[field], (int, float)):
                    errors.append(f"Metadata field '{field}' must be numeric")
                elif field == 'total_trades' and metadata[field] < 0:
                    errors.append("total_trades cannot be negative")
                elif field == 'leverage' and metadata[field] <= 0:
                    errors.append("leverage must be positive")
        
        return errors
    
    async def _validate_consistency(self, data: Dict[str, Any]) -> List[str]:
        """Validate data consistency"""
        errors = []
        
        trades = data.get('trades', [])
        metadata = data.get('metadata', {})
        
        # Check trade count consistency
        if 'total_trades' in metadata:
            if metadata['total_trades'] != len(trades):
                errors.append(f"Metadata total_trades ({metadata['total_trades']}) doesn't match actual trade count ({len(trades)})")
        
        # Check date range consistency
        if trades and 'date_range' in metadata:
            try:
                trade_dates = []
                for trade in trades:
                    if 'open_time' in trade and trade['open_time']:
                        trade_dates.append(datetime.fromisoformat(trade['open_time'].replace('Z', '+00:00')))
                    if 'close_time' in trade and trade['close_time']:
                        trade_dates.append(datetime.fromisoformat(trade['close_time'].replace('Z', '+00:00')))
                
                if trade_dates:
                    actual_start = min(trade_dates)
                    actual_end = max(trade_dates)
                    
                    metadata_start = datetime.fromisoformat(metadata['date_range']['start'].replace('Z', '+00:00'))
                    metadata_end = datetime.fromisoformat(metadata['date_range']['end'].replace('Z', '+00:00'))
                    
                    # Allow for small discrepancies
                    tolerance = timedelta(days=1)
                    if abs((actual_start - metadata_start).total_seconds()) > tolerance.total_seconds():
                        errors.append("Metadata date range start doesn't match actual trade dates")
                    if abs((actual_end - metadata_end).total_seconds()) > tolerance.total_seconds():
                        errors.append("Metadata date range end doesn't match actual trade dates")
            
            except (ValueError, TypeError, AttributeError):
                errors.append("Error validating date range consistency")
        
        return errors
    
    async def _calculate_expected_profit(self, trade: Dict[str, Any]) -> float:
        """Calculate expected profit based on trade parameters"""
        
        open_price = trade['open_price']
        close_price = trade['close_price']
        size = trade['size']
        trade_type = trade['type']
        symbol = trade.get('symbol', '')
        
        # Determine contract size (simplified)
        if 'JPY' in symbol:
            contract_size = 100000  # Standard lot for JPY pairs
        else:
            contract_size = 100000  # Standard lot for most pairs
        
        # Calculate pip value (simplified)
        if 'JPY' in symbol:
            pip_value = (0.01 / close_price) * contract_size * size
        else:
            pip_value = (0.0001 / close_price) * contract_size * size
        
        # Calculate pips
        if trade_type == 'buy':
            pips = (close_price - open_price) * (10000 if 'JPY' not in symbol else 100)
        else:
            pips = (open_price - close_price) * (10000 if 'JPY' not in symbol else 100)
        
        # Calculate profit (very simplified)
        profit = pips * pip_value
        
        return profit
    
    async def generate_quality_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive data quality report"""
        
        trades = data.get('trades', [])
        if not trades:
            return {"error": "No trades to analyze"}
        
        # Basic statistics
        total_trades = len(trades)
        closed_trades = len([t for t in trades if t.get('close_time')])
        open_trades = total_trades - closed_trades
        
        # Profit statistics
        profits = [t.get('profit', 0) for t in trades]
        winning_trades = len([p for p in profits if p > 0])
        losing_trades = len([p for p in profits if p < 0])
        
        # Time analysis
        trade_dates = []
        for trade in trades:
            if 'open_time' in trade and trade['open_time']:
                try:
                    trade_dates.append(datetime.fromisoformat(trade['open_time'].replace('Z', '+00:00')))
                except:
                    pass
        
        # Symbol analysis
        symbols = [t.get('symbol', '') for t in trades]
        unique_symbols = list(set(symbols))
        
        # Data completeness
        completeness = {}
        optional_fields = ['close_time', 'close_price', 'stop_loss', 'take_profit', 'duration', 'pips']
        for field in optional_fields:
            non_null_count = len([t for t in trades if t.get(field) is not None])
            completeness[field] = non_null_count / total_trades if total_trades > 0 else 0
        
        return {
            "summary": {
                "total_trades": total_trades,
                "closed_trades": closed_trades,
                "open_trades": open_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": winning_trades / total_trades if total_trades > 0 else 0,
                "unique_symbols": len(unique_symbols),
                "date_span_days": (max(trade_dates) - min(trade_dates)).days if len(trade_dates) > 1 else 0
            },
            "data_completeness": completeness,
            "symbols": unique_symbols,
            "quality_score": await self._calculate_quality_score(data)
        }
    
    async def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall data quality score (0-100)"""
        
        score = 100.0
        trades = data.get('trades', [])
        
        if not trades:
            return 0.0
        
        # Penalize missing data
        total_fields = len(trades) * 7  # Assuming 7 important fields per trade
        missing_fields = 0
        
        for trade in trades:
            important_fields = ['ticket', 'open_time', 'type', 'size', 'symbol', 'open_price', 'profit']
            for field in important_fields:
                if field not in trade or trade[field] is None:
                    missing_fields += 1
        
        if total_fields > 0:
            score -= (missing_fields / total_fields) * 30  # Up to 30 points for completeness
        
        # Penalize inconsistencies
        validation_result = await self.validate_trading_data(data)
        error_count = len(validation_result.get('errors', []))
        warning_count = len(validation_result.get('warnings', []))
        
        score -= error_count * 10  # 10 points per error
        score -= warning_count * 2  # 2 points per warning
        
        return max(0.0, min(100.0, score))