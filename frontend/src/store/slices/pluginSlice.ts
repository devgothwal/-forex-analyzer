// Plugin management state slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Plugin } from '@/types/trading';

interface PluginState {
  plugins: Record<string, Plugin>;
  loadedPlugins: string[];
  availablePlugins: string[];
  isLoading: boolean;
  loadingPlugin: string | null;
  error: string | null;
  discoveryResults: string[];
  reloadResults: Record<string, boolean>;
}

const initialState: PluginState = {
  plugins: {},
  loadedPlugins: [],
  availablePlugins: [],
  isLoading: false,
  loadingPlugin: null,
  error: null,
  discoveryResults: [],
  reloadResults: {},
};

const pluginSlice = createSlice({
  name: 'plugins',
  initialState,
  reducers: {
    setPlugins: (state, action: PayloadAction<Record<string, Plugin>>) => {
      state.plugins = action.payload;
      
      // Update loaded and available lists
      state.loadedPlugins = Object.entries(action.payload)
        .filter(([_, plugin]) => plugin.status === 'active')
        .map(([name, _]) => name);
        
      state.availablePlugins = Object.keys(action.payload);
    },

    updatePlugin: (state, action: PayloadAction<{ name: string; plugin: Plugin }>) => {
      const { name, plugin } = action.payload;
      state.plugins[name] = plugin;
      
      // Update loaded list
      if (plugin.status === 'active' && !state.loadedPlugins.includes(name)) {
        state.loadedPlugins.push(name);
      } else if (plugin.status !== 'active') {
        state.loadedPlugins = state.loadedPlugins.filter(p => p !== name);
      }
    },

    removePlugin: (state, action: PayloadAction<string>) => {
      const pluginName = action.payload;
      delete state.plugins[pluginName];
      state.loadedPlugins = state.loadedPlugins.filter(p => p !== pluginName);
      state.availablePlugins = state.availablePlugins.filter(p => p !== pluginName);
    },

    setIsLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (!action.payload) {
        state.loadingPlugin = null;
      }
    },

    setLoadingPlugin: (state, action: PayloadAction<string | null>) => {
      state.loadingPlugin = action.payload;
      state.isLoading = action.payload !== null;
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },

    clearError: (state) => {
      state.error = null;
    },

    pluginLoadStarted: (state, action: PayloadAction<string>) => {
      state.loadingPlugin = action.payload;
      state.isLoading = true;
      state.error = null;
    },

    pluginLoadSuccess: (state, action: PayloadAction<{ name: string; plugin: Plugin }>) => {
      const { name, plugin } = action.payload;
      state.plugins[name] = plugin;
      
      if (plugin.status === 'active' && !state.loadedPlugins.includes(name)) {
        state.loadedPlugins.push(name);
      }
      
      state.loadingPlugin = null;
      state.isLoading = false;
      state.error = null;
    },

    pluginLoadFailed: (state, action: PayloadAction<{ name: string; error: string }>) => {
      const { name, error } = action.payload;
      
      // Update plugin status to error if it exists
      if (state.plugins[name]) {
        state.plugins[name].status = 'error';
      }
      
      state.loadingPlugin = null;
      state.isLoading = false;
      state.error = error;
    },

    pluginUnloadStarted: (state, action: PayloadAction<string>) => {
      state.loadingPlugin = action.payload;
      state.isLoading = true;
      state.error = null;
    },

    pluginUnloadSuccess: (state, action: PayloadAction<string>) => {
      const pluginName = action.payload;
      
      // Update plugin status
      if (state.plugins[pluginName]) {
        state.plugins[pluginName].status = 'discovered';
      }
      
      // Remove from loaded list
      state.loadedPlugins = state.loadedPlugins.filter(p => p !== pluginName);
      
      state.loadingPlugin = null;
      state.isLoading = false;
      state.error = null;
    },

    pluginUnloadFailed: (state, action: PayloadAction<{ name: string; error: string }>) => {
      const { error } = action.payload;
      
      state.loadingPlugin = null;
      state.isLoading = false;
      state.error = error;
    },

    setDiscoveryResults: (state, action: PayloadAction<string[]>) => {
      state.discoveryResults = action.payload;
      
      // Add newly discovered plugins to available list
      action.payload.forEach(pluginName => {
        if (!state.availablePlugins.includes(pluginName)) {
          state.availablePlugins.push(pluginName);
        }
        
        // Add to plugins object if not present
        if (!state.plugins[pluginName]) {
          state.plugins[pluginName] = {
            manifest: {
              name: pluginName,
              version: 'unknown',
              description: 'Discovered plugin',
              author: 'unknown',
              api_version: '1.0',
            },
            status: 'discovered',
          };
        }
      });
    },

    discoveryStarted: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    discoveryCompleted: (state, action: PayloadAction<string[]>) => {
      state.discoveryResults = action.payload;
      state.isLoading = false;
      state.error = null;
    },

    discoveryFailed: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    setReloadResults: (state, action: PayloadAction<Record<string, boolean>>) => {
      state.reloadResults = action.payload;
    },

    reloadAllStarted: (state) => {
      state.isLoading = true;
      state.error = null;
      state.reloadResults = {};
    },

    reloadAllCompleted: (state, action: PayloadAction<Record<string, boolean>>) => {
      state.reloadResults = action.payload;
      state.isLoading = false;
      state.error = null;
      
      // Update plugin statuses based on reload results
      Object.entries(action.payload).forEach(([pluginName, success]) => {
        if (state.plugins[pluginName]) {
          state.plugins[pluginName].status = success ? 'active' : 'error';
        }
      });
      
      // Update loaded plugins list
      state.loadedPlugins = Object.entries(action.payload)
        .filter(([_, success]) => success)
        .map(([name, _]) => name);
    },

    reloadAllFailed: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
      state.reloadResults = {};
    },

    // Utility actions
    getPluginsByStatus: (state, action: PayloadAction<Plugin['status']>) => {
      // This would be used in selectors, but we can track it here too
      return Object.entries(state.plugins)
        .filter(([_, plugin]) => plugin.status === action.payload)
        .map(([name, _]) => name);
    },

    resetPluginState: () => {
      return initialState;
    },
  },
});

export const {
  setPlugins,
  updatePlugin,
  removePlugin,
  setIsLoading,
  setLoadingPlugin,
  setError,
  clearError,
  pluginLoadStarted,
  pluginLoadSuccess,
  pluginLoadFailed,
  pluginUnloadStarted,
  pluginUnloadSuccess,
  pluginUnloadFailed,
  setDiscoveryResults,
  discoveryStarted,
  discoveryCompleted,
  discoveryFailed,
  setReloadResults,
  reloadAllStarted,
  reloadAllCompleted,
  reloadAllFailed,
  resetPluginState,
} = pluginSlice.actions;

export default pluginSlice.reducer;