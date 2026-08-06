import React from 'react';
import { usePermissions } from '../../context/PermissionsContext';
import { Lock } from 'lucide-react';

const FeatureGuard = ({ featureName, children, fallback }) => {
    const { hasFeature, isLoading } = usePermissions();

    if (isLoading) {
        return null;
    }

    if (hasFeature(featureName)) {
        return children;
    }

    if (fallback !== undefined) {
        return fallback;
    }

    return (
        <div className="flex flex-col items-center justify-center p-12 text-center bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <div className="p-3 bg-gray-100 rounded-full mb-4">
                <Lock className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Feature Locked</h3>
            <p className="text-gray-500 max-w-md">
                Your current subscription plan does not include access to this feature. 
                Please upgrade your plan to unlock it.
            </p>
        </div>
    );
};

export default FeatureGuard;
