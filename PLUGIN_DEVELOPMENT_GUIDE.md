# Plugin Development Guide

A comprehensive guide for extending the Forex Analyzer platform through custom plugins.

## 🎯 Overview

The Forex Analyzer platform is built with a **modular plugin architecture** that allows developers to easily extend functionality without modifying core code. This guide covers how to create, deploy, and maintain plugins.

## 🔌 Plugin Types

### 1. **Analysis Plugins**
Extend the ML and analytical capabilities of the platform.

**Use Cases:**
- Custom risk metrics
- Advanced trading algorithms
- Sentiment analysis
- Economic indicator integration

### 2. **Data Source Plugins**
Add support for new trading platforms and data formats.

**Use Cases:**
- New broker platforms (TradingView, eToro, etc.)
- Alternative data sources (news, sentiment)
- Custom CSV/Excel formats
- Real-time data feeds

### 3. **Visualization Plugins**
Create custom charts and visual components.

**Use Cases:**
- 3D portfolio visualizations
- Custom chart types
- Interactive dashboards
- Real-time data displays

## 📁 Plugin Structure

Every plugin follows a standardized structure:

```
my-plugin/
├── manifest.json          # Plugin metadata and configuration
├── plugin.py              # Main plugin implementation (backend)
├── component.tsx           # React component (frontend, optional)
├── requirements.txt        # Python dependencies (optional)
├── package.json           # Node.js dependencies (optional)
├── README.md              # Plugin documentation
└── tests/                 # Plugin tests
    ├── test_plugin.py
    └── test_component.tsx
```

## 🛠️ Creating an Analysis Plugin

### Step 1: Create Plugin Structure

```bash
mkdir -p plugins/analysis-plugins/my-analysis-plugin
cd plugins/analysis-plugins/my-analysis-plugin
```

### Step 2: Create Manifest

```json
{
  "name": "my_analysis",
  "version": "1.0.0",
  "description": "My custom trading analysis plugin",
  "author": "Your Name",
  "api_version": "1.0",
  "dependencies": [
    "numpy>=1.20.0",
    "pandas>=1.5.0"
  ],
  "permissions": [
    "data.read",
    "analysis.write"
  ]
}
```

### Step 3: Implement Plugin Logic

```python
# plugin.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
import logging

# Import base plugin interface
import sys
sys.path.append('../../../backend/app')
from core.plugin_manager import AnalysisPlugin, PluginManifest

logger = logging.getLogger(__name__)

class Plugin(AnalysisPlugin):
    """My Custom Analysis Plugin"""
    
    def __init__(self, manifest: PluginManifest):
        super().__init__(manifest)
        self.custom_parameter = 0.5
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration"""
        self.custom_parameter = config.get('custom_parameter', 0.5)
        logger.info(f"Plugin initialized with parameter: {self.custom_parameter}")
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform custom analysis on trading data"""
        
        trades = data['trades']
        if not trades:
            return {"error": "No trades provided"}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(trades)
        
        # Your custom analysis logic here
        results = {
            'custom_metric': self._calculate_custom_metric(df),
            'analysis_summary': {
                'total_trades_analyzed': len(df),
                'analysis_timestamp': datetime.now().isoformat(),
                'parameter_used': self.custom_parameter
            }
        }
        
        return results
    
    async def get_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from analysis results"""
        
        insights = []
        
        custom_metric = results.get('custom_metric', 0)
        
        if custom_metric > 0.8:
            insights.append({
                "type": "success",
                "title": "Excellent Custom Score",
                "description": f"Your custom metric score of {custom_metric:.2f} indicates strong performance.",
                "recommendation": "Maintain your current trading approach.",
                "confidence": 0.85,
                "impact": "medium",
                "category": "performance",
                "data": {"metric_value": custom_metric}
            })
        elif custom_metric < 0.3:
            insights.append({
                "type": "warning",
                "title": "Low Custom Score",
                "description": f"Your custom metric score of {custom_metric:.2f} suggests areas for improvement.",
                "recommendation": "Review your trading strategy and consider adjustments.",
                "confidence": 0.75,
                "impact": "high",
                "category": "performance",
                "data": {"metric_value": custom_metric}
            })
        
        return insights
    
    def _calculate_custom_metric(self, df: pd.DataFrame) -> float:
        """Calculate your custom trading metric"""
        
        # Example: Calculate a custom profitability score
        if 'profit' not in df.columns:
            return 0.0
        
        profits = df['profit']
        positive_trades = len(profits[profits > 0])
        total_trades = len(profits)
        avg_profit = profits.mean()
        
        # Custom formula combining win rate and average profit
        win_rate = positive_trades / total_trades if total_trades > 0 else 0
        normalized_profit = max(0, min(1, (avg_profit + 100) / 200))  # Normalize to 0-1
        
        custom_score = (win_rate * 0.6) + (normalized_profit * 0.4)
        
        return float(custom_score)
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources"""
        logger.info("Custom Analysis Plugin cleanup completed")

# Plugin metadata for registration
PLUGIN_MANIFEST = {
    "name": "my_analysis",
    "version": "1.0.0",
    "description": "My custom trading analysis plugin",
    "author": "Your Name",
    "api_version": "1.0"
}
```

