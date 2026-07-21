import { Routes, Route } from "react-router-dom";

import Registration from "../pages/candidate/Registration";

export default function CandidateRoutes() {
    return (
        <Routes>
            <Route
                path="/"
                element={<Registration />}
            />
        </Routes>
    );
}