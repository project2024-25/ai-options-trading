    # Overall Application Structure

## Main Page (`src/app/page.tsx`)
- This is the entry point of your dashboard.
- It sets up a general layout with a header (displaying "AlgoTradeView Dashboard") and a main content area.
- The main content area uses a responsive CSS grid (`grid-cols-1 md:grid-cols-2 xl:grid-cols-3`) to arrange the various dashboard cards.
- It includes a dedicated section below the main grid for the `OverallServiceStatusCard`.
- A simple footer displays copyright information.

## Layout (`src/app/layout.tsx`)
- Defines the root HTML structure, including `<html>` and `<body>` tags.
- Applies global styles, fonts (Geist Sans and Mono), and sets the dark theme (`className="dark"`).
- Includes the `<Toaster />` component for displaying notifications.

## Global Styles (`src/app/globals.css`)
- Contains the Tailwind CSS base, components, and utilities.
- Defines the application's dark theme using CSS HSL variables for background, foreground, primary, accent, card, border, etc., colors, matching your style guidelines.
- Includes a custom `animate-pulse-subtle` animation for live data updates.

---

## Core Dashboard Card Components (`src/components/dashboard/`)

All dashboard cards leverage a shared `CardWrapper` component and the `useDataFetching` hook.

### `MarketOverviewCard.tsx`
- Displays real-time price information for NIFTY and BANKNIFTY.
- Shows current price, absolute change, percentage change, and a trend indicator (Bullish/Bearish/Neutral) with color-coding.
- Fetches data from:
  - `http://localhost:8001/api/data/nifty-snapshot`
  - `http://localhost:8001/api/data/banknifty-snapshot`
- Uses `TrendingUp`, `TrendingDown`, `Minus` icons from Lucide.

### `AIPredictionsPanelCard.tsx`
- Shows AI-driven market predictions for NIFTY.
- Displays predicted direction (Bullish/Bearish/Neutral) with an icon and color-coding, confidence score, expected price movement range, and market regime.
- Fetches data from: `http://localhost:8003/api/ml/direction-prediction/NIFTY`
- Uses `Cpu`, `TrendingUp`, `TrendingDown`, `Activity`, `Percent`, `Target`, `Zap` icons.

### `StrategyRecommendationsCard.tsx`
- Presents AI-recommended options trading strategies.
- Displays strategy name, underlying asset, confidence score, volatility assessment (as a badge), risk/reward ratio, and optional details like option legs, max profit/loss, and breakeven points.
- Fetches data from: `http://localhost:8004/api/strategy/auto-select`
- Uses `Lightbulb`, `ShieldCheck`, `BarChartBig`, `Activity`, `Layers`, `TrendingUp`, `TrendingDown` icons.

### `RiskManagementDashboardCard.tsx`
- Provides an overview of portfolio risk metrics.
- Displays portfolio value, Value at Risk (VaR) with confidence level, risk utilization percentage (with a progress bar), number of active positions, and maximum drawdown (amount and percent).
- Fetches data from: `http://localhost:8005/api/risk/portfolio-risk`
- Uses `Briefcase`, `ShieldAlert`, `Percent`, `BarChartHorizontalBig`, `TrendingDown` icons.
- Utilizes the `Progress` ShadCN component.

