/**
 * @vitest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Settings from './Settings';
import { vi, describe, it, expect, beforeEach } from 'vitest';

const mockUpdateSettings = vi.fn();

let mockSettingsData = {
    high_contrast: false,
    reduced_motion: false,
    sidebar_auto_collapse: false,
    interview_reminders: false,
    company_updates: false,
    result_notifications: false,
    portal_language: "en",
    live_subtitles: false
};

vi.mock('../../hooks/candidate/useCandidate', () => ({
    useCandidateSettings: () => ({ data: mockSettingsData, isLoading: false }),
    useUpdateSettings: () => ({ mutate: mockUpdateSettings, isPending: false })
}));

function clickToggle(labelText) {
    const labels = screen.getAllByText(labelText);
    const label = labels[0];
    const row = label.parentElement.parentElement;
    const toggleDiv = row.children[1];
    fireEvent.click(toggleDiv);
}

describe('Candidate Settings Page (Task B-01)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockSettingsData = {
            high_contrast: false,
            reduced_motion: false,
            sidebar_auto_collapse: false,
            interview_reminders: false,
            company_updates: false,
            result_notifications: false,
            portal_language: "en",
            live_subtitles: false
        };
    });

    it('renders Preferences tab and handles sidebar_auto_collapse toggle with backend field name', () => {
        render(<Settings />);
        
        expect(screen.getAllByText('System Preferences').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Sidebar Auto-Collapse').length).toBeGreaterThan(0);

        clickToggle('Sidebar Auto-Collapse');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ sidebar_auto_collapse: true });
    });

    it('handles high_contrast and reduced_motion toggles', () => {
        render(<Settings />);

        clickToggle('High Contrast Mode');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ high_contrast: true });

        clickToggle('Reduced Motion');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ reduced_motion: true });
    });

    it('renders Notifications tab and handles interview_reminders and company_updates toggles', () => {
        render(<Settings />);

        // Tab buttons are buttons in sidebar
        const buttons = screen.getAllByRole('button');
        const notifTab = buttons.find(b => b.textContent.includes('Notifications'));
        fireEvent.click(notifTab);

        expect(screen.getAllByText('Interview Reminders').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Company Updates').length).toBeGreaterThan(0);

        clickToggle('Interview Reminders');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ interview_reminders: true });

        clickToggle('Company Updates');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ company_updates: true });

        clickToggle('Result Notifications');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ result_notifications: true });
    });

    it('renders Language tab and handles portal_language and live_subtitles toggles', () => {
        render(<Settings />);

        const buttons = screen.getAllByRole('button');
        const langTab = buttons.find(b => b.textContent.includes('Language'));
        fireEvent.click(langTab);

        expect(screen.getAllByText('Portal Language').length).toBeGreaterThan(0);
        expect(screen.getAllByText('Live Subtitles').length).toBeGreaterThan(0);

        // Change language
        const selectEl = screen.getByRole('combobox');
        fireEvent.change(selectEl, { target: { value: 'es' } });
        expect(mockUpdateSettings).toHaveBeenCalledWith({ portal_language: 'es' });

        clickToggle('Live Subtitles');
        expect(mockUpdateSettings).toHaveBeenCalledWith({ live_subtitles: true });
    });
});
