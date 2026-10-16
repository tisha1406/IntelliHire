import { useQuery } from "@tanstack/react-query";
import { AnalyticsAPI } from "../api/analytics";

export function useAdminAnalytics() {
    return useQuery({
        queryKey: ["admin-analytics-dashboard"],
        queryFn: AnalyticsAPI.getDashboardStats,
        staleTime: 1000 * 60,
        gcTime: 1000 * 60 * 5,
        retry: 1,
    });
}
