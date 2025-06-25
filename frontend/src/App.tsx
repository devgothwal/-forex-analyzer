// Main App component with theme provider and routing

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Store and theme
import { store } from '@/store';
import { useAppTheme } from '@/hooks/useTheme';
import { useViewportResize } from '@/hooks/useViewport';

// Layout components
import AppLayout from '@/components/templates/AppLayout';
import ErrorBoundary from '@/components/molecules/ErrorBoundary';
import NotificationContainer from '@/components/molecules/NotificationContainer';
import LoadingOverlay from '@/components/atoms/LoadingOverlay';

// Page components
import Dashboard from '@/pages/Dashboard';
import DataManagement from '@/pages/DataManagement';
import Analysis from '@/pages/Analysis';
import Insights from '@/pages/Insights';
import Visualizations from '@/pages/Visualizations';
import Plugins from '@/pages/Plugins';
import Settings from '@/pages/Settings';
import NotFound from '@/pages/NotFound';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
});

// App content component (needs to be inside providers)
const AppContent: React.FC = () => {
  const theme = useAppTheme();
  useViewportResize(); // Hook to handle viewport changes

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <ErrorBoundary>
          <Box sx={{ display: 'flex', minHeight: '100vh' }}>
            <Router>
              <AppLayout>
                <Routes>
                  {/* Main routes */}
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/data" element={<DataManagement />} />
                  <Route path="/analysis" element={<Analysis />} />
                  <Route path="/insights" element={<Insights />} />
                  <Route path="/visualizations" element={<Visualizations />} />
                  <Route path="/plugins" element={<Plugins />} />
                  <Route path="/settings" element={<Settings />} />
                  
                  {/* 404 route */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </AppLayout>
            </Router>
            
            {/* Global components */}
            <NotificationContainer />
            <LoadingOverlay />
          </Box>
        </ErrorBoundary>
      </LocalizationProvider>
    </ThemeProvider>
  );
};

// Main App component
const App: React.FC = () => {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <AppContent />
      </QueryClientProvider>
    </Provider>
  );
};

export default App;