import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, TrendingDown, Activity, AlertTriangle, DollarSign, BarChart3 } from 'lucide-react';
import './App.css';

interface MarketData {
  symbol: string;
  ltp: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

interface IndicatorData {
  timestamp: string;
  close: number;
  sma_20: number;
  ema_20: number;
  rsi: number;
  macd: number;
  bb_upper: number;
  bb_lower: number;
}

interface MLPrediction {
  symbol: string;
  direction: string;
  confidence: number;
  predicted_movement: number;
  signals: any;
}

interface StrategyData {
  recommended_strategy: string;
  market_regime: string;
  volatility_environment: string;
  confidence_score: number;
  strategy_details: any;
  risk_reward: any;
}

interface RiskData {
  portfolio_value: number;
  var_95: number;
  max_drawdown: number;
  current_positions: number;
  total_exposure: number;
  risk_utilization: number;
}

interface OptionsData {
  symbol: string;
  current_price: number;
  portfolio_greeks: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
  };
  max_pain: number;
  pcr: number;
}

const App: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [bankniftyData, setBankniftyData] = useState<MarketData | null>(null);
  const [indicators, setIndicators] = useState<IndicatorData[]>([]);
  const [mlPrediction, setMlPrediction] = useState<MLPrediction | null>(null);
  const [strategy, setStrategy] = useState<StrategyData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch market data
        const [niftyRes, bankniftyRes] = await Promise.all([
          axios.get('http://localhost:8001/api/data/nifty-snapshot'),
          axios.get('http://localhost:8001/api/data/banknifty-snapshot')
        ]);
        
        setMarketData(niftyRes.data);
        setBankniftyData(bankniftyRes.data);

        // Fetch technical indicators
        const indicatorsRes = await axios.get('http://localhost:8002/api/analysis/nifty-indicators/1hr');
        setIndicators(indicatorsRes.data.slice(-10)); // Last 10 data points

        // Fetch ML prediction
        const mlRes = await axios.get('http://localhost:8003/api/ml/direction-prediction/NIFTY');
        setMlPrediction(mlRes.data);

        // Fetch strategy recommendation
        const strategyRes = await axios.get('http://localhost:8004/api/strategy/auto-select');
        setStrategy(strategyRes.data);

        // Fetch risk data
        const riskRes = await axios.get('http://localhost:8005/api/risk/portfolio-risk');
        setRisk(riskRes.data);

        // Fetch options data
        const optionsRes = await axios.get('http://localhost:8006/api/options/greeks/NIFTY');
        setOptions(optionsRes.data);

        setError(null);
      } catch (err) {
        setError('Failed to fetch data from services');
        console.error('Data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <Activity className="animate-spin" size={48} />
        <p>Loading trading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <AlertTriangle size={48} />
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="header">
        <h1>AI Options Trading Dashboard</h1>
        <div className="status">
          <span className="status-dot active"></span>
          <span>All Services Active</span>
        </div>
      </header>

      <div className="grid">
        {/* Market Overview */}
        <div className="card market-overview">
          <h2>Market Overview</h2>
          <div className="market-items">
            <div className="market-item">
              <h3>NIFTY</h3>
              <div className="price">₹{marketData?.ltp.toFixed(2)}</div>
              <div className={`change ${marketData && marketData.change >= 0 ? 'positive' : 'negative'}`}>
                {marketData && marketData.change >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {marketData?.change_percent.toFixed(2)}%
              </div>
            </div>
            <div className="market-item">
              <h3>BANKNIFTY</h3>
              <div className="price">₹{bankniftyData?.ltp.toFixed(2)}</div>
              <div className={`change ${bankniftyData && bankniftyData.change >= 0 ? 'positive' : 'negative'}`}>
                {bankniftyData && bankniftyData.change >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {bankniftyData?.change_percent.toFixed(2)}%
              </div>
            </div>
          </div>
        </div>

        {/* ML Prediction */}
        <div className="card prediction">
          <h2>AI Prediction</h2>
          <div className="prediction-content">
            <div className="direction">
              Direction: <strong>{mlPrediction?.direction}</strong>
            </div>
            <div className="confidence">
              Confidence: <strong>{mlPrediction?.confidence.toFixed(1)}%</strong>
            </div>
            <div className="movement">
              Expected Move: <strong>{mlPrediction?.predicted_movement.toFixed(2)}%</strong>
            </div>
          </div>
        </div>

        {/* Strategy Recommendation */}
        <div className="card strategy">
          <h2>Strategy Recommendation</h2>
          <div className="strategy-content">
            <div className="strategy-name">{strategy?.recommended_strategy}</div>
            <div className="market-regime">Market: {strategy?.market_regime}</div>
            <div className="volatility">Volatility: {strategy?.volatility_environment}</div>
            <div className="confidence">Score: {strategy?.confidence_score.toFixed(1)}/10</div>
          </div>
        </div>

        {/* Risk Management */}
        <div className="card risk">
          <h2>Risk Management</h2>
          <div className="risk-content">
            <div className="risk-item">
              <span>Portfolio Value:</span>
              <span>₹{risk?.portfolio_value.toLocaleString()}</span>
            </div>
            <div className="risk-item">
              <span>VaR (95%):</span>
              <span className="negative">₹{risk?.var_95.toFixed(0)}</span>
            </div>
            <div className="risk-item">
              <span>Risk Utilization:</span>
              <span>{risk?.risk_utilization.toFixed(1)}%</span>
            </div>
            <div className="risk-item">
              <span>Active Positions:</span>
              <span>{risk?.current_positions}</span>
            </div>
          </div>
        </div>

        {/* Options Greeks */}
        <div className="card greeks">
          <h2>Portfolio Greeks</h2>
          <div className="greeks-content">
            <div className="greek-item">
              <span>Delta:</span>
              <span>{options?.portfolio_greeks.delta.toFixed(1)}</span>
            </div>
            <div className="greek-item">
              <span>Gamma:</span>
              <span>{options?.portfolio_greeks.gamma.toFixed(1)}</span>
            </div>
            <div className="greek-item">
              <span>Theta:</span>
              <span className="negative">{options?.portfolio_greeks.theta.toFixed(1)}</span>
            </div>
            <div className="greek-item">
              <span>Vega:</span>
              <span>{options?.portfolio_greeks.vega.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* Options Analytics */}
        <div className="card options-analytics">
          <h2>Options Analytics</h2>
          <div className="analytics-content">
            <div className="analytic-item">
              <span>Max Pain:</span>
              <span>{options?.max_pain}</span>
            </div>
            <div className="analytic-item">
              <span>PCR:</span>
              <span>{options?.pcr.toFixed(2)}</span>
            </div>
            <div className="analytic-item">
              <span>Current Price:</span>
              <span>₹{options?.current_price.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Technical Chart */}
        <div className="card chart">
          <h2>Technical Indicators (1H)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={indicators}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="close" stroke="#2563eb" strokeWidth={2} name="Price" />
              <Line type="monotone" dataKey="sma_20" stroke="#dc2626" strokeWidth={1} name="SMA 20" />
              <Line type="monotone" dataKey="ema_20" stroke="#16a34a" strokeWidth={1} name="EMA 20" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* RSI Chart */}
        <div className="card rsi-chart">
          <h2>RSI Indicator</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={indicators}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="rsi" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <footer className="footer">
        <p>Last updated: {new Date().toLocaleTimeString()}</p>
        <p>Phase 1 Complete | Phase 2 Dashboard Active</p>
      </footer>
    </div>
  );
};

export default App;