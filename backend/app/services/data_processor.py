"""
Data Processor Service - Parse and clean MT5/MT4 trading data
Implements standardized data transformation with extensible parsers
"""

import io
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and standardize trading data from various sources"""
    
    def __init__(self):
        self.mt5_columns = {
            'Ticket': 'ticket',
            'Open Time': 'open_time', 
            'Type': 'type',
            'Size': 'size',
            'Symbol': 'symbol',
            'Price': 'open_price',
            'S/L': 'stop_loss',
            'T/P': 'take_profit',
            'Close Time': 'close_time',
            'Close Price': 'close_price',
            'Commission': 'commission',
            'Swap': 'swap',
            'Profit': 'profit'
        }
        
        self.mt4_columns = {
            'Order': 'ticket',
            'Time': 'open_time',
            'Type': 'type', 
            'Size': 'size',
            'Item': 'symbol',
            'Price': 'open_price',
            'S / L': 'stop_loss',
            'T / P': 'take_profit',
            'Time.1': 'close_time',
            'Price.1': 'close_price',
            'Commission': 'commission',
            'Taxes': 'swap',
            'Swap': 'swap',
            'Profit': 'profit'
        }
    
    async def process_file(self, file_content: bytes, filename: str, source: str = "MT5") -> Dict[str, Any]:
        """Process uploaded file and return standardized trading data"""
        
        try:
            # Determine file type and read data
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file format: {filename}")
            
            logger.info(f"Loaded {len(df)} rows from {filename}")
            
            # Auto-detect format and standardize columns
            df_standardized = await self._standardize_columns(df, source)
            
            # Clean and validate data
            df_clean = await self._clean_data(df_standardized)
            
            # Extract trades and metadata
            trades = await self._extract_trades(df_clean)
            metadata = await self._extract_metadata(df_clean, source, filename)
            
            return {
                "trades": trades,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise
    
    async def _standardize_columns(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Standardize column names based on data source"""
        
        # Auto-detect source if not specified
        if source == "auto":
            source = await self._detect_source(df)
        
        # Select appropriate column mapping
        if source.upper() == "MT5":
            column_mapping = self.mt5_columns
        elif source.upper() == "MT4":
            column_mapping = self.mt4_columns
        else:
            # Try to auto-map columns
            column_mapping = await self._auto_map_columns(df)
        
        # Rename columns
        df_renamed = df.copy()
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df_renamed = df_renamed.rename(columns={old_name: new_name})
        
        # Ensure required columns exist
        required_columns = ['ticket', 'open_time', 'type', 'size', 'symbol', 'open_price', 'profit']
        missing_columns = [col for col in required_columns if col not in df_renamed.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        return df_renamed
    
    async def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate trading data"""
        
        df_clean = df.copy()
        
        # Convert data types
        df_clean = await self._convert_data_types(df_clean)
        
        # Handle missing values
        df_clean = await self._handle_missing_values(df_clean)
        
        # Remove invalid trades
        df_clean = await self._remove_invalid_trades(df_clean)
        
        # Calculate additional fields
        df_clean = await self._calculate_additional_fields(df_clean)
        
        # Sort by open time
        df_clean = df_clean.sort_values('open_time').reset_index(drop=True)
        
        logger.info(f"Cleaned data: {len(df_clean)} valid trades")
        
        return df_clean
    
    async def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types"""
        
        df_converted = df.copy()
        
        # Convert datetime columns
        datetime_columns = ['open_time', 'close_time']
        for col in datetime_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_datetime(df_converted[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = [
            'size', 'open_price', 'close_price', 'stop_loss', 'take_profit',
            'commission', 'swap', 'profit'
        ]
        for col in numeric_columns:
            if col in df_converted.columns:
                df_converted[col] = pd.to_numeric(df_converted[col], errors='coerce')
        
        # Convert trade type
        if 'type' in df_converted.columns:
            df_converted['type'] = df_converted['type'].astype(str).str.lower()
            # Standardize trade types
            type_mapping = {
                'buy': 'buy', 'long': 'buy', '0': 'buy', 'op_buy': 'buy',
                'sell': 'sell', 'short': 'sell', '1': 'sell', 'op_sell': 'sell'
            }
            df_converted['type'] = df_converted['type'].map(type_mapping)
        
        # Convert ticket to string
        if 'ticket' in df_converted.columns:
            df_converted['ticket'] = df_converted['ticket'].astype(str)
        
        return df_converted
    
    async def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing and invalid values"""
        
        df_handled = df.copy()
        
        # Fill missing stop loss and take profit with 0
        for col in ['stop_loss', 'take_profit']:
            if col in df_handled.columns:
                df_handled[col] = df_handled[col].fillna(0)
        
        # Fill missing commission and swap with 0
        for col in ['commission', 'swap']:
            if col in df_handled.columns:
                df_handled[col] = df_handled[col].fillna(0)
        
        # Handle missing close times (open trades)
        if 'close_time' in df_handled.columns:
            # For open trades, close_time might be NaT
            pass  # Keep as NaT for open trades
        
        # Handle missing close prices
        if 'close_price' in df_handled.columns:
            # For closed trades, estimate close price if missing
            mask = df_handled['close_time'].notna() & df_handled['close_price'].isna()
            if mask.any():
                # Estimate close price based on profit and trade type
                # This is a rough estimation
                for idx in df_handled[mask].index:
                    trade = df_handled.loc[idx]
                    if trade['profit'] != 0 and trade['size'] != 0:
                        # Very rough estimation - in practice, this would need more sophisticated logic
                        pip_value = 1 if 'JPY' in str(trade['symbol']) else 0.0001
                        estimated_pips = trade['profit'] / (trade['size'] * 100000 * pip_value)
                        if trade['type'] == 'buy':
                            df_handled.loc[idx, 'close_price'] = trade['open_price'] + (estimated_pips * pip_value)
                        else:
                            df_handled.loc[idx, 'close_price'] = trade['open_price'] - (estimated_pips * pip_value)
        
        return df_handled
    
    async def _remove_invalid_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove trades with invalid data"""
        
        initial_count = len(df)
        
        # Remove trades with missing essential data
        df_valid = df.dropna(subset=['ticket', 'open_time', 'type', 'size', 'symbol', 'open_price'])
        
        # Remove trades with invalid sizes
        df_valid = df_valid[df_valid['size'] > 0]
        
        # Remove trades with invalid prices
        df_valid = df_valid[df_valid['open_price'] > 0]
        
        # Remove trades with invalid types
        df_valid = df_valid[df_valid['type'].isin(['buy', 'sell'])]
        
        removed_count = initial_count - len(df_valid)
        if removed_count > 0:
            logger.warning(f"Removed {removed_count} invalid trades")
        
        return df_valid
    
    async def _calculate_additional_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate additional fields like duration, pips, etc."""
        
        df_calc = df.copy()
        
        # Calculate trade duration in minutes
        if 'close_time' in df_calc.columns:
            mask = df_calc['close_time'].notna()
            df_calc.loc[mask, 'duration'] = (
                df_calc.loc[mask, 'close_time'] - df_calc.loc[mask, 'open_time']
            ).dt.total_seconds() / 60
        
        # Calculate pips
        if 'close_price' in df_calc.columns:
            mask = df_calc['close_price'].notna()
            for idx in df_calc[mask].index:
                trade = df_calc.loc[idx]
                symbol = str(trade['symbol']).upper()
                
                # Determine pip multiplier based on currency pair
                if 'JPY' in symbol or 'HUF' in symbol:
                    pip_multiplier = 100  # 2 decimal places
                else:
                    pip_multiplier = 10000  # 4 decimal places
                
                # Calculate pips based on trade direction
                if trade['type'] == 'buy':
                    pips = (trade['close_price'] - trade['open_price']) * pip_multiplier
                else:
                    pips = (trade['open_price'] - trade['close_price']) * pip_multiplier
                
                df_calc.loc[idx, 'pips'] = pips
        
        # Calculate risk-reward ratio
        if all(col in df_calc.columns for col in ['stop_loss', 'take_profit', 'open_price']):
            for idx in df_calc.index:
                trade = df_calc.loc[idx]
                if trade['stop_loss'] > 0 and trade['take_profit'] > 0:
                    if trade['type'] == 'buy':
                        risk = trade['open_price'] - trade['stop_loss']
                        reward = trade['take_profit'] - trade['open_price']
                    else:
                        risk = trade['stop_loss'] - trade['open_price']
                        reward = trade['open_price'] - trade['take_profit']
                    
                    if risk > 0:
                        df_calc.loc[idx, 'risk_reward_ratio'] = reward / risk
        
        return df_calc
    
    async def _extract_trades(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract trades from cleaned DataFrame"""
        
        trades = []
        
        for _, row in df.iterrows():
            trade = {
                'ticket': str(row['ticket']),
                'open_time': row['open_time'].isoformat() if pd.notna(row['open_time']) else None,
                'close_time': row['close_time'].isoformat() if pd.notna(row.get('close_time')) else None,
                'type': row['type'],
                'size': float(row['size']),
                'symbol': str(row['symbol']),
                'open_price': float(row['open_price']),
                'close_price': float(row['close_price']) if pd.notna(row.get('close_price')) else None,
                'stop_loss': float(row['stop_loss']) if pd.notna(row.get('stop_loss', 0)) and row.get('stop_loss', 0) != 0 else None,
                'take_profit': float(row['take_profit']) if pd.notna(row.get('take_profit', 0)) and row.get('take_profit', 0) != 0 else None,
                'commission': float(row.get('commission', 0)),
                'swap': float(row.get('swap', 0)),
                'profit': float(row['profit']),
                'duration': int(row['duration']) if pd.notna(row.get('duration')) else None,
                'pips': float(row['pips']) if pd.notna(row.get('pips')) else None,
                'risk_reward_ratio': float(row['risk_reward_ratio']) if pd.notna(row.get('risk_reward_ratio')) else None
            }
            trades.append(trade)
        
        return trades
    
    async def _extract_metadata(self, df: pd.DataFrame, source: str, filename: str) -> Dict[str, Any]:
        """Extract metadata from trading data"""
        
        metadata = {
            'source': source,
            'filename': filename,
            'account': 'unknown',  # Would need to be extracted from file or provided
            'currency': 'USD',  # Default, would need to be determined
            'leverage': 100,  # Default, would need to be extracted
            'total_trades': len(df),
            'date_range': {
                'start': df['open_time'].min().isoformat() if not df.empty else None,
                'end': df['close_time'].max().isoformat() if 'close_time' in df.columns and df['close_time'].notna().any() else df['open_time'].max().isoformat() if not df.empty else None
            }
        }
        
        # Try to extract account info from symbol patterns or file structure
        if not df.empty:
            # Analyze symbols to determine likely account currency
            symbols = df['symbol'].unique()
            if any('USD' in str(symbol) for symbol in symbols):
                metadata['currency'] = 'USD'
            elif any('EUR' in str(symbol) for symbol in symbols):
                metadata['currency'] = 'EUR'
        
        return metadata
    
    async def _detect_source(self, df: pd.DataFrame) -> str:
        """Auto-detect data source based on column patterns"""
        
        columns = set(df.columns)
        
        # Check for MT5 patterns
        mt5_indicators = {'Ticket', 'Open Time', 'Close Time', 'Symbol', 'Type'}
        if mt5_indicators.issubset(columns):
            return "MT5"
        
        # Check for MT4 patterns  
        mt4_indicators = {'Order', 'Time', 'Item', 'Type'}
        if mt4_indicators.issubset(columns):
            return "MT4"
        
        # Default fallback
        return "Generic"
    
    async def _auto_map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Auto-map columns when source is unknown"""
        
        mapping = {}
        columns = list(df.columns)
        
        # Try to map based on common patterns
        for col in columns:
            col_lower = col.lower().strip()
            
            if any(keyword in col_lower for keyword in ['ticket', 'order', 'id']):
                mapping[col] = 'ticket'
            elif any(keyword in col_lower for keyword in ['open', 'start']) and any(keyword in col_lower for keyword in ['time', 'date']):
                mapping[col] = 'open_time'
            elif any(keyword in col_lower for keyword in ['close', 'end']) and any(keyword in col_lower for keyword in ['time', 'date']):
                mapping[col] = 'close_time'
            elif col_lower in ['type', 'direction', 'side']:
                mapping[col] = 'type'
            elif any(keyword in col_lower for keyword in ['size', 'volume', 'lot']):
                mapping[col] = 'size'
            elif any(keyword in col_lower for keyword in ['symbol', 'pair', 'instrument']):
                mapping[col] = 'symbol'
            elif any(keyword in col_lower for keyword in ['open']) and any(keyword in col_lower for keyword in ['price']):
                mapping[col] = 'open_price'
            elif any(keyword in col_lower for keyword in ['close']) and any(keyword in col_lower for keyword in ['price']):
                mapping[col] = 'close_price'
            elif any(keyword in col_lower for keyword in ['profit', 'pnl', 'p&l']):
                mapping[col] = 'profit'
            elif any(keyword in col_lower for keyword in ['commission', 'fee']):
                mapping[col] = 'commission'
            elif col_lower in ['swap', 'rollover']:
                mapping[col] = 'swap'
            elif any(keyword in col_lower for keyword in ['sl', 'stop']):
                mapping[col] = 'stop_loss'
            elif any(keyword in col_lower for keyword in ['tp', 'take']):
                mapping[col] = 'take_profit'
        
        return mapping