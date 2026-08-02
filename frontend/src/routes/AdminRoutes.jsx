import { Routes, Route, Navigate } from "react-router-dom";

// Main
import Dashboard from "../pages/admin/Dashboard";

// Recruitment
import Companies from "../pages/admin/Companies";
import CompanyDetail from "../pages/admin/CompanyDetail";
import NewCompany from "../pages/admin/NewCompany";
import EditCompany from "../pages/admin/EditCompany";
import Recruiters from "../pages/admin/Recruiters";
import RecruiterDetail from "../pages/admin/RecruiterDetail";
import AdminCandidates from "../pages/admin/AdminCandidates";
import AdminCandidateDetail from "../pages/admin/AdminCandidateDetail";
import Interviews from "../pages/admin/Interviews";
import InterviewCalendar from "../pages/admin/InterviewCalendar";

// AI Center
import AIInsights from "../pages/admin/AIInsights";
import ResumeScreening from "../pages/admin/ResumeScreening";
import InterviewAnalysis from "../pages/admin/InterviewAnalysis";
import AIReports from "../pages/admin/AIReports";

// Analytics
import Reports from "../pages/admin/Reports";
import HiringAnalytics from "../pages/admin/HiringAnalytics";
import Performance from "../pages/admin/Performance";

// Platform
import Users from "../pages/admin/Users";
import SecurityLogs from "../pages/admin/SecurityLogs";
import SystemHealth from "../pages/admin/SystemHealth";
import PlatformSettings from "../pages/admin/PlatformSettings";
import AdminProfile from "../pages/admin/AdminProfile";

export default function AdminRoutes() {
    return (
        <Routes>
            <Route index element={<Navigate to="dashboard" replace />} />

            {/* ─── MAIN ─── */}
            <Route path="dashboard" element={<Dashboard />} />

            {/* ─── RECRUITMENT ─── */}
            <Route path="companies" element={<Companies />} />
            <Route path="companies/new" element={<NewCompany />} />
            <Route path="companies/:companyId" element={<CompanyDetail />} />
            <Route path="companies/edit/:companyId" element={<EditCompany />} />

            <Route path="recruiters" element={<Recruiters />} />
            <Route path="recruiters/:recruiterId" element={<RecruiterDetail />} />

            <Route path="candidates" element={<AdminCandidates />} />
            <Route path="candidates/:candidateId" element={<AdminCandidateDetail />} />

            <Route path="interviews" element={<Interviews />} />
            <Route path="interview-calendar" element={<InterviewCalendar />} />

            {/* ─── AI CENTER ─── */}
            <Route path="ai-insights" element={<AIInsights />} />
            <Route path="resume-screening" element={<ResumeScreening />} />
            <Route path="interview-analysis" element={<InterviewAnalysis />} />
            <Route path="ai-reports" element={<AIReports />} />

            {/* ─── ANALYTICS ─── */}
            <Route path="reports" element={<Reports />} />
            <Route path="hiring-analytics" element={<HiringAnalytics />} />
            <Route path="performance" element={<Performance />} />

            {/* ─── PLATFORM ─── */}
            <Route path="users" element={<Users />} />
            <Route path="security-logs" element={<SecurityLogs />} />
            <Route path="system-health" element={<SystemHealth />} />
            <Route path="platform-settings" element={<PlatformSettings />} />
            <Route path="profile" element={<AdminProfile />} />

            {/* ─── CATCH-ALL ─── */}
            <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Routes>
    );
}