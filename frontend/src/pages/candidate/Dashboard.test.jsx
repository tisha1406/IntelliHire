/**
 * @vitest-environment jsdom
 *
 * Checkpoint-5 regression test: Dashboard's "View Report" next-action link
 * must deep-link to the candidate's own completed session (?session_id=...)
 * instead of a bare /candidate/reports, which renders Reports.jsx's "please
 * select a session" empty state instead of the actual report.
 */
import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, afterEach } from 'vitest';
import Dashboard from './Dashboard';

let mockDashboardData;

vi.mock('../../hooks/candidate/useCandidate', () => ({
    useCandidateDashboard: () => ({ data: mockDashboardData, isLoading: false }),
    useCandidateActivity: () => ({ data: { activities: [] } }),
    useCandidateDocuments: () => ({ data: { documents: [] } }),
}));

function baseDashboard(overrides = {}) {
    return {
        candidate_name: "Jane Doe",
        company_name: "Acme Corp",
        job_position: "Backend Engineer",
        readiness_score: 100,
        next_action: "VIEW_REPORT",
        stage: "INTERVIEW_COMPLETED",
        steps: [],
        official_session_id: null,
        ...overrides,
    };
}

describe('Dashboard — View Report navigation (Checkpoint 5)', () => {
    afterEach(() => {
        cleanup();
    });

    it('links to /candidate/reports with the real session_id when available', () => {
        mockDashboardData = baseDashboard({ official_session_id: "sess-official-123" });

        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        );

        const link = screen.getByRole('link', { name: /view report/i });
        expect(link.getAttribute('href')).toBe('/candidate/reports?session_id=sess-official-123');
    });

    it('falls back to the bare reports route when no session_id has been resolved yet', () => {
        mockDashboardData = baseDashboard({ official_session_id: null });

        render(
            <MemoryRouter>
                <Dashboard />
            </MemoryRouter>
        );

        const link = screen.getByRole('link', { name: /view report/i });
        expect(link.getAttribute('href')).toBe('/candidate/reports');
    });
});
