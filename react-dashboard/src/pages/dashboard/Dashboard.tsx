// src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Container,
  Chip,
  CircularProgress,
} from '@mui/material';
import { TrendingUp, TrendingDown, AccountBalance } from '@mui/icons-material';
import { ApiService, MarketSnapshot, PortfolioMetrics } from '../services/apiService';

interface DashboardState {
  niftyData: MarketSnapshot | null;
  bankNiftyData: MarketSnapshot | null;
  vixData: any;
  portfolioMetrics: PortfolioMetrics | null;
  loading: boolean;
}

const Dashboard: React.FC = () => {
  const [state, setState] = useState<DashboardState>({
    niftyData: null,
    bankNiftyData: null,
    vixData: null,
    portfolioMetrics: null,
    loading: true,
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [nifty, bankNifty, vix, portfolio] = await Promise.all([
          ApiService.getNiftySnapshot(),
          ApiService.getBankNiftySnapshot(),
          ApiService.getVixData(),
          ApiService.getPortfolioMetrics(),
        ]);

        setState({
          niftyData: nifty,
          bankNiftyData: bankNifty,
          vixData: vix,
          portfolioMetrics: portfolio,
          loading: false,
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setState(prev => ({ ...prev, loading: false }));
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const formatNumber = (num: number, decimals: number = 2): string => {
    return num.toLocaleString('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatCurrency = (num: number): string => {
    return `₹${formatNumber(num)}`;
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp sx={{ color: 'success.main' }} />;
    if (change < 0) return <TrendingDown sx={{ color: 'error.main' }} />;
    return null;
  };

  const getTrendColor = (change: number) => {
    if (change > 0) return 'success.main';
    if (change < 0) return 'error.main';
    return 'text.primary';
  };

  if (state.loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>
            Loading market data...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        AI Options Trading Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Market Overview */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Market Overview
              </Typography>
              
              {state.niftyData && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    NIFTY
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6">
                      {formatNumber(state.niftyData.price)}
                    </Typography>
                    {getTrendIcon(state.niftyData.change)}
                    <Typography 
                      variant="body2" 
                      sx={{ color: getTrendColor(state.niftyData.change) }}
                    >
                      {state.niftyData.change > 0 ? '+' : ''}{formatNumber(state.niftyData.change)} 
                      ({state.niftyData.changePercent > 0 ? '+' : ''}{formatNumber(state.niftyData.changePercent)}%)
                    </Typography>
                  </Box>
                </Box>
              )}

              {state.bankNiftyData && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    BANK NIFTY
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6">
                      {formatNumber(state.bankNiftyData.price)}
                    </Typography>
                    {getTrendIcon(state.bankNiftyData.change)}
                    <Typography 
                      variant="body2" 
                      sx={{ color: getTrendColor(state.bankNiftyData.change) }}
                    >
                      {state.bankNiftyData.change > 0 ? '+' : ''}{formatNumber(state.bankNiftyData.change)} 
                      ({state.bankNiftyData.changePercent > 0 ? '+' : ''}{formatNumber(state.bankNiftyData.changePercent)}%)
                    </Typography>
                  </Box>
                </Box>
              )}

              {state.vixData && (
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    VIX
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6">
                      {formatNumber(state.vixData.current)}
                    </Typography>
                    <Chip 
                      label={`${state.vixData.percentile}th percentile`}
                      size="small"
                      color={state.vixData.percentile > 80 ? 'error' : state.vixData.percentile < 20 ? 'success' : 'default'}
                    />
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Portfolio Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <AccountBalance />
                <Typography variant="h6">Portfolio</Typography>
              </Box>
              
              {state.portfolioMetrics && (
                <>
                  <Box mb={1}>
                    <Typography variant="body2" color="text.secondary">
                      Total Value
                    </Typography>
                    <Typography variant="h6">
                      {formatCurrency(state.portfolioMetrics.totalValue)}
                    </Typography>
                  </Box>

                  <Box mb={1}>
                    <Typography variant="body2" color="text.secondary">
                      Today's P&L
                    </Typography>
                    <Typography 
                      variant="h6" 
                      sx={{ color: getTrendColor(state.portfolioMetrics.dailyPnl) }}
                    >
                      {state.portfolioMetrics.dailyPnl > 0 ? '+' : ''}{formatCurrency(state.portfolioMetrics.dailyPnl)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total P&L
                    </Typography>
                    <Typography 
                      variant="h6" 
                      sx={{ color: getTrendColor(state.portfolioMetrics.totalPnl) }}
                    >
                      {state.portfolioMetrics.totalPnl > 0 ? '+' : ''}{formatCurrency(state.portfolioMetrics.totalPnl)} 
                      ({state.portfolioMetrics.totalPnlPercent > 0 ? '+' : ''}{formatNumber(state.portfolioMetrics.totalPnlPercent)}%)
                    </Typography>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Greeks Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Greeks
              </Typography>
              
              {state.portfolioMetrics && (
                <>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Delta:</Typography>
                    <Typography variant="body2">{formatNumber(state.portfolioMetrics.netDelta, 0)}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Gamma:</Typography>
                    <Typography variant="body2">{formatNumber(state.portfolioMetrics.netGamma, 0)}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Theta:</Typography>
                    <Typography variant="body2">{formatNumber(state.portfolioMetrics.netTheta, 0)}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Vega:</Typography>
                    <Typography variant="body2">{formatNumber(state.portfolioMetrics.netVega, 0)}</Typography>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Status Card */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Typography variant="body1" color="success.main">
                All systems operational. Market data updating in real-time.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Last updated: {new Date().toLocaleTimeString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;