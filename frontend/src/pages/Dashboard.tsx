// Dashboard page - Main overview of trading data and insights

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Assessment,
  Lightbulb,
  Upload,
  Refresh,
  Analytics,
  Timeline,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '@/store';
import { addNotification } from '@/store/slices/uiSlice';
import { dataAPI, insightsAPI, analysisAPI } from '@/services/api';
import { Dataset, Insight, AnalysisResult } from '@/types/trading';

// Statistics card component
interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'error' | 'warning' | 'info';
  trend?: 'up' | 'down' | 'neutral';
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color = 'primary',
  trend = 'neutral',
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp color="success" fontSize="small" />;
      case 'down':
        return <TrendingDown color="error" fontSize="small" />;
      default:
        return null;
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ color: `${color}.main`, mr: 2 }}>
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="div" sx={{ fontWeight: 600 }}>
              {value}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {title}
              </Typography>
              {getTrendIcon()}
            </Box>
          </Box>
        </Box>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

// Recent insights component
interface RecentInsightsProps {
  insights: Insight[];
  loading: boolean;
}

const RecentInsights: React.FC<RecentInsightsProps> = ({ insights, loading }) => {
  const navigate = useNavigate();

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'success':
        return 'success';
      default:
        return 'info';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Card sx={{ height: 400 }}>
        <CardContent sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: 400 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            Recent Insights
          </Typography>
          <Button
            size="small"
            onClick={() => navigate('/insights')}
            endIcon={<Lightbulb />}
          >
            View All
          </Button>
        </Box>
        
        <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
          {insights.length === 0 ? (
            <Alert severity="info">
              No insights available. Upload trading data to generate insights.
            </Alert>
          ) : (
            insights.slice(0, 5).map((insight) => (
              <Box
                key={insight.id}
                sx={{
                  p: 2,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                  '&:last-child': { mb: 0 },
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {insight.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip
                      size="small"
                      label={insight.type}
                      color={getInsightColor(insight.type) as any}
                      variant="outlined"
                    />
                    <Chip
                      size="small"
                      label={insight.impact}
                      color={getImpactColor(insight.impact) as any}
                      variant="filled"
                    />
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {insight.description}
                </Typography>
                <Typography variant="caption" color="primary.main" sx={{ fontWeight: 500 }}>
                  Confidence: {Math.round(insight.confidence * 100)}%
                </Typography>
              </Box>
            ))
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

// Quick actions component
const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  const actions = [
    {
      title: 'Upload Data',
      description: 'Import MT5/MT4 trading history',
      icon: <Upload />,
      color: 'primary' as const,
      action: () => navigate('/data'),
    },
    {
      title: 'Run Analysis',
      description: 'Analyze trading patterns',
      icon: <Analytics />,
      color: 'success' as const,
      action: () => navigate('/analysis'),
    },
    {
      title: 'View Charts',
      description: 'Visualize performance',
      icon: <Timeline />,
      color: 'info' as const,
      action: () => navigate('/visualizations'),
    },
    {
      title: 'Manage Plugins',
      description: 'Extend functionality',
      icon: <Assessment />,
      color: 'warning' as const,
      action: () => navigate('/plugins'),
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="div" sx={{ mb: 2 }}>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          {actions.map((action, index) => (
            <Grid item xs={12} sm={6} key={index}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                onClick={action.action}
                startIcon={action.icon}
                sx={{
                  justifyContent: 'flex-start',
                  p: 2,
                  height: 80,
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                }}
              >
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {action.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {action.description}
                </Typography>
              </Button>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

// Main Dashboard component
const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load datasets
      const datasetsResponse = await dataAPI.getDatasets();
      setDatasets(datasetsResponse.datasets);

      // Load recent analyses
      const analysisResponse = await analysisAPI.getAnalysisResults(undefined, undefined, 10);
      setRecentAnalyses(analysisResponse.results);

      // Load insights from the most recent dataset
      if (datasetsResponse.datasets.length > 0) {
        const latestDataset = datasetsResponse.datasets[0];
        try {
          const insightsData = await insightsAPI.getInsights(latestDataset.data_id);
          setInsights(insightsData);
        } catch (error) {
          // Insights might not exist yet
          setInsights([]);
        }
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      dispatch(addNotification({
        message: 'Failed to load dashboard data',
        type: 'error',
      }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
    
    dispatch(addNotification({
      message: 'Dashboard refreshed',
      type: 'success',
    }));
  };

  // Calculate summary statistics
  const totalTrades = datasets.reduce((sum, dataset) => sum + dataset.trade_count, 0);
  const totalProfit = datasets.reduce((sum, dataset) => sum + (dataset.summary_stats?.total_profit || 0), 0);
  const avgWinRate = datasets.length > 0 
    ? datasets.reduce((sum, dataset) => sum + (dataset.summary_stats?.win_rate || 0), 0) / datasets.length 
    : 0;
  const criticalInsights = insights.filter(i => i.type === 'critical').length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 600, mb: 1 }}>
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Overview of your trading performance and insights
          </Typography>
        </Box>
        <Tooltip title="Refresh dashboard">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            <Refresh sx={{ transform: refreshing ? 'rotate(360deg)' : 'none', transition: 'transform 1s' }} />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Statistics cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Trades"
            value={totalTrades.toLocaleString()}
            subtitle={`Across ${datasets.length} datasets`}
            icon={<Assessment />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Profit"
            value={`$${totalProfit.toFixed(2)}`}
            subtitle="All-time performance"
            icon={<TrendingUp />}
            color={totalProfit >= 0 ? 'success' : 'error'}
            trend={totalProfit >= 0 ? 'up' : 'down'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Average Win Rate"
            value={`${avgWinRate.toFixed(1)}%`}
            subtitle="Across all datasets"
            icon={<Timeline />}
            color={avgWinRate >= 50 ? 'success' : 'warning'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Critical Insights"
            value={criticalInsights}
            subtitle="Requiring attention"
            icon={<Lightbulb />}
            color={criticalInsights > 0 ? 'error' : 'success'}
          />
        </Grid>
      </Grid>

      {/* Main content */}
      <Grid container spacing={3}>
        {/* Recent insights */}
        <Grid item xs={12} lg={8}>
          <RecentInsights insights={insights} loading={false} />
        </Grid>

        {/* Quick actions */}
        <Grid item xs={12} lg={4}>
          <QuickActions />
        </Grid>

        {/* Recent analyses */}
        {recentAnalyses.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" component="div">
                    Recent Analyses
                  </Typography>
                  <Button
                    size="small"
                    onClick={() => navigate('/analysis')}
                    endIcon={<Analytics />}
                  >
                    View All
                  </Button>
                </Box>
                
                <Grid container spacing={2}>
                  {recentAnalyses.slice(0, 4).map((analysis) => (
                    <Grid item xs={12} sm={6} md={3} key={analysis.analysis_id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                            {analysis.analysis_type.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {new Date(analysis.timestamp).toLocaleDateString()}
                          </Typography>
                          <Chip
                            size="small"
                            label={analysis.status}
                            color={analysis.status === 'completed' ? 'success' : 'default'}
                            variant="outlined"
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Empty state */}
        {datasets.length === 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Upload sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" sx={{ mb: 2 }}>
                  No Trading Data Yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Upload your MT5/MT4 trading history to start analyzing your performance
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => navigate('/data')}
                  startIcon={<Upload />}
                >
                  Upload Trading Data
                </Button>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Dashboard;