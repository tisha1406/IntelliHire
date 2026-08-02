import { apiRequest } from "./client";

// ==========================================
// Dashboard & Workflow
// ==========================================
export const getDashboard = async (token) => {
    return apiRequest("/api/candidate/dashboard", { method: "GET" }, token);
};

export const getActivity = async (token) => {
    return apiRequest("/api/candidate/activity", { method: "GET" }, token);
};

// ==========================================
// Resume & Documents
// ==========================================
export const getResumeStatus = async (token) => {
    return apiRequest("/api/candidate/resume", { method: "GET" }, token);
};

export const getResumeAnalysis = async (token) => {
    return apiRequest("/api/candidate/resume-analysis", { method: "GET" }, token);
};

export const uploadResume = async (token, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiRequest("/api/candidate/resume", { 
        method: "POST", 
        body: formData,
        // Let browser set Content-Type for FormData
        headers: { "Content-Type": undefined } 
    }, token);
};

export const getDocuments = async (token) => {
    return apiRequest("/api/candidate/documents", { method: "GET" }, token);
};

// ==========================================
// Profile & Settings
// ==========================================
export const getProfile = async (token) => {
    return apiRequest("/api/candidate/profile", { method: "GET" }, token);
};

export const updateProfile = async (token, data) => {
    return apiRequest("/api/candidate/profile", { method: "PUT", body: JSON.stringify(data) }, token);
};

export const getSettings = async (token) => {
    return apiRequest("/api/candidate/settings", { method: "GET" }, token);
};

export const updateSettings = async (token, data) => {
    return apiRequest("/api/candidate/settings", { method: "PUT", body: JSON.stringify(data) }, token);
};

// ==========================================
// Notifications & Support
// ==========================================
export const getNotifications = async (token) => {
    return apiRequest("/api/candidate/notifications", { method: "GET" }, token);
};

export const markNotificationsRead = async (token, notificationIds = null) => {
    return apiRequest("/api/candidate/notifications/read", { 
        method: "PUT", 
        body: JSON.stringify({ notification_ids: notificationIds })
    }, token);
};

export const getSupport = async (token) => {
    return apiRequest("/api/candidate/support", { method: "GET" }, token);
};

export const createTicket = async (token, data) => {
    return apiRequest("/api/candidate/support", { method: "POST", body: JSON.stringify(data) }, token);
};

// ==========================================
// Interview & Practice
// ==========================================
export const startPractice = async (token) => {
    return apiRequest("/api/candidate/practice/start", { method: "POST" }, token);
};

export const completePractice = async (token) => {
    return apiRequest("/api/candidate/practice/complete", { method: "POST" }, token);
};

export const startInterview = async (token) => {
    return apiRequest("/api/candidate/interview/start", { method: "POST" }, token);
};