### Step 4: Add Configuration (Optional)

```python
# config.py (optional)
DEFAULT_CONFIG = {
    "custom_parameter": 0.5,
    "enable_advanced_analysis": True,
    "cache_results": True,
    "log_level": "INFO"
}

def validate_config(config: dict) -> dict:
    """Validate and sanitize plugin configuration"""
    validated = DEFAULT_CONFIG.copy()
    
    if 'custom_parameter' in config:
        validated['custom_parameter'] = max(0, min(1, float(config['custom_parameter'])))
    
    return validated
```

## 📊 Creating a Data Source Plugin

### Example: Custom CSV Parser

```python
# plugin.py
import pandas as pd
import io
from typing import Dict, Any, List
from datetime import datetime
import logging

from core.plugin_manager import DataSourcePlugin, PluginManifest

class Plugin(DataSourcePlugin):
    """Custom CSV Data Source Plugin"""
    
    def __init__(self, manifest: PluginManifest):
        super().__init__(manifest)
        self.supported_formats = ['.csv']
        
        # Define your custom column mappings
        self.column_mappings = {
            'Trade ID': 'ticket',
            'Pair': 'symbol',
            'Direction': 'type',
            'Volume': 'size',
            'Open Price': 'open_price',
            'Close Price': 'close_price',
            'Open Date': 'open_time',
            'Close Date': 'close_time',
            'Profit': 'profit',
            'Commission': 'commission'
        }
    
    async def validate(self, file_data: bytes) -> bool:
        """Check if file matches your custom format"""
        
        try:
            df = pd.read_csv(io.BytesIO(file_data))
            columns = [col.strip() for col in df.columns]
            
            # Check for your specific column patterns
            required_columns = ['Trade ID', 'Pair', 'Direction']
            matches = sum(1 for col in required_columns if col in columns)
            
            return matches >= 2  # At least 2 required columns
            
        except Exception:
            return False
    
    async def parse(self, file_data: bytes) -> Dict[str, Any]:
        """Parse your custom CSV format"""
        
        df = pd.read_csv(io.BytesIO(file_data))
        
        # Standardize column names
        df = df.rename(columns=self.column_mappings)
        
        # Clean and validate data
        df = self._clean_data(df)
        
        # Extract trades and metadata
        trades = self._extract_trades(df)
        metadata = self._extract_metadata(df)
        
        return {
            "trades": trades,
            "metadata": metadata
        }
    
    async def get_schema(self) -> Dict[str, Any]:
        """Return expected data schema"""
        
        return {
            "format": "Custom CSV",
            "required_fields": list(self.column_mappings.keys()),
            "supported_formats": self.supported_formats,
            "column_mappings": self.column_mappings
        }
```

