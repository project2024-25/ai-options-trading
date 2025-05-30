const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Data Acquisition Service
  app.use(
    '/api/data',
    createProxyMiddleware({
      target: 'http://localhost:8001',
      changeOrigin: true,
    })
  );

  // Technical Analysis Service
  app.use(
    '/api/analysis',
    createProxyMiddleware({
      target: 'http://localhost:8002',
      changeOrigin: true,
    })
  );

  // ML Service
  app.use(
    '/api/ml',
    createProxyMiddleware({
      target: 'http://localhost:8003',
      changeOrigin: true,
    })
  );

  // Strategy Engine
  app.use(
    '/api/strategy',
    createProxyMiddleware({
      target: 'http://localhost:8004',
      changeOrigin: true,
    })
  );

  // Risk Management Service
  app.use(
    '/api/risk',
    createProxyMiddleware({
      target: 'http://localhost:8005',
      changeOrigin: true,
    })
  );

  // Options Analytics Service
  app.use(
    '/api/options',
    createProxyMiddleware({
      target: 'http://localhost:8006',
      changeOrigin: true,
    })
  );
};