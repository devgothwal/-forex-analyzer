// Loading overlay component

import React from 'react';
import {
  Backdrop,
  CircularProgress,
  Box,
  Typography,
  LinearProgress,
} from '@mui/material';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';

interface LoadingOverlayProps {
  open?: boolean;
  message?: string;
  progress?: number;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  open: propOpen,
  message: propMessage,
  progress: propProgress,
}) => {
  const { loading } = useSelector((state: RootState) => state.ui);
  
  const open = propOpen !== undefined ? propOpen : loading.isLoading;
  const message = propMessage || loading.message || 'Loading...';
  const progress = propProgress !== undefined ? propProgress : loading.progress;

  if (!open) return null;

  return (
    <Backdrop
      sx={{
        color: '#fff',
        zIndex: (theme) => theme.zIndex.modal + 1,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
      }}
      open={open}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          padding: 3,
          backgroundColor: 'background.paper',
          borderRadius: 2,
          minWidth: 200,
          maxWidth: 400,
        }}
      >
        {/* Circular progress */}
        <CircularProgress
          size={48}
          thickness={4}
          variant={progress !== undefined ? 'determinate' : 'indeterminate'}
          value={progress}
        />
        
        {/* Message */}
        <Typography
          variant="body1"
          color="text.primary"
          textAlign="center"
          sx={{ mt: 1 }}
        >
          {message}
        </Typography>
        
        {/* Linear progress bar for determinate progress */}
        {progress !== undefined && (
          <Box sx={{ width: '100%', mt: 1 }}>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ height: 6, borderRadius: 3 }}
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: 0.5, display: 'block', textAlign: 'center' }}
            >
              {Math.round(progress)}%
            </Typography>
          </Box>
        )}
      </Box>
    </Backdrop>
  );
};

export default LoadingOverlay;