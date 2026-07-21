import { createContext, useContext, useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";

const AuthContext = createContext();

export function AuthProvider({ children }) {
    const [token, setToken] = useState(localStorage.getItem("accessToken"));
    const [user, setUser] = useState(null);

    useEffect(() => {
        if (token) {
            try {
                const decoded = jwtDecode(token);

                setUser({
                    id: decoded.user_id,
                    role: decoded.role,
                    companyId: decoded.company_id,
                    campaignId: decoded.campaign_id,
                    exp: decoded.exp
                });
            } catch (error) {
                console.error("Invalid token", error);
                logout();
            }
        }
    }, [token]);

    const login = (jwt) => {
        localStorage.setItem("accessToken", jwt);
        setToken(jwt);
    };

    const logout = () => {
        localStorage.removeItem("accessToken");
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                token,
                user,
                login,
                logout,
                isAuthenticated: !!token
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export const useAuthContext = () => useContext(AuthContext);