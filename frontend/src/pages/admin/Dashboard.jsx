import { Building2, Users, Briefcase, TrendingUp } from "lucide-react";
import { AnalyticsAPI } from "../../api/analytics";
import { useAdminDashboard } from "../../hooks/useAdminDashboard";

import WelcomeBanner from "../../components/admin/dashboard/WelcomeBanner";
import KpiCard from "../../components/admin/dashboard/KpiCard";
import QuickActions from "../../components/admin/dashboard/QuickActions";
import RecentActivity from "../../components/admin/dashboard/RecentActivity";
import SystemStatus from "../../components/admin/dashboard/SystemStatus";
import OverviewChart from "../../components/admin/dashboard/OverviewChart";
import MonthlyHiringChart from "../../components/admin/dashboard/MonthlyHiringChart";

import DashboardGrid from "../../layouts/DashboardGrid";
import StatGrid from "../../components/layout/StatGrid";
import ContentGrid from "../../components/layout/ContentGrid";

import "../../styles/admin/dashboard.css";

export default function Dashboard() {
    const {
        data: dashboard,
        isLoading,
        error
    } = useAdminDashboard();

    const welcome = dashboard?.welcome || {};
    const statistics = dashboard?.statistics || {};
    const summaryCards = dashboard?.summary_cards || {};
    const recentActivity = dashboard?.recent_activity || [];
    const systemHealth = dashboard?.system_health || {};
    const recruitmentPipeline = dashboard?.recruitment_pipeline || {};
    const charts = dashboard?.charts || {};

    return (
        <DashboardGrid>
            <WelcomeBanner
                welcome={welcome}
                statistics={statistics}
                loading={isLoading}
            />

            {error && (
                <div className="dashboard-error">
                    Unable to load dashboard data. Please refresh or contact support.
                </div>
            )}

            <StatGrid columns={4}>
                <KpiCard
                    title="Companies"
                    value={isLoading ? null : (summaryCards.companies?.count || 0).toLocaleString()}
                    change={`${summaryCards.companies?.active_count || 0} active`}
                    icon={<Building2 size={24}/>}
                    linkTo="/admin/companies"
                    loading={isLoading}
                />
                <KpiCard
                    title="Platform Users"
                    value={isLoading ? null : (summaryCards.platform_users?.count || 0).toLocaleString()}
                    change={`${summaryCards.platform_users?.active_count || 0} active`}
                    icon={<Users size={24}/>}
                    linkTo="/admin/users"
                    loading={isLoading}
                />
                <KpiCard
                    title="Interviews"
                    value={isLoading ? null : (summaryCards.interviews?.count || 0).toLocaleString()}
                    change={`${summaryCards.interviews?.active_count || 0} active now`}
                    icon={<Briefcase size={24}/>}
                    linkTo="/admin/interviews"
                    loading={isLoading}
                />
                <KpiCard
                    title="Success Rate"
                    value={isLoading ? null : summaryCards.success_rate?.count || "0%"}
                    change="Avg completion"
                    icon={<TrendingUp size={24}/>}
                    linkTo="/admin/analytics"
                    loading={isLoading}
                />
            </StatGrid>

            <QuickActions />

            <ContentGrid 
                left={<OverviewChart pipeline={recruitmentPipeline} loading={isLoading} />}
                right={<SystemStatus health={systemHealth} loading={isLoading} />}
            />

            <ContentGrid
                left={<MonthlyHiringChart data={charts?.interviews_over_time} loading={isLoading} />}
                right={<RecentActivity data={recentActivity} loading={isLoading} />}
            />
        </DashboardGrid>
    );
}