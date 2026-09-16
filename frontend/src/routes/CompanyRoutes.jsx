import { Routes, Route } from "react-router-dom";

import Dashboard from "../pages/company/Dashboard";
import VerifySubscription from "../pages/company/subscription/VerifySubscription";
import Payment from "../pages/company/subscription/Payment";
import RenewSubscription from "../pages/company/subscription/RenewSubscription";
import SubscriptionManagement from "../pages/company/subscription/SubscriptionManagement";
import ChangeSubscription from "../pages/company/subscription/ChangeSubscription";

export default function CompanyRoutes() {
    return (
        <Routes>
            <Route
                path="/"
                element={<Dashboard />}
            />
            <Route path="subscription/verify" element={<VerifySubscription />} />
            <Route path="subscription/payment" element={<Payment />} />
            <Route path="subscription/renew" element={<RenewSubscription />} />
            <Route path="subscription" element={<SubscriptionManagement />} />
            <Route path="subscription/change" element={<ChangeSubscription />} />
        </Routes>
    );
}