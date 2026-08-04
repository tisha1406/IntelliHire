import { apiRequest } from "./client";

const getToken = () => localStorage.getItem("accessToken");

export const ReportsAPI = {
    getPlatformReport: async (range) => {
        return await apiRequest(`/admin/reports/platform?range=${range}`, {}, getToken());
    },
    getCompanyReport: async (range) => {
        return await apiRequest(`/admin/reports/company?range=${range}`, {}, getToken());
    },
    getInterviewReport: async (range) => {
        return await apiRequest(`/admin/reports/interview?range=${range}`, {}, getToken());
    },
    getCandidateReport: async (range) => {
        return await apiRequest(`/admin/reports/candidate?range=${range}`, {}, getToken());
    },
    getInterviewsChart: async (range) => {
        return await apiRequest(`/admin/reports/chart/interviews?range=${range}`, {}, getToken());
    },
    exportCSV: async (reportType, range) => {
        // Since we want to download the file directly, we usually do this differently,
        // but for now we can fetch and trigger a download blob.
        const response = await fetch(`${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/admin/reports/export/csv?report_type=${reportType}&range=${range}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        if (!response.ok) throw new Error("Export failed");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportType}_report.csv`;
        a.click();
    },
    exportPDF: async (reportType, range) => {
        const response = await fetch(`${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/admin/reports/export/pdf?report_type=${reportType}&range=${range}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        if (!response.ok) throw new Error("Export failed");
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${reportType}_report.pdf`;
        a.click();
    }
};
