import { apiRequest } from "./client";

export const ReportsAPI = {
    getPlatformReport: async (range, token) => {
        return await apiRequest(`/admin/reports/platform?range=${range}`, {}, token);
    },
    getCompanyReport: async (range, token) => {
        return await apiRequest(`/admin/reports/company?range=${range}`, {}, token);
    },
    getInterviewReport: async (range, token) => {
        return await apiRequest(`/admin/reports/interview?range=${range}`, {}, token);
    },
    getCandidateReport: async (range, token) => {
        return await apiRequest(`/admin/reports/candidate?range=${range}`, {}, token);
    },
    getInterviewsChart: async (range, token) => {
        return await apiRequest(`/admin/reports/chart/interviews?range=${range}`, {}, token);
    },
    exportCSV: async (reportType, range, token) => {
        // Since we want to download the file directly, we usually do this differently,
        // but for now we can fetch and trigger a download blob.
        const response = await fetch(`${import.meta.env.VITE_API_URL}/admin/reports/export/csv?report_type=${reportType}&range=${range}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
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
    exportPDF: async (reportType, range, token) => {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/admin/reports/export/pdf?report_type=${reportType}&range=${range}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
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
