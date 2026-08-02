import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {

    const getInitialTheme = () => {

        const savedTheme = localStorage.getItem("theme");

        if (savedTheme) {
            return savedTheme;
        }

        return window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";

    };

    const [theme, setTheme] = useState(getInitialTheme);

    useEffect(() => {

        document.documentElement.setAttribute(
            "data-theme",
            theme
        );

        localStorage.setItem(
            "theme",
            theme
        );

    }, [theme]);

    const toggleTheme = () => {

        setTheme((prevTheme) =>
            prevTheme === "dark"
                ? "light"
                : "dark"
        );

    };

    return (

        <ThemeContext.Provider
            value={{
                theme,
                toggleTheme,
                setTheme,
            }}
        >
            {children}
        </ThemeContext.Provider>

    );

}

/*
 * Keeping the same hook name so existing imports
 * (useTheme) continue to work without changes.
 */
export function useTheme() {

    const context = useContext(ThemeContext);

    if (!context) {

        throw new Error(
            "useTheme must be used within a ThemeProvider"
        );

    }

    return context;

}