## 🎨 Creating Frontend Components

### React Component Plugin

```typescript
// component.tsx
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

interface MyPluginComponentProps {
  data?: any;
  config?: any;
}

export const MyPluginComponent: React.FC<MyPluginComponentProps> = ({ 
  data, 
  config 
}) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          My Custom Analysis
        </Typography>
        <Box>
          {data ? (
            <Typography variant="body2">
              Custom Metric: {data.custom_metric?.toFixed(3)}
            </Typography>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No data available
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// Plugin registration
export const PLUGIN_COMPONENT = {
  name: 'my_analysis_component',
  component: MyPluginComponent,
  routes: [
    {
      path: '/analysis/my-custom',
      component: MyPluginComponent,
      exact: true
    }
  ],
  menuItems: [
    {
      label: 'My Analysis',
      path: '/analysis/my-custom',
      permissions: ['analysis.read']
    }
  ]
};
```

## 🧪 Testing Plugins

### Python Tests

```python
# tests/test_plugin.py
import pytest
import pandas as pd
from unittest.mock import AsyncMock

from plugin import Plugin, PLUGIN_MANIFEST

@pytest.fixture
def plugin():
    manifest = type('Manifest', (), PLUGIN_MANIFEST)()
    return Plugin(manifest)

@pytest.fixture
def sample_data():
    return {
        'trades': [
            {
                'ticket': '12345',
                'symbol': 'EURUSD',
                'type': 'buy',
                'size': 0.1,
                'profit': 50.0,
                'open_time': '2024-01-01T10:00:00',
                'close_time': '2024-01-01T11:00:00'
            },
            {
                'ticket': '12346',
                'symbol': 'GBPUSD',
                'type': 'sell',
                'size': 0.2,
                'profit': -25.0,
                'open_time': '2024-01-01T12:00:00',
                'close_time': '2024-01-01T13:00:00'
            }
        ]
    }

@pytest.mark.asyncio
async def test_plugin_initialization(plugin):
    config = {'custom_parameter': 0.7}
    await plugin.initialize(config)
    assert plugin.custom_parameter == 0.7

@pytest.mark.asyncio
async def test_analysis(plugin, sample_data):
    await plugin.initialize({})
    
    results = await plugin.analyze(sample_data)
    
    assert 'custom_metric' in results
    assert 'analysis_summary' in results
    assert results['analysis_summary']['total_trades_analyzed'] == 2

@pytest.mark.asyncio
async def test_insights_generation(plugin, sample_data):
    await plugin.initialize({})
    
    results = await plugin.analyze(sample_data)
    insights = await plugin.get_insights(results)
    
    assert isinstance(insights, list)
    for insight in insights:
        assert 'type' in insight
        assert 'title' in insight
        assert 'description' in insight

def test_custom_metric_calculation(plugin):
    df = pd.DataFrame([
        {'profit': 100},
        {'profit': -50},
        {'profit': 75}
    ])
    
    metric = plugin._calculate_custom_metric(df)
    
    assert 0 <= metric <= 1  # Should be normalized
```

### TypeScript Tests

```typescript
// tests/test_component.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MyPluginComponent } from '../component';

describe('MyPluginComponent', () => {
  test('renders without data', () => {
    render(<MyPluginComponent />);
    
    expect(screen.getByText('My Custom Analysis')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  test('renders with data', () => {
    const testData = {
      custom_metric: 0.756
    };
    
    render(<MyPluginComponent data={testData} />);
    
    expect(screen.getByText('Custom Metric: 0.756')).toBeInTheDocument();
  });
});
```

## 🚀 Plugin Deployment

### Local Development

1. **Place plugin in correct directory:**
   ```bash
   plugins/analysis-plugins/my-plugin/
   ```

2. **Install dependencies:**
   ```bash
   cd plugins/analysis-plugins/my-plugin
   pip install -r requirements.txt  # If applicable
   ```

3. **Load plugin via API:**
   ```bash
   curl -X POST http://localhost:8000/api/plugins/my_analysis/load
   ```

