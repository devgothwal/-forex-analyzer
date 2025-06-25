// Core plugin system interfaces - Foundation for extensibility

export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  dependencies?: string[];
  permissions?: string[];
  api_version: string;
}

export interface AnalysisPlugin {
  manifest: PluginManifest;
  initialize(config: Record<string, any>): Promise<void>;
  analyze(data: TradingData): Promise<AnalysisResult>;
  visualize?(results: AnalysisResult): Promise<VisualizationData>;
  getInsights(results: AnalysisResult): Promise<Insight[]>;
  cleanup?(): Promise<void>;
}

export interface DataSourcePlugin {
  manifest: PluginManifest;
  validate(file: File): Promise<boolean>;
  parse(file: File): Promise<TradingData>;
  getSchema(): Promise<DataSchema>;
  getSampleData?(): Promise<TradingData>;
}

export interface ComponentPlugin {
  manifest: PluginManifest;
  component: React.ComponentType<any>;
  routes?: Route[];
  menuItems?: MenuItem[];
  hooks?: CustomHook[];
}

export interface TradingData {
  trades: Trade[];
  metadata: DataMetadata;
  timeRange: {
    start: Date;
    end: Date;
  };
}

export interface Trade {
  ticket: string;
  openTime: Date;
  closeTime?: Date;
  type: 'buy' | 'sell';
  size: number;
  symbol: string;
  openPrice: number;
  closePrice?: number;
  stopLoss?: number;
  takeProfit?: number;
  commission: number;
  swap: number;
  profit: number;
  duration?: number;
  pips?: number;
}

export interface DataMetadata {
  source: string;
  account: string;
  currency: string;
  leverage: number;
  totalTrades: number;
  dateRange: {
    start: Date;
    end: Date;
  };
}

export interface AnalysisResult {
  analysisType: string;
  timestamp: Date;
  data: Record<string, any>;
  metadata: {
    pluginName: string;
    version: string;
    executionTime: number;
  };
}

export interface Insight {
  id: string;
  type: 'warning' | 'success' | 'info' | 'critical';
  title: string;
  description: string;
  recommendation?: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  category: string;
  data?: Record<string, any>;
}

export interface VisualizationData {
  type: 'chart' | 'table' | 'heatmap' | 'custom';
  config: Record<string, any>;
  data: any[];
  options?: Record<string, any>;
}

export interface DataSchema {
  fields: FieldDefinition[];
  requiredFields: string[];
  optionalFields: string[];
}

export interface FieldDefinition {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean';
  required: boolean;
  format?: string;
  validation?: ValidationRule[];
}

export interface ValidationRule {
  type: string;
  value: any;
  message: string;
}

export interface Route {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  permissions?: string[];
}

export interface MenuItem {
  label: string;
  path?: string;
  icon?: string;
  children?: MenuItem[];
  permissions?: string[];
}

export interface CustomHook {
  name: string;
  hook: (...args: any[]) => any;
}

// Event system for plugin communication
export interface PluginEvent {
  type: string;
  payload: any;
  source: string;
  timestamp: Date;
}

export interface EventHandler {
  (event: PluginEvent): void | Promise<void>;
}