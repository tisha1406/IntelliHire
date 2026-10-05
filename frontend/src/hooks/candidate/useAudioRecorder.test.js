/**
 * @vitest-environment jsdom
 */
import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useAudioRecorder } from './useAudioRecorder';

/**
 * Regression: Sarvam Saaras (the real-time STT provider) hard-rejects any
 * audio clip over 30 seconds ("Audio duration exceeds the maximum limit of
 * 30 seconds. Please use the batch API for longer audio files."), but
 * recording was previously unbounded -- a candidate could record past this
 * limit with no warning and the transcription would fail with a 400,
 * silently losing their answer in an official interview.
 *
 * Fix: useAudioRecorder auto-stops the recording 28s after it starts
 * (leaving margin below Sarvam's 30s hard limit) and exposes `autoStopped`
 * so the UI can tell the candidate what happened.
 */

class MockMediaRecorder {
    constructor(stream, options) {
        this.stream = stream;
        this.options = options;
        this.state = 'recording';
        MockMediaRecorder.instances.push(this);
    }
    start() {}
    stop() {
        this.state = 'inactive';
        if (this.ondataavailable) {
            this.ondataavailable({ data: new Blob(['chunk']), });
        }
        if (this.onstop) {
            this.onstop();
        }
    }
}
MockMediaRecorder.instances = [];
MockMediaRecorder.isTypeSupported = () => true;

describe('useAudioRecorder — 28s auto-stop guard', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        MockMediaRecorder.instances = [];
        global.MediaRecorder = MockMediaRecorder;
        global.navigator.mediaDevices = {
            getUserMedia: vi.fn().mockResolvedValue({
                getTracks: () => [{ stop: vi.fn() }],
            }),
        };
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('automatically stops the recording after 28 seconds and sets autoStopped', async () => {
        const { result } = renderHook(() => useAudioRecorder());

        await act(async () => {
            await result.current.startRecording();
        });

        expect(result.current.status).toBe('recording');
        expect(result.current.autoStopped).toBe(false);

        await act(async () => {
            vi.advanceTimersByTime(28000);
        });

        expect(result.current.status).toBe('idle');
        expect(result.current.autoStopped).toBe(true);
        expect(result.current.audioData).not.toBeNull();
    });

    it('does not set autoStopped when the candidate stops recording manually before the limit', async () => {
        const { result } = renderHook(() => useAudioRecorder());

        await act(async () => {
            await result.current.startRecording();
        });

        await act(async () => {
            vi.advanceTimersByTime(5000);
            result.current.stopRecording();
        });

        expect(result.current.status).toBe('idle');
        expect(result.current.autoStopped).toBe(false);

        // The auto-stop timer must have been cleared by the manual stop --
        // advancing past 28s total must not retroactively flip autoStopped.
        await act(async () => {
            vi.advanceTimersByTime(30000);
        });
        expect(result.current.autoStopped).toBe(false);
    });

    it('resets autoStopped on the next recording', async () => {
        const { result } = renderHook(() => useAudioRecorder());

        await act(async () => {
            await result.current.startRecording();
        });
        await act(async () => {
            vi.advanceTimersByTime(28000);
        });
        expect(result.current.autoStopped).toBe(true);

        await act(async () => {
            await result.current.startRecording();
        });
        expect(result.current.autoStopped).toBe(false);
    });

    it('does not fire the auto-stop timer after cancelRecording', async () => {
        const { result } = renderHook(() => useAudioRecorder());

        await act(async () => {
            await result.current.startRecording();
        });
        await act(async () => {
            result.current.cancelRecording();
        });

        expect(result.current.status).toBe('idle');
        expect(result.current.audioData).toBeNull();

        await act(async () => {
            vi.advanceTimersByTime(28000);
        });

        // No crash, and no stray autoStopped flip from the (cleared) timer.
        expect(result.current.autoStopped).toBe(false);
        expect(result.current.audioData).toBeNull();
    });
});
