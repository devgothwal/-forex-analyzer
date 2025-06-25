"""
cTrader Data Source Plugin - Parse cTrader trading platform exports
Demonstrates data source plugin extensibility
"""

import pandas as pd
import io
from typing import Dict, Any, List
from datetime import datetime
import logging

# Import base plugin interface
import sys
sys.path.append('../../../backend/app')
from core.plugin_manager import DataSourcePlugin, PluginManifest

logger = logging.getLogger(__name__)


class Plugin(DataSourcePlugin):
    """cTrader Data Source Plugin"""
    
    def __init__(self, manifest: PluginManifest):
        super().__init__(manifest)
        self.supported_formats = ['.csv', '.xlsx']
        
        # cTrader column mappings
        self.ctrader_columns = {
            'Position ID': 'ticket',
            'Symbol': 'symbol',
            'Side': 'type',
            'Volume': 'size',
            'Entry Price': 'open_price',
            'Exit Price': 'close_price',
            'Entry Time': 'open_time',
            'Exit Time': 'close_time',
            'Gross P&L': 'profit',
            'Commission': 'commission',
            'Swap': 'swap',
            'Net P&L': 'net_profit',
            'Stop Loss': 'stop_loss',
            'Take Profit': 'take_profit'
        }
        
        # Alternative column names cTrader might use
        self.alternative_columns = {
            'Deal': 'ticket',
            'Deal ID': 'ticket',
            'Position': 'ticket',
            'Instrument': 'symbol',
            'Currency Pair': 'symbol',
            'Direction': 'type',
            'Trade Type': 'type',
            'Quantity': 'size',
            'Amount': 'size',
            'Open Price': 'open_price',
            'Close Price': 'close_price',
            'Open Time': 'open_time',
            'Close Time': 'close_time',
            'Opening Time': 'open_time',
            'Closing Time': 'close_time',
            'P&L': 'profit',
            'Profit/Loss': 'profit',
            'PnL': 'profit',
            'Fees': 'commission',
            'Rollover': 'swap',
            'Interest': 'swap'
        }
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration"""
        logger.info("cTrader Data Source Plugin initialized")
    
    async def validate(self, file_data: bytes) -> bool:
        """Validate if file is a cTrader export"""
        
        try:
            # Try to read as CSV first
            df = pd.read_csv(io.BytesIO(file_data))
            
            # Check for cTrader-specific column patterns
            columns = [col.strip() for col in df.columns]
            
            # Look for characteristic cTrader columns
            ctrader_indicators = [
                'Position ID', 'Deal', 'Deal ID',
                'Symbol', 'Instrument', 'Currency Pair',
                'Side', 'Direction', 'Trade Type',
                'Volume', 'Quantity', 'Amount',
                'Entry Price', 'Open Price',
                'Entry Time', 'Open Time', 'Opening Time',
                'Gross P&L', 'Net P&L', 'P&L', 'PnL'
            ]
            
            # Check if we have at least 3 characteristic columns
            matches = sum(1 for indicator in ctrader_indicators 
                         if any(indicator.lower() in col.lower() for col in columns))
            
            if matches >= 3:
                logger.info(f"cTrader format detected with {matches} matching columns")
                return True
            
            # Check for specific cTrader headers or metadata
            first_few_rows = df.head().to_string().lower()
            if any(keyword in first_few_rows for keyword in ['ctrader', 'spotware', 'icmarkets', 'pepperstone']):
                logger.info("cTrader format detected by metadata")
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"CSV validation failed: {e}")
            
            # Try Excel format
            try:
                df = pd.read_excel(io.BytesIO(file_data))
                columns = [col.strip() for col in df.columns]
                
                ctrader_indicators = [
                    'Position ID', 'Deal', 'Symbol', 'Side', 'Volume',
                    'Entry Price', 'Entry Time', 'Gross P&L'
                ]
                
                matches = sum(1 for indicator in ctrader_indicators 
                             if any(indicator.lower() in col.lower() for col in columns))
                
                return matches >= 3
                
            except Exception as e2:
                logger.debug(f"Excel validation failed: {e2}")
                return False
    
    async def parse(self, file_data: bytes) -> Dict[str, Any]:
        """Parse cTrader export file"""
        
        try:
            # Try CSV first
            try:
                df = pd.read_csv(io.BytesIO(file_data))
            except:
                # Fallback to Excel
                df = pd.read_excel(io.BytesIO(file_data))
            
            logger.info(f"Loaded cTrader data with {len(df)} rows and columns: {list(df.columns)}")
            
            # Clean and standardize column names
            df.columns = [col.strip() for col in df.columns]
            
            # Map cTrader columns to standard format
            df_standardized = await self._standardize_columns(df)
            
            # Clean and validate data
            df_clean = await self._clean_data(df_standardized)
            
            # Extract trades and metadata
            trades = await self._extract_trades(df_clean)
            metadata = await self._extract_metadata(df_clean)
            
            return {
                "trades": trades,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing cTrader file: {e}")
            raise
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get expected data schema for cTrader files"""
        
        return {
            "format": "cTrader",
            "description": "cTrader trading platform export format",
            "required_fields": [
                "Position ID or Deal ID",
                "Symbol",
                "Side or Direction", 
                "Volume",
                "Entry Price",
                "Entry Time"
            ],
            "optional_fields": [
                "Exit Price",
                "Exit Time", 
                "Stop Loss",
                "Take Profit",
                "Commission",
                "Swap",
                "Gross P&L",
                "Net P&L"
            ],
            "supported_formats": self.supported_formats,
            "column_mappings": self.ctrader_columns,
            "alternative_mappings": self.alternative_columns
        }
    
    async def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize cTrader column names to internal format"""
        
        df_renamed = df.copy()
        columns_mapped = {}
        
        # First pass: exact matches
        for ctrader_col, standard_col in self.ctrader_columns.items():
            if ctrader_col in df.columns:
                columns_mapped[ctrader_col] = standard_col
        
        # Second pass: alternative names
        for alt_col, standard_col in self.alternative_columns.items():
            if alt_col in df.columns and standard_col not in columns_mapped.values():
                columns_mapped[alt_col] = standard_col
        
        # Third pass: fuzzy matching for similar column names
        remaining_columns = [col for col in df.columns if col not in columns_mapped]
        
        for remaining_col in remaining_columns:
            remaining_lower = remaining_col.lower().strip()
            
            # Try to match against standard names
            if 'id' in remaining_lower and ('position' in remaining_lower or 'deal' in remaining_lower):
                if 'ticket' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'ticket'
            elif 'symbol' in remaining_lower or 'instrument' in remaining_lower or 'pair' in remaining_lower:
                if 'symbol' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'symbol'
            elif 'side' in remaining_lower or 'direction' in remaining_lower or 'type' in remaining_lower:
                if 'type' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'type'
            elif 'volume' in remaining_lower or 'quantity' in remaining_lower or 'amount' in remaining_lower:
                if 'size' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'size'
            elif 'entry' in remaining_lower and 'price' in remaining_lower:
                if 'open_price' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'open_price'
            elif 'exit' in remaining_lower and 'price' in remaining_lower:
                if 'close_price' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'close_price'
            elif 'entry' in remaining_lower and 'time' in remaining_lower:
                if 'open_time' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'open_time'
            elif 'exit' in remaining_lower and 'time' in remaining_lower:
                if 'close_time' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'close_time'
            elif 'p&l' in remaining_lower or 'pnl' in remaining_lower or 'profit' in remaining_lower:
                if 'profit' not in columns_mapped.values():
                    columns_mapped[remaining_col] = 'profit'
        
        # Apply column mappings
        df_renamed = df_renamed.rename(columns=columns_mapped)
        
        logger.info(f"Mapped {len(columns_mapped)} columns: {columns_mapped}")
        
        return df_renamed
    
    async def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate cTrader data"""
        
        df_clean = df.copy()
        
        # Convert data types
        df_clean = await self._convert_data_types(df_clean)
        
        # Handle missing values
        df_clean = await self._handle_missing_values(df_clean)
        
        # Remove invalid trades
        df_clean = await self._remove_invalid_trades(df_clean)
        
        # Calculate additional fields
        df_clean = await self._calculate_additional_fields(df_clean)
        
        logger.info(f"Cleaned cTrader data: {len(df_clean)} valid trades")
        
        return df_clean
    
    async def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types"""
        
        df_converted = df.copy()
        
        # Convert datetime columns
        datetime_columns = ['open_time', 'close_time']
        for col in datetime_columns:
            if col in df_converted.columns:
                # cTrader often uses specific datetime formats
                df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce', 
                                                  format='%d/%m/%Y %H:%M:%S', dayfirst=True)
                # Try alternative formats if first attempt failed
                if df_converted[col].isna().all():
                    df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = ['size', 'open_price', 'close_price', 'stop_loss', 'take_profit',
                          'commission', 'swap', 'profit', 'net_profit']
        for col in numeric_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
        
        # Convert trade type - cTrader uses "Buy"/"Sell"
        if 'type' in df_converted.columns:
            df_converted['type'] = df_converted['type'].astype(str).str.lower()
            # Standardize trade types
            type_mapping = {
                'buy': 'buy', 'long': 'buy', 'b': 'buy',
                'sell': 'sell', 'short': 'sell', 's': 'sell'
            }
            df_converted['type'] = df_converted['type'].map(type_mapping)
        
        # Convert ticket to string
        if 'ticket' in df_converted.columns:
            df_converted['ticket'] = df_converted['ticket'].astype(str)
        
        return df_converted
    
    async def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing and invalid values"""
        
        df_handled = df.copy()
        
        # Fill missing stop loss and take profit with None/0
        for col in ['stop_loss', 'take_profit']:
            if col in df_handled.columns:
                df_handled[col] = df_handled[col].fillna(0)
        
        # Fill missing commission and swap with 0
        for col in ['commission', 'swap']:
            if col in df_handled.columns:
                df_handled[col] = df_handled[col].fillna(0)
        
        # Use net_profit if available and profit is missing
        if 'net_profit' in df_handled.columns and 'profit' in df_handled.columns:
            df_handled['profit'] = df_handled['profit'].fillna(df_handled['net_profit'])
        
        return df_handled
    
    async def _remove_invalid_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove trades with invalid data"""
        
        initial_count = len(df)
        
        # Remove trades with missing essential data
        essential_columns = ['ticket', 'open_time', 'type', 'size', 'symbol', 'open_price']
        available_essential = [col for col in essential_columns if col in df.columns]
        
        df_valid = df.dropna(subset=available_essential)
        
        # Remove trades with invalid sizes
        if 'size' in df_valid.columns:
            df_valid = df_valid[df_valid['size'] > 0]
        
        # Remove trades with invalid prices
        if 'open_price' in df_valid.columns:
            df_valid = df_valid[df_valid['open_price'] > 0]
        
        # Remove trades with invalid types
        if 'type' in df_valid.columns:
            df_valid = df_valid[df_valid['type'].isin(['buy', 'sell'])]
        
        removed_count = initial_count - len(df_valid)
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} invalid trades from cTrader data")
        
        return df_valid
    
    async def _calculate_additional_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional fields like duration, pips, etc."""
        
        df_calc = df.copy()
        
        # Calculate trade duration in minutes
        if 'close_time' in df_calc.columns and 'open_time' in df_calc.columns:
            mask = df_calc['close_time'].notna() & df_calc['open_time'].notna()
            if mask.any():
                df_calc.loc[mask, 'duration'] = (
                    df_calc.loc[mask, 'close_time'] - df_calc.loc[mask, 'open_time']
                ).dt.total_seconds() / 60
        
        # Calculate pips (simplified calculation)
        if all(col in df_calc.columns for col in ['close_price', 'open_price', 'type', 'symbol']):
            for idx in df_calc.index:
                if pd.notna(df_calc.loc[idx, 'close_price']) and pd.notna(df_calc.loc[idx, 'open_price']):
                    symbol = str(df_calc.loc[idx, 'symbol']).upper()
                    
                    # Determine pip multiplier based on currency pair
                    if 'JPY' in symbol or 'HUF' in symbol:
                        pip_multiplier = 100  # 2 decimal places
                    else:
                        pip_multiplier = 10000  # 4 decimal places
                    
                    # Calculate pips based on trade direction
                    if df_calc.loc[idx, 'type'] == 'buy':
                        pips = (df_calc.loc[idx, 'close_price'] - df_calc.loc[idx, 'open_price']) * pip_multiplier
                    else:
                        pips = (df_calc.loc[idx, 'open_price'] - df_calc.loc[idx, 'close_price']) * pip_multiplier
                    
                    df_calc.loc[idx, 'pips'] = pips
        
        return df_calc
    
    async def _extract_trades(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract trades from cleaned DataFrame"""
        
        trades = []
        
        for _, row in df.iterrows():
            trade = {
                'ticket': str(row.get('ticket', '')),
                'open_time': row['open_time'].isoformat() if pd.notna(row.get('open_time')) else None,
                'close_time': row['close_time'].isoformat() if pd.notna(row.get('close_time')) else None,
                'type': row.get('type', ''),
                'size': float(row.get('size', 0)),
                'symbol': str(row.get('symbol', '')),
                'open_price': float(row.get('open_price', 0)),
                'close_price': float(row['close_price']) if pd.notna(row.get('close_price')) else None,
                'stop_loss': float(row['stop_loss']) if pd.notna(row.get('stop_loss', 0)) and row.get('stop_loss', 0) != 0 else None,
                'take_profit': float(row['take_profit']) if pd.notna(row.get('take_profit', 0)) and row.get('take_profit', 0) != 0 else None,
                'commission': float(row.get('commission', 0)),
                'swap': float(row.get('swap', 0)),
                'profit': float(row.get('profit', 0)),
                'duration': int(row['duration']) if pd.notna(row.get('duration')) else None,
                'pips': float(row['pips']) if pd.notna(row.get('pips')) else None
            }
            trades.append(trade)
        
        return trades
    
    async def _extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract metadata from cTrader data"""
        
        metadata = {
            'source': 'cTrader',
            'account': 'unknown',  # cTrader doesn't always include account info
            'currency': 'USD',  # Default, would need to be determined from data
            'leverage': 100,  # Default, cTrader doesn't typically include this
            'total_trades': len(df),
            'date_range': {
                'start': df['open_time'].min().isoformat() if not df.empty and 'open_time' in df.columns else None,
                'end': df['close_time'].max().isoformat() if 'close_time' in df.columns and df['close_time'].notna().any() else df['open_time'].max().isoformat() if not df.empty and 'open_time' in df.columns else None
            }
        }
        
        # Try to extract account currency from symbols
        if not df.empty and 'symbol' in df.columns:
            symbols = df['symbol'].unique()
            # Look for common base currencies in symbols
            for symbol in symbols:
                symbol_str = str(symbol).upper()
                if symbol_str.endswith('USD'):
                    metadata['currency'] = 'USD'
                    break
                elif symbol_str.endswith('EUR'):
                    metadata['currency'] = 'EUR'
                    break
                elif symbol_str.endswith('GBP'):
                    metadata['currency'] = 'GBP'
                    break
        
        return metadata
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        logger.info("cTrader Data Source Plugin cleanup completed")


# Plugin metadata for registration
PLUGIN_MANIFEST = {
    "name": "ctrader_parser",
    "version": "1.0.0",
    "description": "cTrader trading platform data parser plugin",
    "author": "Forex Analyzer Team",
    "api_version": "1.0"
}