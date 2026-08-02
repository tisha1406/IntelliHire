import { useQuery } from "@tanstack/react-query";
import { DashboardAPI } from "../api/dashboard";

export function useAdminDashboard() {
    return useQuery({
        queryKey: ["admin-dashboard"],
        queryFn: DashboardAPI.getDashboard,
        staleTime: 1000 * 60,
        gcTime: 1000 * 60 * 5,
        retry: 1,
    });
}

export function useAdminNotifications() {
    return useQuery({
        queryKey: ["admin-notifications"],
        queryFn: async () => {
            return []; // Placeholder until API is connected
        },
        staleTime: 1000 * 60,
    });
}
