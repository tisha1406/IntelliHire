import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

import { jwtDecode } from "jwt-decode";
import profileService from "../services/company/profileService";
import recruiterService from "../services/recruiter/recruiterService";

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

    const [recruiterProfile, setRecruiterProfile] = useState(null);

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

                must_change_password: decoded.must_change_password || false,

                exp: decoded.exp,

            });

            if (decoded.role === "company") {
                profileService.getProfile().then(profile => {
                    setCompanyProfile(profile);
                }).catch(err => {
                    console.error("Failed to fetch company profile:", err);
                });
            } else if (decoded.role === "recruiter") {
                // Fetch recruiter's personal profile
                recruiterService.getProfile().then(res => {
                    setRecruiterProfile(res.data?.data || res.data);
                }).catch(err => {
                    console.error("Failed to fetch recruiter profile:", err);
                });
                // Fetch the company profile for the recruiter's workspace.
                // The backend now allows recruiter role on GET /company/profile,
                // resolving company_id from the JWT's company_id claim.
                profileService.getProfile().then(profile => {
                    setCompanyProfile(profile);
                }).catch(err => {
                    console.error("Failed to fetch company profile for recruiter:", err);
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
        setRecruiterProfile(null);

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

                must_change_password: decoded.must_change_password || false,

                exp: decoded.exp,

            });

            if (decoded.role === "company" && !companyProfile) {
                profileService.getProfile().then(profile => {
                    setCompanyProfile(profile);
                }).catch(err => {
                    console.error("Failed to fetch company profile:", err);
                });
            }

            if (decoded.role === "recruiter") {
                if (!recruiterProfile) {
                    recruiterService.getProfile().then(res => {
                        setRecruiterProfile(res.data?.data || res.data);
                    }).catch(err => {
                        console.error("Failed to fetch recruiter profile:", err);
                    });
                }
                if (!companyProfile) {
                    // Reload company context for recruiter workspace
                    profileService.getProfile().then(profile => {
                        setCompanyProfile(profile);
                    }).catch(err => {
                        console.error("Failed to fetch company profile for recruiter:", err);
                    });
                }
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

                recruiterProfile,

                setCompanyProfile,

                setRecruiterProfile,

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