import { apiRequest } from "./client";

export const getJobs = async (params = {}) => {
    const token = localStorage.getItem("accessToken");
    const searchParams = new URLSearchParams();
    
    if (params.q) searchParams.append("q", params.q);
    if (params.department) searchParams.append("department", params.department);
    if (params.employment_type) searchParams.append("employment_type", params.employment_type);
    if (params.status) searchParams.append("status", params.status);
    if (params.sort) searchParams.append("sort", params.sort);
    if (params.order) searchParams.append("order", params.order);
    if (params.page) searchParams.append("page", params.page);
    if (params.page_size) searchParams.append("page_size", params.page_size);

    const queryString = searchParams.toString();
    const endpoint = `/company/jobs${queryString ? `?${queryString}` : ""}`;
    
    return await apiRequest(endpoint, { method: "GET" }, token);
};

export const getJob = async (jobId) => {
    const token = localStorage.getItem("accessToken");
    return await apiRequest(`/company/jobs/${jobId}`, { method: "GET" }, token);
};

export const createJob = async (jobData) => {
    const token = localStorage.getItem("accessToken");
    return await apiRequest(`/company/jobs/`, {
        method: "POST",
        body: JSON.stringify(jobData)
    }, token);
};

export const updateJob = async (jobId, updateData) => {
    const token = localStorage.getItem("accessToken");
    return await apiRequest(`/company/jobs/${jobId}`, {
        method: "PATCH",
        body: JSON.stringify(updateData)
    }, token);
};

export const deleteJob = async (jobId) => {
    const token = localStorage.getItem("accessToken");
    return await apiRequest(`/company/jobs/${jobId}`, { method: "DELETE" }, token);
};
