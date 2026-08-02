import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import {
    QueryClient,
    QueryClientProvider,
} from "@tanstack/react-query";

import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import App from "./App";

import "./styles/global.css";

import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { SidebarProvider } from "./context/SidebarContext";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 1000 * 60 * 5,
        },
        mutations: {
            retry: 1,
        },
    },
});

ReactDOM.createRoot(
    document.getElementById("root")
).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <ThemeProvider>
                    <SidebarProvider>
                        <AuthProvider>
                            <App />
                        </AuthProvider>
                    </SidebarProvider>
                </ThemeProvider>
            </BrowserRouter>

            {import.meta.env.DEV && (
                <ReactQueryDevtools
                    initialIsOpen={false}
                />
            )}
        </QueryClientProvider>
    </React.StrictMode>
);