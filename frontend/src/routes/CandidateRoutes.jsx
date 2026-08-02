import { Routes, Route, Navigate } from "react-router-dom";

import Dashboard         from "../pages/candidate/Dashboard";
import Resume            from "../pages/candidate/Resume";
import InterviewRoom     from "../pages/candidate/InterviewRoom";
import InterviewComplete from "../pages/candidate/InterviewComplete";
import Reports           from "../pages/candidate/Reports";
import Profile           from "../pages/candidate/Profile";
import Settings          from "../pages/candidate/Settings";
import Support           from "../pages/candidate/Support";

export default function CandidateRoutes() {
    return (
        <Routes>
            {/* Default */}
            <Route index element={<Navigate to="dashboard" replace />} />

            {/* Core Campaign Pages */}
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="resume"    element={<Resume />} />
            <Route path="reports"   element={<Reports />} />

            {/* Official Campaign Interview */}
            <Route path="interview/:id"          element={<InterviewRoom />} />
            <Route path="interview/:id/complete" element={<InterviewComplete />} />

            {/* Account Settings */}
            <Route path="profile"  element={<Profile />} />
            <Route path="settings" element={<Settings />} />
            <Route path="support"  element={<Support />} />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="dashboard" replace />} />
        </Routes>
    );
}