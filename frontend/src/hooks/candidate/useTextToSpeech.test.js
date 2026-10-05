/**
 * @vitest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react';
import { useTextToSpeech } from './useTextToSpeech';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('useTextToSpeech Deduplication and Lifecycle', () => {
    let mockFetch;
    let mockAudioPlay;
    let mockAudioPause;

    beforeEach(() => {
        // Mock Audio API
        mockAudioPlay = vi.fn().mockResolvedValue(undefined);
        mockAudioPause = vi.fn();

        global.Audio = vi.fn().mockImplementation(function () {
            return {
                play: mockAudioPlay,
                pause: mockAudioPause,
                currentTime: 0,
                onplay: null,
                onended: null,
                onerror: null
            };
        });

        // Mock URL API
        global.URL.createObjectURL = vi.fn(() => 'blob:test');
        global.URL.revokeObjectURL = vi.fn();

        // Mock fetch with delayed resolution to test race conditions
        mockFetch = vi.fn();
        global.fetch = mockFetch;

        // Mock speechSynthesis
        global.speechSynthesis = {
            cancel: vi.fn(),
            speak: vi.fn()
        };
        global.SpeechSynthesisUtterance = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('A & B. Calling playQuestion twice synchronously (or before promise resolves) with autoPlay=true results in exactly ONE fetch request', async () => {
        let resolveFetch;
        const fetchPromise = new Promise((resolve) => {
            resolveFetch = resolve;
        });

        mockFetch.mockReturnValue(fetchPromise);

        const { result } = renderHook(() => useTextToSpeech('http://api', () => 'token'));

        // Call playQuestion twice synchronously
        act(() => {
            result.current.playQuestion('session1', 'q1', 'text', true);
            result.current.playQuestion('session1', 'q1', 'text', true);
        });

        // Exactly one fetch should have been initiated
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Resolve the fetch
        resolveFetch({
            ok: true,
            blob: () => Promise.resolve(new Blob(['test']))
        });

        // Wait for async operations to complete
        await act(async () => {
            await new Promise(r => setTimeout(r, 0));
        });

        // Exactly one Audio object should be created and played
        expect(global.Audio).toHaveBeenCalledTimes(1);
        expect(mockAudioPlay).toHaveBeenCalledTimes(1);
    });

    it('C. A new question_record_id starts a new TTS request', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            blob: () => Promise.resolve(new Blob(['test']))
        });

        const { result } = renderHook(() => useTextToSpeech('http://api', () => 'token'));

        await act(async () => {
            await result.current.playQuestion('session1', 'q1', 'text', true);
        });

        expect(mockFetch).toHaveBeenCalledTimes(1);

        // New question ID
        await act(async () => {
            await result.current.playQuestion('session1', 'q2', 'text', true);
        });

        // Fetch is called again
        expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('D. autoPlay=false bypasses deduplication for manual replay', async () => {
        mockFetch.mockResolvedValue({
            ok: true,
            blob: () => Promise.resolve(new Blob(['test']))
        });

        const { result } = renderHook(() => useTextToSpeech('http://api', () => 'token'));

        // First auto play
        await act(async () => {
            await result.current.playQuestion('session1', 'q1', 'text', true);
        });
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Second manual play for the exact same question
        await act(async () => {
            await result.current.playQuestion('session1', 'q1', 'text', false); // autoPlay is false
        });

        // Fetch should be called a second time
        expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('E. Existing stopAudio behavior remains intact', async () => {
        const { result } = renderHook(() => useTextToSpeech('http://api', () => 'token'));

        // Directly call stopAudio
        act(() => {
            result.current.stopAudio();
        });

        // Expect speech synthesis cancel to be called
        expect(global.speechSynthesis.cancel).toHaveBeenCalledTimes(1);
        // Expect audio pause to not throw (since audioRef is null initially)
        expect(mockAudioPause).toHaveBeenCalledTimes(0);
    });

    it('F. TTS failure preserves existing fallback and does not loop', async () => {
        mockFetch.mockResolvedValue({
            ok: false,
            status: 404
        });

        const { result } = renderHook(() => useTextToSpeech('http://api', () => 'token'));

        await act(async () => {
            await result.current.playQuestion('session1', 'q1', 'fallback-text', true);
        });

        // Exactly one fetch attempted
        expect(mockFetch).toHaveBeenCalledTimes(1);

        // Should fall back to native synthesis
        expect(global.speechSynthesis.speak).toHaveBeenCalledTimes(1);

        // Calling it again synchronously should still be blocked (no infinite loop)
        await act(async () => {
            await result.current.playQuestion('session1', 'q1', 'fallback-text', true);
        });

        expect(mockFetch).toHaveBeenCalledTimes(1); // No new fetch
    });
});
