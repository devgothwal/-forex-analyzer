// Data Management page - Upload and manage trading data

import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
} from '@mui/material';
import { Upload, Storage } from '@mui/icons-material';

const DataManagement: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Data Management
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Upload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 2 }}>
                Upload Trading Data
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Import your MT5/MT4 trading history
              </Typography>
              <Button variant="contained" size="large">
                Choose File
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <Storage sx={{ fontSize: 64, color: 'secondary.main', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 2 }}>
                Manage Datasets
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                View and manage your uploaded data
              </Typography>
              <Button variant="outlined" size="large">
                View All
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DataManagement;