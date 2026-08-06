import React from 'react';
import { usePermissions } from '../../context/PermissionsContext';

const LimitIndicator = ({ limitName, usageName, label }) => {
    const { getLimit, getUsage, isLoading } = usePermissions();

    if (isLoading) {
        return <div className="h-2 w-full bg-gray-200 animate-pulse rounded-full mt-2"></div>;
    }

    const limit = getLimit(limitName);
    const usage = getUsage(usageName) || 0;

    if (limit === undefined) {
        return null;
    }

    const isUnlimited = limit === -1;
    const percentage = isUnlimited ? 0 : Math.min((usage / limit) * 100, 100);
    
    let colorClass = "bg-blue-600";
    if (!isUnlimited) {
        if (percentage >= 90) colorClass = "bg-red-600";
        else if (percentage >= 75) colorClass = "bg-yellow-500";
    }

    return (
        <div className="mt-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
            <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700">{label}</span>
                <span className="text-sm text-gray-500">
                    {usage} {isUnlimited ? '' : `/ ${limit}`}
                </span>
            </div>
            {!isUnlimited && (
                <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
                    <div className={`${colorClass} h-2.5 rounded-full transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
                </div>
            )}
            {isUnlimited && (
                <div className="text-xs text-green-600 mt-1 font-medium">Unlimited Access</div>
            )}
            {!isUnlimited && percentage >= 90 && (
                <div className="text-xs text-red-600 mt-2 font-medium">Approaching limit. Consider upgrading.</div>
            )}
        </div>
    );
};

export default LimitIndicator;
