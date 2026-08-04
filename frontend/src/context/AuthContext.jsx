import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

import { jwtDecode } from "jwt-decode";
import profileService from "../services/company/profileService";

const AuthContext = createContext();

export function AuthProvider({ children }) {

    const [token, setToken] = useState(
        localStorage.getItem("accessToken")
    );

    const [refreshToken, setRefreshToken] = useState(
        localStorage.getItem("refreshToken")
    );

    const [user, setUser] = useState(null);

    const [companyProfile, setCompanyProfile] = useState(null);

    const [loading, setLoading] = useState(true);

    useEffect(() => {

        if (!token) {

            setUser(null);
            setLoading(false);

            return;

        }

        try {

            const decoded = jwtDecode(token);

            if (decoded.exp * 1000 < Date.now()) {

                logout();

                return;

            }

            setUser({

                id: decoded.sub,

                name: decoded.name || "",

                email: decoded.email || "",

                role: decoded.role,

                companyId: decoded.company_id || null,

                recruiterId: decoded.recruiter_id || null,

                candidateId: decoded.candidate_id || null,

                campaignId: decoded.campaign_id || null,

                exp: decoded.exp,

            });

            if (decoded.role === "company") {
                profileService.getProfile().then(profile => {
                    setCompanyProfile(profile);
                }).catch(err => {
                    console.error("Failed to fetch company profile:", err);
                });
            } else {
                setCompanyProfile(null);
            }

        }

        catch (err) {

            console.error("Invalid JWT:", err);

            logout();

        }

        finally {

            setLoading(false);

        }

    }, [token]);

    // ==========================
    // Authentication
    // ==========================

    const login = (accessToken, refresh = null, companyName = null) => {

        localStorage.setItem(
            "accessToken",
            accessToken
        );

        if (refresh) {

            localStorage.setItem(
                "refreshToken",
                refresh
            );

            setRefreshToken(refresh);

        }

        if (companyName) {
            localStorage.setItem("companyName", companyName);
        }

        setToken(accessToken);

    };

    const logout = () => {

        localStorage.removeItem("accessToken");

        localStorage.removeItem("refreshToken");

        localStorage.removeItem("companyName");

        setToken(null);

        setRefreshToken(null);

        setUser(null);
        setCompanyProfile(null);

    };

    const refreshUser = () => {

        if (!token) return;

        try {

            const decoded = jwtDecode(token);

            setUser({

                id: decoded.sub,

                name: decoded.name || "",

                email: decoded.email || "",

                role: decoded.role,

                companyId: decoded.company_id || null,

                recruiterId: decoded.recruiter_id || null,

                candidateId: decoded.candidate_id || null,

                campaignId: decoded.campaign_id || null,

                exp: decoded.exp,

            });

            if (decoded.role === "company" && !companyProfile) {
                profileService.getProfile().then(profile => {
                    setCompanyProfile(profile);
                }).catch(err => {
                    console.error("Failed to fetch company profile:", err);
                });
            }

        }

        catch {

            logout();

        }

    };

    const hasRole = (...roles) => {

        return roles.includes(user?.role);

    };

    const isAdmin = user?.role === "admin";

    const isCompany = user?.role === "company";

    const isRecruiter = user?.role === "recruiter";

    const isCandidate = user?.role === "candidate";

    return (

        <AuthContext.Provider

            value={{

                token,

                refreshToken,

                user,

                companyProfile,

                setCompanyProfile,

                loading,

                login,

                logout,

                refreshUser,

                hasRole,

                isAdmin,

                isCompany,

                isRecruiter,

                isCandidate,

                isAuthenticated: !!token,

            }}

        >

            {children}

        </AuthContext.Provider>

    );

}

export function useAuthContext() {

    const context = useContext(AuthContext);

    if (!context) {

        throw new Error(

            "useAuthContext must be used within AuthProvider"

        );

    }

    return context;

}