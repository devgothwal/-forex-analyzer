// Settings page - Application configuration

import React from 'react';
import { Box, Typography } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Settings
      </Typography>
      <Typography variant="body1">
        Application settings will be available here.
      </Typography>
    </Box>
  );
};

export default Settings;