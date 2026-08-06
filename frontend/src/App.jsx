import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";

import ProtectedRoute from "./routes/ProtectedRoute";
import { PermissionsProvider } from "./context/PermissionsContext";

import AdminLayout from "./layouts/AdminLayout";
import CompanyLayout from "./layouts/CompanyLayout";
import CandidateLayout from "./layouts/CandidateLayout";
import RecruiterLayout from "./layouts/RecruiterLayout";

import Dashboard from "./pages/company/Dashboard";
import Campaigns from "./pages/company/Campaigns";
import CampaignDetail from "./pages/company/CampaignDetail";
import NewCampaign from "./pages/company/NewCampaign";
import Candidates from "./pages/company/Candidates";
import CandidateReport from "./pages/company/CandidateReport";
import CandidateDetails from "./pages/company/CandidateDetails";
import Analytics from "./pages/company/Analytics";
import Exports from "./pages/company/Exports";
import Profile from "./pages/company/Profile";
import Settings from "./pages/company/Settings";
import Activity from "./pages/company/Activity";
import Jobs from "./pages/company/Jobs";
import JobForm from "./pages/company/JobForm";
import Interviews from "./pages/company/Interviews";
import Reports from "./pages/company/Reports";
import Team from "./pages/company/Team";
import Notifications from "./pages/company/Notifications";
import RecruiterProfile from "./pages/company/RecruiterProfile";
import EditCampaign from "./pages/company/EditCampaign";

// Recruiter Pages
import RecruiterDashboard from "./pages/recruiter/Dashboard";
import RecruiterCandidates from "./pages/recruiter/MyCandidates";
import RecruiterCampaigns from "./pages/recruiter/MyCampaigns";
import RecruiterInterviews from "./pages/recruiter/InterviewSessions";
import RecruiterReports from "./pages/recruiter/InterviewReports";
import RecruiterNotifications from "./pages/recruiter/RecruiterNotifications";
import RecruiterProfilePage from "./pages/recruiter/RecruiterProfilePage";
import ChangePassword from "./pages/recruiter/ChangePassword";

function App() {
    return (
        <Routes>

            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/admin/*"
                element={
                    <ProtectedRoute role="admin">
                        <AdminLayout />
                    </ProtectedRoute>
                }
            />

            <Route
                path="/company"
                element={
                    <ProtectedRoute role="company">
                        <PermissionsProvider>
                            <CompanyLayout />
                        </PermissionsProvider>
                    </ProtectedRoute>
                }
            >

                <Route
                    index
                    element={<Dashboard />}
                />

                <Route
                    path="dashboard"
                    element={<Dashboard />}
                />

                <Route
                    path="campaigns"
                    element={<Campaigns />}
                />

                <Route
                    path="campaigns/new"
                    element={<NewCampaign />}
                />

                <Route
                    path="campaigns/edit/:id"
                    element={<EditCampaign />}
                />

                <Route
                    path="campaigns/:id"
                    element={<CampaignDetail />}
                />

                <Route
                    path="candidates"
                    element={<Candidates />}
                />

                <Route
                    path="candidates/:id/report"
                    element={<CandidateReport />}
                />

                <Route
                    path="candidates/:id"
                    element={<CandidateDetails />}
                />

                <Route
                    path="analytics"
                    element={<Analytics />}
                />

                <Route
                    path="exports"
                    element={<Exports />}
                />

                <Route
                    path="profile"
                    element={<Profile />}
                />

                <Route
                    path="settings"
                    element={<Settings />}
                />

                <Route
                    path="activity"
                    element={<Activity />}
                />

                <Route
                    path="jobs"
                    element={<Jobs />}
                />

                <Route
                    path="jobs/new"
                    element={<JobForm />}
                />

                <Route
                    path="jobs/:id/edit"
                    element={<JobForm />}
                />

                <Route
                    path="interviews"
                    element={<Interviews />}
                />

                <Route
                    path="reports"
                    element={<Reports />}
                />

                <Route
                    path="team"
                    element={<Team />}
                />

                <Route
                    path="notifications"
                    element={<Notifications />}
                />

                <Route
                    path="recruiter"
                    element={<RecruiterProfile />}
                />

            </Route>

            <Route
                path="/recruiter"
                element={
                    <ProtectedRoute role="recruiter">
                        <RecruiterLayout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<RecruiterDashboard />} />
                <Route path="dashboard" element={<RecruiterDashboard />} />
                <Route path="candidates" element={<RecruiterCandidates />} />
                <Route path="campaigns" element={<RecruiterCampaigns />} />
                <Route path="interviews" element={<RecruiterInterviews />} />
                <Route path="reports" element={<RecruiterReports />} />
                <Route path="notifications" element={<RecruiterNotifications />} />
                <Route path="profile" element={<RecruiterProfilePage />} />
                <Route path="change-password" element={<ChangePassword />} />
            </Route>

            <Route
                path="/candidate/*"
                element={
                    <ProtectedRoute role="candidate">
                        <CandidateLayout />
                    </ProtectedRoute>
                }
            />

            <Route
                path="*"
                element={<Navigate to="/login" replace />}
            />

        </Routes>
    );
}

export default App;