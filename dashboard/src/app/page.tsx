
import MarketOverviewCard from '@/components/dashboard/MarketOverviewCard';
import AIPredictionsPanelCard from '@/components/dashboard/AIPredictionsPanelCard';
import StrategyRecommendationsCard from '@/components/dashboard/StrategyRecommendationsCard';
import RiskManagementDashboardCard from '@/components/dashboard/RiskManagementDashboardCard';
import OptionsAnalyticsCard from '@/components/dashboard/OptionsAnalyticsCard';
import TechnicalAnalysisChartsCard from '@/components/dashboard/TechnicalAnalysisChartsCard';
import OverallServiceStatusCard from '@/components/dashboard/OverallServiceStatusCard';

export default function AlgoTradeViewPage() {
  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-6 lg:p-8">
      <header className="mb-8">
        <h1 className="text-xl sm:text-2xl font-bold text-primary-foreground">AlgoTradeView Dashboard</h1>
      </header>
      <main className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <MarketOverviewCard />
        <AIPredictionsPanelCard />
        <StrategyRecommendationsCard />
        <RiskManagementDashboardCard />
        <OptionsAnalyticsCard />
        <TechnicalAnalysisChartsCard />
      </main>
      <section className="mt-8">
        <OverallServiceStatusCard />
      </section>
      <footer className="mt-12 text-center text-sm text-muted-foreground">
        <p>&copy; {new Date().getFullYear()} AlgoTradeView. All data is for informational purposes only.</p>
      </footer>
    </div>
  );
}
