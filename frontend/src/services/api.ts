// API service layer - Centralized HTTP client for backend communication

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  TradingData,
  AnalysisRequest,
  AnalysisResult,
  Insight,
  VisualizationData,
  UploadResponse,
  Dataset,
  Plugin,
  AnalysisType,
} from '@/types/trading';

// API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';

// Create axios instance with default config
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      // Add request timestamp for debugging
      config.metadata = { startTime: Date.now() };
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      // Log request duration
      if (response.config.metadata) {
        const duration = Date.now() - response.config.metadata.startTime;
        console.log(`API Request: ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
      }
      
      return response;
    },
    (error) => {
      // Handle common errors
      if (error.response?.status === 401) {
        // Unauthorized - clear auth and redirect to login
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
      
      // Log error for debugging
      console.error('API Error:', error.response?.data || error.message);
      
      return Promise.reject(error);
    }
  );

  return client;
};

const apiClient = createApiClient();

// Generic API wrapper functions
class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = apiClient;
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.client.delete(url, config);
    return response.data;
  }

  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response: AxiosResponse<T> = await this.client.post(url, formData, config);
    return response.data;
  }
}

const apiService = new ApiService();

// Data management API
export const dataAPI = {
  uploadFile: (file: File, source?: string, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    const url = source ? `/data/upload?source=${source}` : '/data/upload';
    return apiService.upload<UploadResponse>(url, file, onProgress);
  },

  getDatasets: (): Promise<{ datasets: Dataset[] }> => {
    return apiService.get<{ datasets: Dataset[] }>('/data/datasets');
  },

  getDataset: (dataId: string): Promise<Dataset> => {
    return apiService.get<Dataset>(`/data/datasets/${dataId}`);
  },

  deleteDataset: (dataId: string): Promise<{ message: string }> => {
    return apiService.delete<{ message: string }>(`/data/datasets/${dataId}`);
  },

  previewDataset: (dataId: string, limit: number = 10): Promise<{ trades: any[]; total_trades: number }> => {
    return apiService.get<{ trades: any[]; total_trades: number }>(`/data/datasets/${dataId}/preview?limit=${limit}`);
  },

  getSupportedFormats: (): Promise<any> => {
    return apiService.get<any>('/data/supported-formats');
  },
};

// Analysis API
export const analysisAPI = {
  runAnalysis: (request: AnalysisRequest): Promise<AnalysisResult> => {
    return apiService.post<AnalysisResult>('/analysis/run', request);
  },

  getAnalysisResults: (dataId?: string, analysisType?: string, limit: number = 50): Promise<{ results: AnalysisResult[]; total: number }> => {
    const params = new URLSearchParams();
    if (dataId) params.append('data_id', dataId);
    if (analysisType) params.append('analysis_type', analysisType);
    params.append('limit', limit.toString());
    
    return apiService.get<{ results: AnalysisResult[]; total: number }>(`/analysis/results?${params.toString()}`);
  },

  getAnalysisResult: (analysisId: string): Promise<AnalysisResult> => {
    return apiService.get<AnalysisResult>(`/analysis/results/${analysisId}`);
  },

  deleteAnalysisResult: (analysisId: string): Promise<{ message: string }> => {
    return apiService.delete<{ message: string }>(`/analysis/results/${analysisId}`);
  },

  getAnalysisTypes: (): Promise<{ built_in: AnalysisType[]; plugins: AnalysisType[] }> => {
    return apiService.get<{ built_in: AnalysisType[]; plugins: AnalysisType[] }>('/analysis/types');
  },
};

// Insights API
export const insightsAPI = {
  generateInsights: (dataId: string): Promise<Insight[]> => {
    return apiService.post<Insight[]>(`/insights/generate/${dataId}`);
  },

  getInsights: (dataId: string): Promise<Insight[]> => {
    return apiService.get<Insight[]>(`/insights/${dataId}`);
  },

  getInsightsByCategory: (dataId: string): Promise<Record<string, Insight[]>> => {
    return apiService.get<Record<string, Insight[]>>(`/insights/${dataId}/categories`);
  },

  getPriorityInsights: (dataId: string, minConfidence: number = 0.7, maxResults: number = 10): Promise<Insight[]> => {
    return apiService.get<Insight[]>(`/insights/${dataId}/priority?min_confidence=${minConfidence}&max_results=${maxResults}`);
  },
};

// Visualization API
export const visualizationAPI = {
  getPerformanceChart: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/performance-chart`);
  },

  getHourlyHeatmap: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/hourly-heatmap`);
  },

  getSymbolPerformance: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/symbol-performance`);
  },

  getDrawdownChart: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/drawdown-chart`);
  },

  getMonthlyPerformance: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/monthly-performance`);
  },

  getRiskMetrics: (dataId: string): Promise<VisualizationData> => {
    return apiService.get<VisualizationData>(`/visualizations/${dataId}/risk-metrics`);
  },
};

// Plugin API
export const pluginAPI = {
  listPlugins: (): Promise<Record<string, Plugin>> => {
    return apiService.get<Record<string, Plugin>>('/plugins/');
  },

  loadPlugin: (pluginName: string): Promise<{ message: string }> => {
    return apiService.post<{ message: string }>(`/plugins/${pluginName}/load`);
  },

  unloadPlugin: (pluginName: string): Promise<{ message: string }> => {
    return apiService.post<{ message: string }>(`/plugins/${pluginName}/unload`);
  },

  getPluginStatus: (pluginName: string): Promise<Plugin> => {
    return apiService.get<Plugin>(`/plugins/${pluginName}/status`);
  },

  discoverPlugins: (): Promise<{ discovered_plugins: string[] }> => {
    return apiService.post<{ discovered_plugins: string[] }>('/plugins/discover');
  },

  reloadAllPlugins: (): Promise<{ reload_results: Record<string, boolean> }> => {
    return apiService.post<{ reload_results: Record<string, boolean> }>('/plugins/reload-all');
  },
};

// Health check API
export const healthAPI = {
  checkHealth: (): Promise<any> => {
    return apiService.get<any>('/health');
  },

  getEventHistory: (eventType?: string, limit: number = 100): Promise<any[]> => {
    const params = new URLSearchParams();
    if (eventType) params.append('event_type', eventType);
    params.append('limit', limit.toString());
    
    return apiService.get<any[]>(`/events/history?${params.toString()}`);
  },

  getEventStats: (): Promise<any> => {
    return apiService.get<any>('/events/stats');
  },
};

// Export default API instance for direct use
export default apiService;