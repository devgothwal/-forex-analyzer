// Data management state slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Dataset, TradingData, UploadResponse } from '@/types/trading';

interface DataState {
  datasets: Dataset[];
  currentDataset: Dataset | null;
  uploadProgress: number;
  isUploading: boolean;
  selectedDatasetId: string | null;
  filters: {
    dateRange: {
      start: string | null;
      end: string | null;
    };
    symbols: string[];
    tradeTypes: string[];
    minProfit: number | null;
    maxProfit: number | null;
  };
  sorting: {
    field: string;
    direction: 'asc' | 'desc';
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
}

const initialState: DataState = {
  datasets: [],
  currentDataset: null,
  uploadProgress: 0,
  isUploading: false,
  selectedDatasetId: null,
  filters: {
    dateRange: {
      start: null,
      end: null,
    },
    symbols: [],
    tradeTypes: [],
    minProfit: null,
    maxProfit: null,
  },
  sorting: {
    field: 'upload_time',
    direction: 'desc',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
};

const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    setDatasets: (state, action: PayloadAction<Dataset[]>) => {
      state.datasets = action.payload;
      state.pagination.total = action.payload.length;
    },

    addDataset: (state, action: PayloadAction<Dataset>) => {
      state.datasets.unshift(action.payload); // Add to beginning
      state.pagination.total += 1;
    },

    updateDataset: (state, action: PayloadAction<Dataset>) => {
      const index = state.datasets.findIndex(d => d.data_id === action.payload.data_id);
      if (index !== -1) {
        state.datasets[index] = action.payload;
      }
    },

    removeDataset: (state, action: PayloadAction<string>) => {
      state.datasets = state.datasets.filter(d => d.data_id !== action.payload);
      state.pagination.total -= 1;
      
      // Clear current dataset if it was deleted
      if (state.currentDataset?.data_id === action.payload) {
        state.currentDataset = null;
      }
      
      // Clear selection if it was deleted
      if (state.selectedDatasetId === action.payload) {
        state.selectedDatasetId = null;
      }
    },

    setCurrentDataset: (state, action: PayloadAction<Dataset | null>) => {
      state.currentDataset = action.payload;
    },

    setSelectedDatasetId: (state, action: PayloadAction<string | null>) => {
      state.selectedDatasetId = action.payload;
      
      // Auto-set current dataset
      if (action.payload) {
        const dataset = state.datasets.find(d => d.data_id === action.payload);
        if (dataset) {
          state.currentDataset = dataset;
        }
      }
    },

    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },

    setIsUploading: (state, action: PayloadAction<boolean>) => {
      state.isUploading = action.payload;
      if (!action.payload) {
        state.uploadProgress = 0;
      }
    },

    uploadStarted: (state) => {
      state.isUploading = true;
      state.uploadProgress = 0;
    },

    uploadCompleted: (state, action: PayloadAction<UploadResponse>) => {
      state.isUploading = false;
      state.uploadProgress = 100;
      
      // Convert upload response to dataset format
      const newDataset: Dataset = {
        data_id: action.payload.data_id,
        metadata: {
          source: 'MT5', // Default, would be provided
          account: 'unknown',
          currency: 'USD',
          leverage: 100,
          total_trades: action.payload.records_count,
          date_range: {
            start: new Date().toISOString(),
            end: new Date().toISOString(),
          },
        },
        summary_stats: action.payload.summary_stats,
        upload_time: action.payload.upload_time,
        trade_count: action.payload.records_count,
        date_range: {
          start: new Date().toISOString(),
          end: new Date().toISOString(),
        },
      };
      
      state.datasets.unshift(newDataset);
      state.pagination.total += 1;
    },

    uploadFailed: (state) => {
      state.isUploading = false;
      state.uploadProgress = 0;
    },

    setFilters: (state, action: PayloadAction<Partial<DataState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
      state.pagination.page = 1; // Reset to first page when filtering
    },

    clearFilters: (state) => {
      state.filters = initialState.filters;
      state.pagination.page = 1;
    },

    setSorting: (state, action: PayloadAction<{ field: string; direction: 'asc' | 'desc' }>) => {
      state.sorting = action.payload;
      state.pagination.page = 1; // Reset to first page when sorting
    },

    setPagination: (state, action: PayloadAction<Partial<DataState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },

    nextPage: (state) => {
      const maxPage = Math.ceil(state.pagination.total / state.pagination.pageSize);
      if (state.pagination.page < maxPage) {
        state.pagination.page += 1;
      }
    },

    previousPage: (state) => {
      if (state.pagination.page > 1) {
        state.pagination.page -= 1;
      }
    },

    setPageSize: (state, action: PayloadAction<number>) => {
      state.pagination.pageSize = action.payload;
      state.pagination.page = 1; // Reset to first page
    },
  },
});

export const {
  setDatasets,
  addDataset,
  updateDataset,
  removeDataset,
  setCurrentDataset,
  setSelectedDatasetId,
  setUploadProgress,
  setIsUploading,
  uploadStarted,
  uploadCompleted,
  uploadFailed,
  setFilters,
  clearFilters,
  setSorting,
  setPagination,
  nextPage,
  previousPage,
  setPageSize,
} = dataSlice.actions;

export default dataSlice.reducer;