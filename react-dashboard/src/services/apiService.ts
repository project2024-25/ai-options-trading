// src/services/apiService.ts
import axios from 'axios';

// Base URLs for microservices
const BASE_URLS = {
  dataAcquisition: 'http://localhost:8001',
  technicalAnalysis: 'http://localhost:8002',
  mlService: 'http://localhost:8003',
  strategyEngine: 'http://localhost:8004',
  riskManagement: 'http://localhost:8005',
  optionsAnalytics: 'http://localhost:8006',
};

// Create axios instances for each service
const createApiInstance = (baseURL: string) => {
  return axios.create({
    baseURL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

const apiClients = {
  dataAcquisition: createApiInstance(BASE_URLS.dataAcquisition),
  technicalAnalysis: createApiInstance(BASE_URLS.technicalAnalysis),
  mlService: createApiInstance(BASE_URLS.mlService),
  strategyEngine: createApiInstance(BASE_URLS.strategyEngine),
  riskManagement: createApiInstance(BASE_URLS.riskManagement),
  optionsAnalytics: createApiInstance(BASE_URLS.optionsAnalytics),
};

// Types
export interface MarketSnapshot {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  timestamp: string;
}

export interface OptionsChainData {
  symbol: string;
  expiry: string;
  strike: number;
  optionType: 'CE' | 'PE';
  ltp: number;
  bid: number;
  ask: number;
  volume: number;
  oi: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  iv: number;
}

export interface TradingSignal {
  id: string;
  timestamp: string;
  symbol: string;
  strategy: string;
  signalType: 'BUY' | 'SELL';
  confidence: number;
  entryPrice: number;
  stopLoss: number;
  target: number;
  rationale: string;
}

export interface Position {
  id: string;
  symbol: string;
  strategy: string;
  entryDate: string;
  entryPrice: number;
  currentPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

export interface PortfolioMetrics {
  totalValue: number;
  dailyPnl: number;
  totalPnl: number;
  totalPnlPercent: number;
  netDelta: number;
  netGamma: number;
  netTheta: number;
  netVega: number;
  marginUsed: number;
  marginAvailable: number;
}

// Mock data for development
const mockMarketData: MarketSnapshot = {
  symbol: 'NIFTY',
  price: 19845.50,
  change: 125.30,
  changePercent: 0.63,
  volume: 45234567,
  timestamp: new Date().toISOString(),
};

const mockBankNiftyData: MarketSnapshot = {
  symbol: 'BANKNIFTY',
  price: 45123.75,
  change: -89.25,
  changePercent: -0.20,
  volume: 23456789,
  timestamp: new Date().toISOString(),
};

const mockVixData = {
  current: 13.45,
  change: 0.25,
  percentile: 35,
};

const mockSignals: TradingSignal[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    symbol: 'NIFTY',
    strategy: 'Bull Call Spread',
    signalType: 'BUY',
    confidence: 8.5,
    entryPrice: 45.50,
    stopLoss: 25.00,
    target: 75.00,
    rationale: 'Bullish momentum with low IV',
  },
];

const mockPositions: Position[] = [
  {
    id: '1',
    symbol: 'NIFTY 19900 CE',
    strategy: 'Long Call',
    entryDate: '2024-01-15',
    entryPrice: 52.50,
    currentPrice: 67.25,
    quantity: 50,
    pnl: 737.50,
    pnlPercent: 28.1,
    delta: 0.65,
    gamma: 0.012,
    theta: -8.5,
    vega: 15.2,
  },
];

const mockPortfolioMetrics: PortfolioMetrics = {
  totalValue: 125000,
  dailyPnl: 2340,
  totalPnl: 8750,
  totalPnlPercent: 7.5,
  netDelta: 145,
  netGamma: 23,
  netTheta: -125,
  netVega: 89,
  marginUsed: 45000,
  marginAvailable: 80000,
};

// API Service Class
export class ApiService {
  // Market Data APIs
  static async getNiftySnapshot(): Promise<MarketSnapshot> {
    try {
      const response = await apiClients.dataAcquisition.get('/api/data/nifty-snapshot');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for NIFTY snapshot');
      return mockMarketData;
    }
  }

  static async getBankNiftySnapshot(): Promise<MarketSnapshot> {
    try {
      const response = await apiClients.dataAcquisition.get('/api/data/banknifty-snapshot');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for BANKNIFTY snapshot');
      return mockBankNiftyData;
    }
  }

  static async getVixData() {
    try {
      const response = await apiClients.dataAcquisition.get('/api/data/vix-data');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for VIX');
      return mockVixData;
    }
  }

  static async getOptionsChain(symbol: string): Promise<OptionsChainData[]> {
    try {
      const response = await apiClients.dataAcquisition.get(`/api/data/options-chain/${symbol.toLowerCase()}`);
      return response.data;
    } catch (error) {
      console.warn(`Using mock data for ${symbol} options chain`);
      return [];
    }
  }

  // Trading Signals APIs
  static async getCurrentSignals(): Promise<TradingSignal[]> {
    try {
      const response = await apiClients.strategyEngine.get('/api/strategy/current-signals');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for signals');
      return mockSignals;
    }
  }

  // Portfolio APIs
  static async getActivePositions(): Promise<Position[]> {
    try {
      const response = await apiClients.riskManagement.get('/api/risk/active-positions');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for positions');
      return mockPositions;
    }
  }

  static async getPortfolioMetrics(): Promise<PortfolioMetrics> {
    try {
      const response = await apiClients.riskManagement.get('/api/risk/portfolio-metrics');
      return response.data;
    } catch (error) {
      console.warn('Using mock data for portfolio metrics');
      return mockPortfolioMetrics;
    }
  }

  // Technical Analysis APIs
  static async getTechnicalIndicators(symbol: string, timeframe: string) {
    try {
      const response = await apiClients.technicalAnalysis.get(`/api/analysis/${symbol.toLowerCase()}-indicators/${timeframe}`);
      return response.data;
    } catch (error) {
      console.warn(`Using mock data for ${symbol} technical indicators`);
      return {};
    }
  }

  // System Health Check
  static async getSystemHealth() {
    const services = [
      { serviceName: 'Data Acquisition', url: '/health' },
      { serviceName: 'Technical Analysis', url: '/health' },
      { serviceName: 'ML Service', url: '/health' },
      { serviceName: 'Strategy Engine', url: '/health' },
      { serviceName: 'Risk Management', url: '/health' },
      { serviceName: 'Options Analytics', url: '/health' },
    ];

    const clients = [
      apiClients.dataAcquisition,
      apiClients.technicalAnalysis,
      apiClients.mlService,
      apiClients.strategyEngine,
      apiClients.riskManagement,
      apiClients.optionsAnalytics,
    ];

    try {
      const results = await Promise.allSettled(
        clients.map(client => client.get('/health'))
      );

      return results.map((result, index) => ({
        service: services[index].serviceName,
        status: result.status === 'fulfilled' ? 'healthy' : 'error',
        ...(result.status === 'rejected' && { error: result.reason?.message })
      }));
    } catch (error) {
      console.warn('Health check failed, returning mock status');
      return services.map(service => ({
        service: service.serviceName,
        status: 'unknown',
      }));
    }
  }
}

export default ApiService;