import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { useAuthContext } from './AuthContext';
import platformConfigService from '../services/company/platformConfigService';

const PermissionsContext = createContext();

export const PermissionsProvider = ({ children }) => {
    const { isCompany, loading: authLoading, token } = useAuthContext();
    const [platformConfig, setPlatformConfig] = useState(null);
    const [configLoading, setConfigLoading] = useState(true);

    useEffect(() => {
        if (!token) {
            setPlatformConfig(null);
            setConfigLoading(false);
            return;
        }
        
        if (isCompany) {
            platformConfigService.getPlatformConfig()
                .then(data => {
                    setPlatformConfig(data);
                })
                .catch(err => {
                    console.error("Failed to load platform config:", err);
                })
                .finally(() => {
                    setConfigLoading(false);
                });
        } else {
            setPlatformConfig(null);
            setConfigLoading(false);
        }
    }, [isCompany, token]);

    const permissions = useMemo(() => {
        if (!platformConfig) {
            return {
                platform: {},
                features: {},
                limits: {},
                subscription: {},
                branding: {},
                security: {}
            };
        }
        return {
            platform: platformConfig.platform || {},
            features: platformConfig.features || {},
            limits: platformConfig.limits || {},
            subscription: platformConfig.subscription || {},
            branding: platformConfig.branding || {},
            security: platformConfig.security || {}
        };
    }, [platformConfig]);

    const hasFeature = (featureName) => {
        return !!permissions.features[featureName];
    };

    const getLimit = (limitName) => {
        return permissions.limits[limitName];
    };

    // To prevent breaking changes, map usage if we had it, but actually usage isn't in platformConfig
    // Wait, let's include usage in platformConfig if needed, but the backend doesn't return usage in platformConfig.
    // It's in companyProfile. So we can also grab usage from AuthContext if we want, or just fetch it here.
    const { companyProfile } = useAuthContext();
    const getUsage = (usageName) => {
        if (companyProfile && companyProfile.usage) {
            return companyProfile.usage[usageName];
        }
        return 0;
    };

    return (
        <PermissionsContext.Provider 
            value={{ 
                ...permissions, 
                hasFeature, 
                getLimit, 
                getUsage,
                isLoading: authLoading || configLoading
            }}
        >
            {children}
        </PermissionsContext.Provider>
    );
};

export const usePermissions = () => {
    const context = useContext(PermissionsContext);
    if (!context) {
        throw new Error("usePermissions must be used within PermissionsProvider");
    }
    return context;
};
