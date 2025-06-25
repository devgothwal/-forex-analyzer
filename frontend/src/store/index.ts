// Redux store configuration with RTK Query

import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Import slice reducers
import uiReducer from './slices/uiSlice';
import dataReducer from './slices/dataSlice';
import analysisReducer from './slices/analysisSlice';
import pluginReducer from './slices/pluginSlice';

// RTK Query API
export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1',
    prepareHeaders: (headers, { getState }) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Dataset', 'Analysis', 'Insight', 'Plugin'],
  endpoints: () => ({}),
});

// Configure store
export const store = configureStore({
  reducer: {
    ui: uiReducer,
    data: dataReducer,
    analysis: analysisReducer,
    plugins: pluginReducer,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(api.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

// Setup listeners for refetch behaviors
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;