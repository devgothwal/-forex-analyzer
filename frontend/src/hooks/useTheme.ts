// Theme management hook

import { useMemo } from 'react';
import { createTheme, Theme } from '@mui/material/styles';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';

// Custom theme configuration
export const useAppTheme = (): Theme => {
  const { theme: themeConfig } = useSelector((state: RootState) => state.ui);

  const theme = useMemo(() => {
    return createTheme({
      palette: {
        mode: themeConfig.mode,
        primary: {
          main: themeConfig.primary,
          light: themeConfig.mode === 'light' ? '#42a5f5' : '#90caf9',
          dark: themeConfig.mode === 'light' ? '#1565c0' : '#1976d2',
        },
        secondary: {
          main: themeConfig.secondary,
          light: themeConfig.mode === 'light' ? '#ff5983' : '#f48fb1',
          dark: themeConfig.mode === 'light' ? '#ad1457' : '#c2185b',
        },
        background: {
          default: themeConfig.mode === 'light' ? '#f5f5f5' : '#121212',
          paper: themeConfig.mode === 'light' ? '#ffffff' : '#1e1e1e',
        },
        text: {
          primary: themeConfig.mode === 'light' ? '#000000' : '#ffffff',
          secondary: themeConfig.mode === 'light' ? '#666666' : '#cccccc',
        },
        success: {
          main: '#4caf50',
          light: '#81c784',
          dark: '#2e7d32',
        },
        warning: {
          main: '#ff9800',
          light: '#ffb74d',
          dark: '#f57c00',
        },
        error: {
          main: '#f44336',
          light: '#e57373',
          dark: '#d32f2f',
        },
        info: {
          main: '#2196f3',
          light: '#64b5f6',
          dark: '#1976d2',
        },
      },
      typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: {
          fontSize: '2.5rem',
          fontWeight: 600,
          lineHeight: 1.2,
        },
        h2: {
          fontSize: '2rem',
          fontWeight: 600,
          lineHeight: 1.3,
        },
        h3: {
          fontSize: '1.75rem',
          fontWeight: 600,
          lineHeight: 1.3,
        },
        h4: {
          fontSize: '1.5rem',
          fontWeight: 600,
          lineHeight: 1.4,
        },
        h5: {
          fontSize: '1.25rem',
          fontWeight: 600,
          lineHeight: 1.4,
        },
        h6: {
          fontSize: '1rem',
          fontWeight: 600,
          lineHeight: 1.5,
        },
        body1: {
          fontSize: '1rem',
          lineHeight: 1.5,
        },
        body2: {
          fontSize: '0.875rem',
          lineHeight: 1.43,
        },
        caption: {
          fontSize: '0.75rem',
          lineHeight: 1.66,
        },
        button: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
      shape: {
        borderRadius: 8,
      },
      spacing: 8,
      components: {
        MuiButton: {
          styleOverrides: {
            root: {
              borderRadius: 8,
              textTransform: 'none',
              fontWeight: 500,
              padding: '8px 16px',
            },
            contained: {
              boxShadow: 'none',
              '&:hover': {
                boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.2)',
              },
            },
          },
        },
        MuiCard: {
          styleOverrides: {
            root: {
              borderRadius: 12,
              boxShadow: themeConfig.mode === 'light' 
                ? '0px 2px 8px rgba(0, 0, 0, 0.1)' 
                : '0px 2px 8px rgba(0, 0, 0, 0.3)',
            },
          },
        },
        MuiPaper: {
          styleOverrides: {
            root: {
              borderRadius: 8,
            },
            elevation1: {
              boxShadow: themeConfig.mode === 'light'
                ? '0px 1px 3px rgba(0, 0, 0, 0.1)'
                : '0px 1px 3px rgba(0, 0, 0, 0.3)',
            },
          },
        },
        MuiAppBar: {
          styleOverrides: {
            root: {
              backgroundColor: themeConfig.mode === 'light' ? '#ffffff' : '#1e1e1e',
              color: themeConfig.mode === 'light' ? '#000000' : '#ffffff',
              boxShadow: 'none',
              borderBottom: `1px solid ${themeConfig.mode === 'light' ? '#e0e0e0' : '#333333'}`,
            },
          },
        },
        MuiDrawer: {
          styleOverrides: {
            paper: {
              backgroundColor: themeConfig.mode === 'light' ? '#fafafa' : '#1a1a1a',
              borderRight: `1px solid ${themeConfig.mode === 'light' ? '#e0e0e0' : '#333333'}`,
            },
          },
        },
        MuiListItemButton: {
          styleOverrides: {
            root: {
              borderRadius: 8,
              margin: '2px 8px',
              '&.Mui-selected': {
                backgroundColor: themeConfig.mode === 'light' 
                  ? 'rgba(25, 118, 210, 0.08)' 
                  : 'rgba(144, 202, 249, 0.08)',
                '&:hover': {
                  backgroundColor: themeConfig.mode === 'light'
                    ? 'rgba(25, 118, 210, 0.12)'
                    : 'rgba(144, 202, 249, 0.12)',
                },
              },
            },
          },
        },
        MuiChip: {
          styleOverrides: {
            root: {
              borderRadius: 16,
            },
          },
        },
        MuiTextField: {
          styleOverrides: {
            root: {
              '& .MuiOutlinedInput-root': {
                borderRadius: 8,
              },
            },
          },
        },
        MuiTableCell: {
          styleOverrides: {
            head: {
              fontWeight: 600,
              backgroundColor: themeConfig.mode === 'light' ? '#f5f5f5' : '#2a2a2a',
            },
          },
        },
        MuiTooltip: {
          styleOverrides: {
            tooltip: {
              backgroundColor: themeConfig.mode === 'light' ? '#616161' : '#f5f5f5',
              color: themeConfig.mode === 'light' ? '#ffffff' : '#000000',
              fontSize: '0.75rem',
            },
          },
        },
      },
      breakpoints: {
        values: {
          xs: 0,
          sm: 600,
          md: 960,
          lg: 1280,
          xl: 1920,
        },
      },
      zIndex: {
        appBar: 1200,
        drawer: 1100,
        modal: 1300,
        snackbar: 1400,
        tooltip: 1500,
      },
    });
  }, [themeConfig]);

  return theme;
};