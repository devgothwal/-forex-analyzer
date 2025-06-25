# Contributing to Forex Analyzer

Thank you for your interest in contributing to the Forex Trading Analysis Platform! This document provides guidelines for contributing to this modular, extensible platform.

## 🎯 **Ways to Contribute**

### 1. **Plugin Development** (Primary Focus)
- Create new analysis algorithms
- Add data source parsers
- Build visualization components
- Extend ML capabilities

### 2. **Core Platform Improvements**
- Enhance plugin architecture
- Improve performance optimizations
- Add new API endpoints
- Strengthen security features

### 3. **Documentation & Examples**
- Improve plugin development guides
- Add tutorial content
- Create sample implementations
- Enhance API documentation

## 🔌 **Plugin Contribution Guidelines**

### **Analysis Plugins**
```
plugins/analysis-plugins/your-plugin-name/
├── manifest.json          # Required
├── plugin.py              # Required
├── README.md              # Required
├── requirements.txt        # If needed
└── tests/                 # Recommended
```

### **Data Source Plugins**
```
plugins/data-sources/your-plugin-name/
├── manifest.json          # Required
├── plugin.py              # Required
├── README.md              # Required
└── sample-data/           # Recommended
```

### **Plugin Requirements**
- Follow the plugin interface contracts
- Include comprehensive error handling
- Add unit tests for all functionality
- Document configuration options
- Provide example usage

## 🛠️ **Development Setup**

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Git

### **Setup Steps**
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/forex-analyzer.git
cd forex-analyzer

# Setup development environment
./scripts/deploy.sh setup

# Start development servers
./scripts/deploy.sh dev
```

### **Plugin Development**
```bash
# Create new plugin
mkdir -p plugins/analysis-plugins/my-plugin
cd plugins/analysis-plugins/my-plugin

# Follow the Plugin Development Guide
# See PLUGIN_DEVELOPMENT_GUIDE.md for detailed instructions
```

## 📝 **Pull Request Process**

### **1. Fork & Branch**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/forex-analyzer.git
cd forex-analyzer

# Create feature branch
git checkout -b feature/amazing-plugin
```

### **2. Development**
- Follow the coding standards
- Write comprehensive tests
- Update documentation
- Test on multiple platforms

### **3. Testing**
```bash
# Backend tests
cd backend
pytest tests/ --cov=app

# Frontend tests
cd frontend
npm test

# Plugin tests
pytest tests/plugins/
```

### **4. Submit PR**
- Create descriptive commit messages
- Include screenshots for UI changes
- Reference any related issues
- Ensure CI checks pass

## 🎨 **Coding Standards**

### **Python (Backend)**
- Follow PEP 8 style guide
- Use type hints for all functions
- Include docstrings for public methods
- Maximum line length: 88 characters

```python
async def analyze_data(
    self, 
    data: Dict[str, Any], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze trading data using custom algorithm.
    
    Args:
        data: Trading data dictionary
        config: Optional configuration parameters
        
    Returns:
        Analysis results dictionary
        
    Raises:
        ValueError: If data format is invalid
    """
```

### **TypeScript (Frontend)**
- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Implement proper error boundaries

```typescript
interface AnalysisProps {
  data: TradingData;
  onAnalysisComplete: (results: AnalysisResult) => void;
}

export const AnalysisComponent: React.FC<AnalysisProps> = ({
  data,
  onAnalysisComplete,
}) => {
  // Component implementation
};
```

### **Plugin Architecture**
- Implement all required interface methods
- Use dependency injection patterns
- Follow SOLID principles
- Ensure backward compatibility

## 🧪 **Testing Guidelines**

### **Unit Tests**
- Test all public methods
- Mock external dependencies
- Use descriptive test names
- Aim for >90% code coverage

### **Integration Tests**
- Test plugin loading/unloading
- Verify API endpoint functionality
- Test data processing pipelines
- Validate frontend-backend communication

### **Plugin Tests**
- Test plugin interface compliance
- Verify configuration handling
- Test error scenarios
- Validate output formats

## 📋 **Issue Reporting**

### **Bug Reports**
- Use the bug report template
- Include minimal reproduction steps
- Provide environment details
- Include relevant logs/screenshots

### **Feature Requests**
- Use the feature request template
- Explain the use case clearly
- Consider plugin-based implementation
- Discuss backward compatibility

### **Plugin Ideas**
- Describe the analysis capability
- Identify data requirements
- Consider existing alternatives
- Estimate complexity level

## 🏆 **Recognition**

### **Contributors**
All contributors will be:
- Listed in the README contributors section
- Credited in plugin documentation
- Mentioned in release notes
- Invited to join the core team (for significant contributions)

### **Plugin Authors**
Plugin authors receive:
- Featured plugin showcase
- Developer spotlight articles
- Early access to new features
- Direct feedback channel

## 📚 **Resources**

### **Documentation**
- [Plugin Development Guide](PLUGIN_DEVELOPMENT_GUIDE.md)
- [API Documentation](docs/api/)
- [Architecture Overview](docs/architecture/)

### **Community**
- Discord: [Join our community](https://discord.gg/forex-analyzer)
- GitHub Discussions: [Ask questions](https://github.com/forex-analyzer/discussions)
- Issue Tracker: [Report bugs](https://github.com/forex-analyzer/issues)

### **Examples**
- [Sample Plugins](plugins/)
- [Tutorial Projects](examples/)
- [Best Practices](docs/best-practices/)

## 🔒 **Security**

### **Reporting Vulnerabilities**
- Email: security@forex-analyzer.com
- Use GitHub Security Advisories
- Allow 90 days for response
- No public disclosure until fixed

### **Plugin Security**
- Validate all input data
- Sanitize file uploads
- Limit resource usage
- Use secure dependencies

## 📄 **License**

By contributing, you agree that your contributions will be licensed under the MIT License.

## ✅ **Checklist**

Before submitting a contribution:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are descriptive
- [ ] PR description explains changes
- [ ] Breaking changes are documented
- [ ] Plugin follows interface contracts
- [ ] Security considerations addressed

---

**Thank you for helping make Forex Analyzer the most extensible trading analysis platform! 🚀**