import { NavLink } from "react-router-dom";

export default function SidebarItem({
    to,
    icon: Icon,
    label,
    collapsed
}) {

    return (

        <NavLink
            to={to}
            title={collapsed ? label : ""}
            className={({ isActive }) =>
                `sidebar-item ${isActive ? "active" : ""}`
            }
        >
            {({ isActive }) => (

                <>
                    <span className="active-indicator"></span>

                    <div className="sidebar-icon-wrapper">

                        <Icon
                            size={20}
                            strokeWidth={2}
                            className="sidebar-icon"
                        />

                    </div>

                    {!collapsed && (

                        <span className="sidebar-label">

                            {label}

                        </span>

                    )}

                    {!collapsed && isActive && (

                        <span className="sidebar-active-dot"></span>

                    )}

                </>

            )}
        </NavLink>

    );

}