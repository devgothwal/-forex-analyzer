// Error boundary component

import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ErrorOutline,
  Refresh,
  ExpandMore,
  BugReport,
} from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });

    // Log to external service in production
    if (process.env.NODE_ENV === 'production') {
      // logErrorToService(error, errorInfo);
    }
  }

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleReport = () => {
    const { error, errorInfo } = this.state;
    const errorReport = {
      message: error?.message,
      stack: error?.stack,
      componentStack: errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // Copy to clipboard for easy reporting
    navigator.clipboard.writeText(JSON.stringify(errorReport, null, 2));
    
    // Show notification
    alert('Error details copied to clipboard. Please report this issue.');
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorInfo } = this.state;
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            padding: 3,
            backgroundColor: 'background.default',
          }}
        >
          <Card sx={{ maxWidth: 800, width: '100%' }}>
            <CardContent sx={{ p: 4 }}>
              {/* Error icon and title */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  mb: 3,
                }}
              >
                <ErrorOutline color="error" sx={{ fontSize: 48 }} />
                <Box>
                  <Typography variant="h5" color="error" gutterBottom>
                    Something went wrong
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    An unexpected error occurred in the application
                  </Typography>
                </Box>
              </Box>

              {/* Error message */}
              <Alert severity="error" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  {error?.message || 'An unknown error occurred'}
                </Typography>
              </Alert>

              {/* Action buttons */}
              <Box
                sx={{
                  display: 'flex',
                  gap: 2,
                  mb: 3,
                  flexWrap: 'wrap',
                }}
              >
                <Button
                  variant="contained"
                  startIcon={<Refresh />}
                  onClick={this.handleRetry}
                >
                  Try Again
                </Button>
                
                <Button
                  variant="outlined"
                  onClick={this.handleReload}
                >
                  Reload Page
                </Button>
                
                <Button
                  variant="text"
                  startIcon={<BugReport />}
                  onClick={this.handleReport}
                  size="small"
                >
                  Report Issue
                </Button>
              </Box>

              {/* Developer details */}
              {isDevelopment && error && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle2">
                      Error Details (Development)
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Error Message:
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: 'monospace',
                          backgroundColor: 'grey.100',
                          p: 1,
                          borderRadius: 1,
                          mt: 0.5,
                        }}
                      >
                        {error.message}
                      </Typography>
                    </Box>

                    {error.stack && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          Stack Trace:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            backgroundColor: 'grey.100',
                            p: 1,
                            borderRadius: 1,
                            mt: 0.5,
                            whiteSpace: 'pre-wrap',
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          {error.stack}
                        </Typography>
                      </Box>
                    )}

                    {errorInfo?.componentStack && (
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Component Stack:
                        </Typography>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            backgroundColor: 'grey.100',
                            p: 1,
                            borderRadius: 1,
                            mt: 0.5,
                            whiteSpace: 'pre-wrap',
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          {errorInfo.componentStack}
                        </Typography>
                      </Box>
                    )}
                  </AccordionDetails>
                </Accordion>
              )}

              {/* Help text */}
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 2 }}
              >
                If this problem persists, please try refreshing the page or contact support.
              </Typography>
            </CardContent>
          </Card>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;