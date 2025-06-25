// Core trading data types - Shared with backend

export interface Trade {
  ticket: string;
  open_time: string;
  close_time?: string;
  type: 'buy' | 'sell';
  size: number;
  symbol: string;
  open_price: number;
  close_price?: number;
  stop_loss?: number;
  take_profit?: number;
  commission: number;
  swap: number;
  profit: number;
  duration?: number;
  pips?: number;
  risk_reward_ratio?: number;
}

export interface DataMetadata {
  source: string;
  account: string;
  currency: string;
  leverage: number;
  total_trades: number;
  date_range: {
    start: string;
    end: string;
  };
  balance_start?: number;
  balance_end?: number;
  equity_high?: number;
  equity_low?: number;
}

export interface TradingData {
  trades: Trade[];
  metadata: DataMetadata;
}

export interface SummaryStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit: number;
  average_win: number;
  average_loss: number;
  profit_factor: number;
  largest_win: number;
  largest_loss: number;
}

export interface AnalysisRequest {
  data_id: string;
  analysis_type: string;
  parameters: Record<string, any>;
  plugins?: string[];
}

export interface AnalysisResult {
  analysis_id: string;
  analysis_type: string;
  timestamp: string;
  data: Record<string, any>;
  metadata: Record<string, any>;
  execution_time: number;
  status: string;
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
  created_at: string;
}

export interface VisualizationData {
  type: 'chart' | 'table' | 'heatmap' | 'custom';
  config: Record<string, any>;
  data: any[];
  options?: Record<string, any>;
}

export interface UploadResponse {
  data_id: string;
  filename: string;
  size: number;
  records_count: number;
  validation_status: string;
  validation_errors: string[];
  summary_stats: SummaryStats;
  upload_time: string;
}

export interface Dataset {
  data_id: string;
  metadata: DataMetadata;
  summary_stats: SummaryStats;
  upload_time: string;
  trade_count: number;
  date_range: {
    start: string;
    end: string;
  };
}

// Chart data types
export interface ChartDataPoint {
  x: number | string;
  y: number;
  [key: string]: any;
}

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
  [key: string]: any;
}

export interface HeatmapPoint {
  x: number | string;
  y: number | string;
  value: number;
}

// Plugin types
export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  dependencies?: string[];
  permissions?: string[];
  api_version: string;
}

export interface Plugin {
  manifest: PluginManifest;
  status: 'discovered' | 'loading' | 'active' | 'error' | 'disabled';
}

export interface AnalysisType {
  name: string;
  description: string;
  parameters?: Record<string, any>;
  type?: 'built_in' | 'plugin';
  version?: string;
}