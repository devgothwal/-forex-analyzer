// UI state management slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ThemeConfig, LoadingState, ErrorState, NotificationState, ModalState, LayoutConfig } from '@/types/ui';

interface UIState {
  theme: ThemeConfig;
  loading: LoadingState;
  error: ErrorState;
  notifications: NotificationState[];
  modal: ModalState;
  layout: LayoutConfig;
  isMobile: boolean;
  viewport: {
    width: number;
    height: number;
  };
}

const initialState: UIState = {
  theme: {
    mode: 'light',
    primary: '#1976d2',
    secondary: '#dc004e',
    background: '#ffffff',
    surface: '#f5f5f5',
    text: '#000000',
  },
  loading: {
    isLoading: false,
  },
  error: {
    hasError: false,
  },
  notifications: [],
  modal: {
    isOpen: false,
  },
  layout: {
    sidebar: {
      open: true,
      width: 280,
      variant: 'permanent',
    },
    header: {
      height: 64,
      variant: 'fixed',
    },
    footer: {
      height: 48,
      visible: true,
    },
  },
  isMobile: false,
  viewport: {
    width: window.innerWidth,
    height: window.innerHeight,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<Partial<ThemeConfig>>) => {
      state.theme = { ...state.theme, ...action.payload };
    },

    toggleThemeMode: (state) => {
      state.theme.mode = state.theme.mode === 'light' ? 'dark' : 'light';
    },

    setLoading: (state, action: PayloadAction<Partial<LoadingState>>) => {
      state.loading = { ...state.loading, ...action.payload };
    },

    clearLoading: (state) => {
      state.loading = { isLoading: false };
    },

    setError: (state, action: PayloadAction<Partial<ErrorState>>) => {
      state.error = { hasError: true, ...action.payload };
    },

    clearError: (state) => {
      state.error = { hasError: false };
    },

    addNotification: (state, action: PayloadAction<Omit<NotificationState, 'id'>>) => {
      const notification: NotificationState = {
        ...action.payload,
        id: Date.now().toString(),
      };
      state.notifications.push(notification);
    },

    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },

    clearNotifications: (state) => {
      state.notifications = [];
    },

    openModal: (state, action: PayloadAction<Omit<ModalState, 'isOpen'>>) => {
      state.modal = { isOpen: true, ...action.payload };
    },

    closeModal: (state) => {
      state.modal = { isOpen: false };
    },

    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.layout.sidebar.open = action.payload;
    },

    setSidebarVariant: (state, action: PayloadAction<'permanent' | 'temporary' | 'persistent'>) => {
      state.layout.sidebar.variant = action.payload;
    },

    setIsMobile: (state, action: PayloadAction<boolean>) => {
      state.isMobile = action.payload;
      // Auto-adjust layout for mobile
      if (action.payload) {
        state.layout.sidebar.variant = 'temporary';
        state.layout.sidebar.open = false;
      } else {
        state.layout.sidebar.variant = 'permanent';
        state.layout.sidebar.open = true;
      }
    },

    setViewport: (state, action: PayloadAction<{ width: number; height: number }>) => {
      state.viewport = action.payload;
      // Auto-detect mobile based on width
      const isMobile = action.payload.width < 768;
      if (isMobile !== state.isMobile) {
        state.isMobile = isMobile;
        if (isMobile) {
          state.layout.sidebar.variant = 'temporary';
          state.layout.sidebar.open = false;
        } else {
          state.layout.sidebar.variant = 'permanent';
          state.layout.sidebar.open = true;
        }
      }
    },

    updateLayout: (state, action: PayloadAction<Partial<LayoutConfig>>) => {
      state.layout = { ...state.layout, ...action.payload };
    },
  },
});

export const {
  setTheme,
  toggleThemeMode,
  setLoading,
  clearLoading,
  setError,
  clearError,
  addNotification,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  setSidebarOpen,
  setSidebarVariant,
  setIsMobile,
  setViewport,
  updateLayout,
} = uiSlice.actions;

export default uiSlice.reducer;