4. **Verify plugin status:**
   ```bash
   curl http://localhost:8000/api/plugins/my_analysis/status
   ```

### Production Deployment

1. **Docker approach:**
   ```dockerfile
   # Add to Dockerfile
   COPY plugins/ /app/plugins/
   RUN pip install -r /app/plugins/my-plugin/requirements.txt
   ```

2. **Plugin marketplace (future):**
   ```bash
   # Future feature
   forex-analyzer plugin install my-plugin
   ```

## 📚 Best Practices

### 1. **Error Handling**
```python
async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Your analysis logic
        pass
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "error": str(e),
            "partial_results": {}  # Return what you can
        }
```

### 2. **Configuration Validation**
```python
def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration with sensible defaults"""
    validated = {
        'parameter1': min(max(config.get('parameter1', 0.5), 0), 1),
        'enable_feature': bool(config.get('enable_feature', True))
    }
    return validated
```

### 3. **Performance Optimization**
```python
async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # Cache expensive computations
    cache_key = self._generate_cache_key(data)
    
    if self.cache.exists(cache_key):
        return self.cache.get(cache_key)
    
    results = self._perform_analysis(data)
    self.cache.set(cache_key, results, ttl=3600)
    
    return results
```

### 4. **Memory Management**
```python
async def cleanup(self) -> None:
    """Clean up resources properly"""
    if hasattr(self, 'large_dataset'):
        del self.large_dataset
    
    if hasattr(self, 'model'):
        self.model.clear()
    
    logger.info("Plugin cleanup completed")
```

## 🔒 Security Considerations

### 1. **Input Validation**
```python
def validate_input(self, data: Dict[str, Any]) -> bool:
    """Validate input data structure and content"""
    
    if not isinstance(data, dict):
        return False
    
    if 'trades' not in data:
        return False
    
    # Check for malicious content
    trades = data['trades']
    if not isinstance(trades, list):
        return False
    
    # Limit data size
    if len(trades) > 100000:  # Reasonable limit
        return False
    
    return True
```

### 2. **Safe File Processing**
```python
async def parse(self, file_data: bytes) -> Dict[str, Any]:
    """Safely parse file data"""
    
    # Check file size
    if len(file_data) > 50 * 1024 * 1024:  # 50MB limit
        raise ValueError("File too large")
    
    # Validate file content
    try:
        # Safe parsing logic
        pass
    except Exception as e:
        logger.warning(f"File parsing failed: {e}")
        raise ValueError("Invalid file format")
```

## 📖 API Reference

### Plugin Base Classes

#### AnalysisPlugin
```python
class AnalysisPlugin:
    async def initialize(self, config: Dict[str, Any]) -> None
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]
    async def get_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]
    async def cleanup(self) -> None
```

#### DataSourcePlugin
```python
class DataSourcePlugin:
    async def validate(self, file_data: bytes) -> bool
    async def parse(self, file_data: bytes) -> Dict[str, Any]
    async def get_schema(self) -> Dict[str, Any]
```

### Event System
```python
# Subscribe to events
event_manager.subscribe('data_uploaded', self.on_data_uploaded)

# Emit custom events
await event_manager.emit('custom_analysis_completed', {
    'plugin': self.manifest.name,
    'results': results
})
```

## 🤝 Contributing Plugins

1. **Fork the repository**
2. **Create plugin in appropriate directory**
3. **Follow naming conventions**: `my_plugin_name`
4. **Include comprehensive tests**
5. **Document configuration options**
6. **Submit pull request with plugin**

## 📞 Support

- **Documentation**: [Plugin API Docs](https://docs.forex-analyzer.com/plugins)
- **Examples**: [Sample Plugins](https://github.com/forex-analyzer/examples)
- **Community**: [Discord #plugin-development](https://discord.gg/forex-analyzer)
- **Issues**: [GitHub Issues](https://github.com/forex-analyzer/issues)

---

**Happy Plugin Development! 🚀**