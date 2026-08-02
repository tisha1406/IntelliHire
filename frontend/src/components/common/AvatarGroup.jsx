import React from "react";

export default function AvatarGroup({
    members = [],
    max = 3,
    size = "md",
    className = "",
    ...props
}) {
    const visibleMembers = members.slice(0, max);
    const extraCount = members.length - max;

    const getInitials = (member) => {
        if (typeof member === "string") {
            return member.slice(0, 2).toUpperCase();
        }
        if (member.avatar) return member.avatar;
        if (member.name) {
            return member.name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
        }
        return "CN";
    };

    return (
        <div className={`avatar-group-container size-${size} ${className}`} {...props}>
            {visibleMembers.map((member, idx) => (
                <div
                    key={member.id || idx}
                    className="avatar-group-circle"
                    style={{ zIndex: max - idx }}
                    title={member.name || (typeof member === "string" ? member : "")}
                >
                    {getInitials(member)}
                </div>
            ))}
            {extraCount > 0 && (
                <div
                    className="avatar-group-circle avatar-extra-circle"
                    style={{ zIndex: 0 }}
                    title={`${extraCount} more members`}
                >
                    +{extraCount}
                </div>
            )}
        </div>
    );
}
