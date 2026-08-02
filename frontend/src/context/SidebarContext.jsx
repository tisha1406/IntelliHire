import { createContext, useContext, useEffect, useState } from "react";

const SidebarContext = createContext();

export function SidebarProvider({ children }) {

    const getInitialState = () => {

        const savedState = localStorage.getItem("sidebarCollapsed");

        if (savedState !== null) {

            return JSON.parse(savedState);

        }

        return false;

    };

    const [collapsed, setCollapsed] = useState(getInitialState);

    useEffect(() => {

        localStorage.setItem(
            "sidebarCollapsed",
            JSON.stringify(collapsed)
        );

    }, [collapsed]);

    const toggleSidebar = () => {

        setCollapsed(prev => !prev);

    };

    return (

        <SidebarContext.Provider
            value={{
                collapsed,
                setCollapsed,
                toggleSidebar
            }}
        >

            {children}

        </SidebarContext.Provider>

    );

}

export function useSidebarContext() {

    const context = useContext(SidebarContext);

    if (!context) {

        throw new Error(
            "useSidebar must be used inside SidebarProvider"
        );

    }

    return context;

}