### `OptionsAnalyticsCard.tsx`
- Summarizes portfolio Greeks for NIFTY options.
- Displays Delta, Gamma, Theta, and Vega values.
- Fetches data from: `http://localhost:8006/api/options/greeks/NIFTY`
- Uses `Sigma` (or alternatives like `ArrowRightLeft`, `TrendingUp`, `Hourglass`, `Wind` as placeholders if `Sigma` isn't available) to represent Greeks.

### `TechnicalAnalysisChartsCard.tsx`
- Shows technical analysis data for NIFTY (1-hour timeframe).
- Includes a line chart for historical price data.
- Displays last price, support/resistance levels, RSI, and volume.
- Fetches data from: `http://localhost:8002/api/analysis/nifty-indicators/1hr`
- Uses `LineChart` (Lucide icon for the card title), `BarChart3`, `TrendingUp`, `TrendingDown`, `PercentSquare` icons.
- Employs `recharts` for rendering the line chart, integrated via ShadCN's `ChartContainer`.

### `OverallServiceStatusCard.tsx`
- Provides a consolidated view of the operational status of all backend microservices.
- Fetches data from all the endpoints used by the other cards.
- Displays an overall status (e.g., "All services operational") and individual statuses (Online/Offline/Loading) for each of the 6 key services.
- Uses `CheckCircle2`, `XCircle`, `Wifi`, `Loader2` icons.

---

## Shared UI Components (`src/components/shared/`)

### `CardWrapper.tsx`
- A higher-order component that wraps each dashboard card.
- Provides a consistent header structure with a title and an icon.
- Includes a `ServiceStatusIndicator` to show the loading/online/offline status and last update time for the data specific to that card.
- Handles displaying loading spinners and error messages gracefully if data fetching fails or is in progress.
- Applies a subtle pulsing animation (`animate-pulse-subtle`) on successful data updates.

### `ServiceStatusIndicator.tsx`
- A small component used within `CardWrapper` (and potentially other places) to visually indicate the status of a service or data fetch.
- Shows an icon (`loader`, `check`, `x`, `wifi-off`) and text (e.g., "Updating...", "Updated Xs ago", "Offline").
- Uses a tooltip to provide more detailed status information on hover.

---

## Custom Hooks (`src/hooks/`)

### `useDataFetching.ts`
- A crucial custom hook responsible for fetching data from the specified API endpoint.
- Manages loading state (`isLoading`), error state (`error`), online status (`isOnline`), and the timestamp of the last successful update (`lastUpdated`).
- Automatically refetches data at a `REFRESH_INTERVAL` (set to 30 seconds).
- Handles API errors and attempts to parse them as JSON, falling back to a generic error message. It keeps stale data visible if a refresh fails.

### `useToast.ts`
- Provides functionality for displaying toast notifications (used by the `<Toaster />` in `layout.tsx`).

### `use-mobile.ts`
- A hook to detect if the application is being viewed on a mobile-sized screen.

---

## UI Libraries and Styling

- **ShadCN UI (`src/components/ui/`)**: The application extensively uses pre-built, customizable UI components from ShadCN (e.g., `Card`, `Button`, `Progress`, `Skeleton`, `Tooltip`, `Chart`). These components are styled with Tailwind CSS.
- **Tailwind CSS**: Used for all styling, leveraging utility classes for a consistent and responsive design. The theme is defined in `globals.css`.
- **Lucide React**: The primary icon library used throughout the application for clear and minimalist icons.
- **Recharts**: Used for rendering charts (specifically in `TechnicalAnalysisChartsCard`) via ShadCN's chart components.

---

## Data Types (`src/types/api.ts`)
- This file defines TypeScript interfaces for all the expected API response structures (e.g., `MarketSnapshot`, `AIPrediction`, `StrategyRecommendation`, `PortfolioRisk`, `OptionsGreeks`, `TechnicalIndicators`, `ApiError`).
- This helps ensure type safety and provides clarity on the data being handled by the components.

---

This summary covers the main aspects of your UI code, its organization, and how different parts interact to create the **AlgoTradeView dashboard**.


    # Overall Application Structure:

## To run this Next.js application locally, you'll generally need to do the following:

### Install Dependencies:
If you haven't already, or if you've pulled the code to a new environment, you'll need to install the project dependencies. Open your terminal in the project's root directory and run:

```
npm install
```
(If you use yarn or pnpm, use `yarn install` or `pnpm install` respectively.)

### Run the Backend Microservices:
Your application relies on several backend microservices for data. The PRD mentions these are expected to be running on:

- http://localhost:8001 (Market Data NIFTY & BANKNIFTY)
- http://localhost:8002 (Technical Analysis Charts)
- http://localhost:8003 (AI Predictions Panel)
- http://localhost:8004 (Strategy Recommendations)
- http://localhost:8005 (Risk Management Dashboard)
- http://localhost:8006 (Options Analytics)

You'll need to ensure these services are running independently before you start the frontend application. How you run these will depend on how they are implemented (e.g., they might be separate projects, Docker containers, etc.).

### Run the Next.js Development Server:
Once the dependencies are installed and your backend services are up, you can start the Next.js development server. The package.json file specifies the command for this:

```
npm run dev
```

This command will typically start the app on http://localhost:9002 (as specified by the `-p 9002` flag in your dev script). Your terminal will show the exact address once it's running.

### (Optional) Run Genkit Development Server:
If you were actively developing or using Genkit flows (for AI features), you would also run the Genkit development server. Your package.json has scripts for this:

- For a single run:  
  ```
  npm run genkit:dev
  ```
- To watch for changes and restart:  
  ```
  npm run genkit:watch
  ```

Currently, your `src/ai/dev.ts` file is empty, so there are no flows to run, but this would be the command if you add them later.

### In summary for your current app state:

- Make sure all your backend microservices (on ports 8001-8006) are running.
- Open your terminal in the AlgoTradeView project folder.
- Run `npm install` (if you haven't).
- Run `npm run dev`.
- Open your browser to http://localhost:9002.