import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthContext } from "../../context/AuthContext";
import * as api from "../../api/candidate";

// Dashboard
export function useCandidateDashboard() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_dashboard"],
        queryFn: () => api.getDashboard(token),
        enabled: !!token,
    });
}

export function useCandidateActivity() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_activity"],
        queryFn: () => api.getActivity(token),
        enabled: !!token,
    });
}

// Resume
export function useResumeStatus() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_resume_status"],
        queryFn: () => api.getResumeStatus(token),
        enabled: !!token,
    });
}

export function useResumeAnalysis() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_resume_analysis"],
        queryFn: () => api.getResumeAnalysis(token),
        enabled: !!token,
        retry: false, // Don't retry if it fails (e.g. 404 because not analyzed yet)
    });
}

export function useUploadResume() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (file) => api.uploadResume(token, file),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_dashboard"]);
            queryClient.invalidateQueries(["candidate_resume_status"]);
            queryClient.invalidateQueries(["candidate_resume_analysis"]);
            queryClient.invalidateQueries(["candidate_activity"]);
        },
    });
}

export function useCandidateDocuments() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_documents"],
        queryFn: () => api.getDocuments(token),
        enabled: !!token,
    });
}

// Profile
export function useCandidateProfile() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_profile"],
        queryFn: () => api.getProfile(token),
        enabled: !!token,
    });
}

export function useUpdateProfile() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data) => api.updateProfile(token, data),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_profile"]);
        },
    });
}

// Settings
export function useCandidateSettings() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_settings"],
        queryFn: () => api.getSettings(token),
        enabled: !!token,
    });
}

export function useUpdateSettings() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data) => api.updateSettings(token, data),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_settings"]);
        },
    });
}

// Notifications
export function useCandidateNotifications() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_notifications"],
        queryFn: () => api.getNotifications(token),
        enabled: !!token,
        refetchInterval: 30000, // Refetch every 30s
    });
}

export function useMarkNotificationsRead() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (ids) => api.markNotificationsRead(token, ids),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_notifications"]);
        },
    });
}

// Support
export function useCandidateSupport() {
    const { token } = useAuthContext();
    return useQuery({
        queryKey: ["candidate_support"],
        queryFn: () => api.getSupport(token),
        enabled: !!token,
    });
}

export function useCreateTicket() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (data) => api.createTicket(token, data),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_support"]);
        },
    });
}

// Practice & Interview
export function useStartPractice() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: () => api.startPractice(token),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_dashboard"]);
        },
    });
}

export function useCompletePractice() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: () => api.completePractice(token),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_dashboard"]);
        },
    });
}

export function useStartInterview() {
    const { token } = useAuthContext();
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: () => api.startInterview(token),
        onSuccess: () => {
            queryClient.invalidateQueries(["candidate_dashboard"]);
        },
    });
}
