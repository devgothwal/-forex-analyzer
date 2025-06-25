// Analysis state management slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AnalysisResult, AnalysisType, Insight } from '@/types/trading';

interface AnalysisState {
  results: AnalysisResult[];
  currentResult: AnalysisResult | null;
  insights: Insight[];
  availableAnalysisTypes: {
    built_in: AnalysisType[];
    plugins: AnalysisType[];
  };
  isRunning: boolean;
  progress: number;
  selectedAnalysisTypes: string[];
  analysisParameters: Record<string, any>;
  filters: {
    analysisType: string | null;
    dateRange: {
      start: string | null;
      end: string | null;
    };
    status: string | null;
  };
  insightFilters: {
    category: string | null;
    type: string | null;
    impact: string | null;
    minConfidence: number;
  };
}

const initialState: AnalysisState = {
  results: [],
  currentResult: null,
  insights: [],
  availableAnalysisTypes: {
    built_in: [],
    plugins: [],
  },
  isRunning: false,
  progress: 0,
  selectedAnalysisTypes: ['comprehensive'],
  analysisParameters: {},
  filters: {
    analysisType: null,
    dateRange: {
      start: null,
      end: null,
    },
    status: null,
  },
  insightFilters: {
    category: null,
    type: null,
    impact: null,
    minConfidence: 0.5,
  },
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setAnalysisResults: (state, action: PayloadAction<AnalysisResult[]>) => {
      state.results = action.payload;
    },

    addAnalysisResult: (state, action: PayloadAction<AnalysisResult>) => {
      state.results.unshift(action.payload); // Add to beginning
    },

    updateAnalysisResult: (state, action: PayloadAction<AnalysisResult>) => {
      const index = state.results.findIndex(r => r.analysis_id === action.payload.analysis_id);
      if (index !== -1) {
        state.results[index] = action.payload;
      }
    },

    removeAnalysisResult: (state, action: PayloadAction<string>) => {
      state.results = state.results.filter(r => r.analysis_id !== action.payload);
      
      // Clear current result if it was deleted
      if (state.currentResult?.analysis_id === action.payload) {
        state.currentResult = null;
      }
    },

    setCurrentResult: (state, action: PayloadAction<AnalysisResult | null>) => {
      state.currentResult = action.payload;
    },

    setInsights: (state, action: PayloadAction<Insight[]>) => {
      state.insights = action.payload;
    },

    addInsight: (state, action: PayloadAction<Insight>) => {
      state.insights.unshift(action.payload);
    },

    updateInsight: (state, action: PayloadAction<Insight>) => {
      const index = state.insights.findIndex(i => i.id === action.payload.id);
      if (index !== -1) {
        state.insights[index] = action.payload;
      }
    },

    removeInsight: (state, action: PayloadAction<string>) => {
      state.insights = state.insights.filter(i => i.id !== action.payload);
    },

    setAvailableAnalysisTypes: (state, action: PayloadAction<{ built_in: AnalysisType[]; plugins: AnalysisType[] }>) => {
      state.availableAnalysisTypes = action.payload;
    },

    setIsRunning: (state, action: PayloadAction<boolean>) => {
      state.isRunning = action.payload;
      if (!action.payload) {
        state.progress = 0;
      }
    },

    setProgress: (state, action: PayloadAction<number>) => {
      state.progress = Math.max(0, Math.min(100, action.payload));
    },

    analysisStarted: (state) => {
      state.isRunning = true;
      state.progress = 0;
    },

    analysisProgress: (state, action: PayloadAction<number>) => {
      state.progress = action.payload;
    },

    analysisCompleted: (state, action: PayloadAction<AnalysisResult>) => {
      state.isRunning = false;
      state.progress = 100;
      state.results.unshift(action.payload);
      state.currentResult = action.payload;
    },

    analysisFailed: (state) => {
      state.isRunning = false;
      state.progress = 0;
    },

    setSelectedAnalysisTypes: (state, action: PayloadAction<string[]>) => {
      state.selectedAnalysisTypes = action.payload;
    },

    addSelectedAnalysisType: (state, action: PayloadAction<string>) => {
      if (!state.selectedAnalysisTypes.includes(action.payload)) {
        state.selectedAnalysisTypes.push(action.payload);
      }
    },

    removeSelectedAnalysisType: (state, action: PayloadAction<string>) => {
      state.selectedAnalysisTypes = state.selectedAnalysisTypes.filter(t => t !== action.payload);
    },

    setAnalysisParameters: (state, action: PayloadAction<Record<string, any>>) => {
      state.analysisParameters = action.payload;
    },

    updateAnalysisParameter: (state, action: PayloadAction<{ key: string; value: any }>) => {
      state.analysisParameters[action.payload.key] = action.payload.value;
    },

    setAnalysisFilters: (state, action: PayloadAction<Partial<AnalysisState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },

    clearAnalysisFilters: (state) => {
      state.filters = initialState.filters;
    },

    setInsightFilters: (state, action: PayloadAction<Partial<AnalysisState['insightFilters']>>) => {
      state.insightFilters = { ...state.insightFilters, ...action.payload };
    },

    clearInsightFilters: (state) => {
      state.insightFilters = initialState.insightFilters;
    },

    // Batch operations
    clearAllResults: (state) => {
      state.results = [];
      state.currentResult = null;
    },

    clearAllInsights: (state) => {
      state.insights = [];
    },

    resetAnalysisState: (state) => {
      return {
        ...initialState,
        availableAnalysisTypes: state.availableAnalysisTypes, // Keep loaded types
      };
    },
  },
});

export const {
  setAnalysisResults,
  addAnalysisResult,
  updateAnalysisResult,
  removeAnalysisResult,
  setCurrentResult,
  setInsights,
  addInsight,
  updateInsight,
  removeInsight,
  setAvailableAnalysisTypes,
  setIsRunning,
  setProgress,
  analysisStarted,
  analysisProgress,
  analysisCompleted,
  analysisFailed,
  setSelectedAnalysisTypes,
  addSelectedAnalysisType,
  removeSelectedAnalysisType,
  setAnalysisParameters,
  updateAnalysisParameter,
  setAnalysisFilters,
  clearAnalysisFilters,
  setInsightFilters,
  clearInsightFilters,
  clearAllResults,
  clearAllInsights,
  resetAnalysisState,
} = analysisSlice.actions;

export default analysisSlice.reducer;