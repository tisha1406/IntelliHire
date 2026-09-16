import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";

import ProtectedRoute from "./routes/ProtectedRoute";
import { PermissionsProvider } from "./context/PermissionsContext";

import AdminLayout from "./layouts/AdminLayout";
import CompanyLayout from "./layouts/CompanyLayout";
import CandidateLayout from "./layouts/CandidateLayout";

// Company / Shared Portal Pages (used by both Company Admin and Recruiter)
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
import Recruiters from "./pages/company/Recruiters";
import ChangePassword from "./pages/company/ChangePassword";

// Subscription Pages
import VerifySubscription from "./pages/company/subscription/VerifySubscription";
import Payment from "./pages/company/subscription/Payment";
import RenewSubscription from "./pages/company/subscription/RenewSubscription";
import ChangeSubscription from "./pages/company/subscription/ChangeSubscription";
import SubscriptionManagement from "./pages/company/subscription/SubscriptionManagement";

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

            {/*
             * Company Portal — shared by both Company Admins and Recruiters.
             * The backend scopes data by JWT role automatically.
             * The frontend shows/hides UI elements based on role.
             */}
            <Route
                path="/company"
                element={
                    <ProtectedRoute roles={["company", "recruiter"]}>
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
                    path="interviews"
                    element={<Interviews />}
                />

                <Route
                    path="reports"
                    element={<Reports />}
                />

                <Route
                    path="notifications"
                    element={<Notifications />}
                />

                {/* Company Admin only routes (hidden from recruiter sidebar, 403 if directly accessed) */}
                <Route
                    path="analytics"
                    element={<Analytics />}
                />

                <Route
                    path="exports"
                    element={<Exports />}
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
                    path="team"
                    element={<Team />}
                />

                <Route
                    path="recruiters"
                    element={<Recruiters />}
                />

                <Route
                    path="activity"
                    element={<Activity />}
                />

                <Route
                    path="settings"
                    element={<Settings />}
                />

                {/* Profile — renders Company profile for admins, Recruiter profile for recruiters */}
                <Route
                    path="profile"
                    element={<Profile />}
                />

                {/* Recruiter-specific: view own profile (also linked from sidebar) */}
                <Route
                    path="recruiter"
                    element={<RecruiterProfile />}
                />

                {/* First-login password change for recruiters */}
                <Route
                    path="change-password"
                    element={<ChangePassword />}
                />

                {/* Subscription Management */}
                <Route path="subscription" element={<SubscriptionManagement />} />
                <Route path="subscription/verify" element={<VerifySubscription />} />
                <Route path="subscription/payment" element={<Payment />} />
                <Route path="subscription/renew" element={<RenewSubscription />} />
                <Route path="subscription/change" element={<ChangeSubscription />} />

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