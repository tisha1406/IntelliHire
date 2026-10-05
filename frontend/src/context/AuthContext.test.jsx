/**
 * @vitest-environment jsdom
 *
 * G-03 regression: specs.md confirmed that the JWT never carried `name`/
 * `email`, yet AuthContext.jsx read `decoded.name`/`decoded.email` -- so
 * `user.name`/`user.email` were permanently "" for every role, everywhere a
 * component falls back to the auth context for display identity (e.g.
 * RecruiterProfile.jsx, CompanyNavbar.jsx, company Profile.jsx's error-path
 * fallback). The fix is backend-only (jwt_handler.py + auth_service.py now
 * put real name/email claims on the token); this test proves the existing,
 * already-correct frontend decode logic actually surfaces them once present.
 */
import { act, cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, afterEach } from "vitest";
import { AuthProvider, useAuthContext } from "./AuthContext";

vi.mock("../services/company/profileService", () => ({
    default: { getProfile: vi.fn(() => Promise.resolve({})) },
}));
vi.mock("../services/recruiter/recruiterService", () => ({
    default: { getProfile: vi.fn(() => Promise.resolve({ data: {} })) },
}));

function base64url(obj) {
    return btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** jwt-decode only reads the payload; it never verifies the signature. */
function fakeJwt(payload) {
    return `${base64url({ alg: "HS256", typ: "JWT" })}.${base64url(payload)}.fake-signature`;
}

function IdentityProbe() {
    const { user, loading } = useAuthContext();
    if (loading) return <div>loading</div>;
    return (
        <div>
            <span data-testid="name">{user?.name}</span>
            <span data-testid="email">{user?.email}</span>
        </div>
    );
}

const nowSeconds = () => Math.floor(Date.now() / 1000);

describe("AuthContext identity claims (G-03)", () => {
    afterEach(() => {
        cleanup();
        localStorage.clear();
    });

    it("renders user.name/user.email from the JWT's name/email claims", async () => {
        const token = fakeJwt({
            sub: "cand-1", role: "candidate",
            name: "Jane Doe", email: "jane@example.com",
            iat: nowSeconds(), exp: nowSeconds() + 3600,
        });
        localStorage.setItem("accessToken", token);

        await act(async () => {
            render(<AuthProvider><IdentityProbe /></AuthProvider>);
        });

        expect(screen.getByTestId("name").textContent).toBe("Jane Doe");
        expect(screen.getByTestId("email").textContent).toBe("jane@example.com");
    });

    it("falls back to empty strings (not a crash) for an older token with no name/email claims", async () => {
        const token = fakeJwt({
            sub: "cand-2", role: "candidate",
            iat: nowSeconds(), exp: nowSeconds() + 3600,
        });
        localStorage.setItem("accessToken", token);

        await act(async () => {
            render(<AuthProvider><IdentityProbe /></AuthProvider>);
        });

        expect(screen.getByTestId("name").textContent).toBe("");
        expect(screen.getByTestId("email").textContent).toBe("");
    });
});
