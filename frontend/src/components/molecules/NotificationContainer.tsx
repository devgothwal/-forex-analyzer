// Notification container component

import React, { useEffect } from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Slide,
  SlideProps,
  IconButton,
} from '@mui/material';
import { Close } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '@/store';
import { removeNotification } from '@/store/slices/uiSlice';
import { TransitionProps } from '@mui/material/transitions';

// Slide transition component
function SlideTransition(props: SlideProps) {
  return <Slide {...props} direction="left" />;
}

const NotificationContainer: React.FC = () => {
  const dispatch = useDispatch();
  const notifications = useSelector((state: RootState) => state.ui.notifications);

  const handleClose = (notificationId: string) => {
    dispatch(removeNotification(notificationId));
  };

  return (
    <>
      {notifications.map((notification, index) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          index={index}
          onClose={() => handleClose(notification.id)}
        />
      ))}
    </>
  );
};

// Individual notification item component
interface NotificationItemProps {
  notification: {
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
  };
  index: number;
  onClose: () => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  index,
  onClose,
}) => {
  // Auto-dismiss after duration
  useEffect(() => {
    const duration = notification.duration || 6000;
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [notification.duration, onClose]);

  // Calculate position based on index
  const anchorOrigin = {
    vertical: 'top' as const,
    horizontal: 'right' as const,
  };

  const style = {
    top: 24 + index * 80, // Stack notifications
  };

  return (
    <Snackbar
      open={true}
      anchorOrigin={anchorOrigin}
      TransitionComponent={SlideTransition}
      sx={style}
    >
      <Alert
        severity={notification.type}
        variant="filled"
        onClose={onClose}
        sx={{
          minWidth: 300,
          maxWidth: 500,
          '& .MuiAlert-message': {
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          },
        }}
        action={
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={onClose}
          >
            <Close fontSize="small" />
          </IconButton>
        }
      >
        {notification.message}
      </Alert>
    </Snackbar>
  );
};

export default NotificationContainer;