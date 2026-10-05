/**
 * Converts any browser-supported audio Blob (like WebM or OGG) to a PCM WAV Blob.
 * Uses the Web Audio API to decode the audio, then manually builds the WAV header.
 *
 * Diagnostic logs are prefixed [INTERVIEW] and never contain audio bytes or transcript text.
 */
export async function convertBlobToWav(blob) {
    // === DIAGNOSTIC: log input ===
    console.log(`[INTERVIEW] AUDIO_INPUT type=${blob.type} size=${blob.size}`);

    if (!blob || blob.size === 0) {
        throw new Error('[INTERVIEW] convertBlobToWav: input blob is empty');
    }

    const arrayBuffer = await blob.arrayBuffer();
    console.log(`[INTERVIEW] AUDIO_ARRAYBUFFER size=${arrayBuffer.byteLength}`);

    // Create an AudioContext for decoding.
    // NOTE: In Chrome, AudioContext starts in 'suspended' state.
    // decodeAudioData CAN silently produce all-zero samples when the context is suspended.
    // We MUST call resume() first to ensure proper decoding.
    let audioContext;
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (ctxErr) {
        throw new Error(`[INTERVIEW] Failed to create AudioContext: ${ctxErr.message}`);
    }

    // Resume the context BEFORE decoding — critical to avoid silent output in Chrome
    try {
        if (audioContext.state === 'suspended') {
            console.log(`[INTERVIEW] AUDIOCONTEXT_RESUME state=suspended — resuming before decode`);
            await audioContext.resume();
            console.log(`[INTERVIEW] AUDIOCONTEXT_RESUMED state=${audioContext.state}`);
        } else {
            console.log(`[INTERVIEW] AUDIOCONTEXT_STATE state=${audioContext.state}`);
        }
    } catch (resumeErr) {
        console.warn(`[INTERVIEW] AUDIOCONTEXT_RESUME_FAILED: ${resumeErr.message} — continuing anyway`);
    }

    let audioBuffer;
    try {
        audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    } catch (decodeErr) {
        try { audioContext.close(); } catch (_) {}
        throw new Error(`[INTERVIEW] decodeAudioData failed: ${decodeErr.message || decodeErr}`);
    }

    // DO NOT CLOSE audioContext YET! 
    // In Chrome, closing the AudioContext frees the AudioBuffer memory, causing it to render as silence.

    // === FORCE RESAMPLE TO 16kHz MONO ===
    // Chrome's decodeAudioData returns the original sample rate (e.g., 48000)
    // Sarvam Saaras STT strictly expects 16000 Hz. We MUST resample it.
    const TARGET_SAMPLE_RATE = 16000;
    const offlineCtx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(
        1, // mono
        Math.ceil(audioBuffer.duration * TARGET_SAMPLE_RATE),
        TARGET_SAMPLE_RATE
    );
    
    const source = offlineCtx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start();
    
    let resampledBuffer;
    try {
        resampledBuffer = await offlineCtx.startRendering();
        console.log(`[INTERVIEW] AUDIO_RESAMPLED from=${audioBuffer.sampleRate} to=${resampledBuffer.sampleRate}`);
    } catch (resampleErr) {
        throw new Error(`[INTERVIEW] Resampling failed: ${resampleErr.message}`);
    }

    // Use the resampled buffer for all subsequent steps
    audioBuffer = resampledBuffer;

    const decodedDurationMs = Math.round(audioBuffer.duration * 1000);
    const decodedSampleRate = audioBuffer.sampleRate;
    const decodedChannels = audioBuffer.numberOfChannels;
    const decodedSamples = audioBuffer.length;

    // Now it is safe to close the original context since we are done with its buffer
    try { audioContext.close(); } catch (_) {}

    console.log(
        `[INTERVIEW] AUDIO_DECODED duration_ms=${decodedDurationMs}` +
        ` sample_rate=${decodedSampleRate}` +
        ` channels=${decodedChannels}` +
        ` samples=${decodedSamples}`
    );

    if (audioBuffer.duration <= 0 || decodedSamples === 0) {
        throw new Error('[INTERVIEW] convertBlobToWav: decoded audio has zero duration');
    }

    // === Silence / RMS check on source data ===
    const rawData = audioBuffer.getChannelData(0);
    let sumSq = 0;
    let nonZeroCount = 0;
    for (let i = 0; i < rawData.length; i++) {
        const s = rawData[i];
        sumSq += s * s;
        if (Math.abs(s) > 0.0001) nonZeroCount++;
    }
    const rms = Math.sqrt(sumSq / rawData.length);
    console.log(
        `[INTERVIEW] AUDIO_SOURCE_ANALYSIS` +
        ` nonzero_samples=${nonZeroCount}` +
        ` rms=${rms.toFixed(6)}`
    );

    if (rms < 0.000001) {
        console.warn('[INTERVIEW] WARNING: source audio appears to be completely silent (rms≈0). Check microphone permissions and hardware.');
    }

    // === Build PCM WAV ===
    // Force mono (1 channel) for STT compatibility
    const numOfChan = 1;
    const sampleRate = decodedSampleRate;
    const numSamples = audioBuffer.length;
    const bitsPerSample = 16;
    const blockAlign = numOfChan * (bitsPerSample / 8); // 2 bytes per sample
    const byteRate = sampleRate * blockAlign;
    const pcmDataBytes = numSamples * blockAlign;
    const totalBytes = 44 + pcmDataBytes;

    const buffer = new ArrayBuffer(totalBytes);
    const view = new DataView(buffer);
    let offset = 0;

    // Helper: write a 4-character ASCII string
    function writeString(str) {
        for (let i = 0; i < str.length; i++) {
            view.setUint8(offset + i, str.charCodeAt(i));
        }
        offset += str.length;
    }

    // RIFF header
    writeString('RIFF');
    view.setUint32(offset, 36 + pcmDataBytes, true); offset += 4;
    writeString('WAVE');

    // fmt chunk
    writeString('fmt ');
    view.setUint32(offset, 16, true);            offset += 4; // chunk size = 16
    view.setUint16(offset, 1, true);             offset += 2; // PCM = 1
    view.setUint16(offset, numOfChan, true);     offset += 2;
    view.setUint32(offset, sampleRate, true);    offset += 4;
    view.setUint32(offset, byteRate, true);      offset += 4;
    view.setUint16(offset, blockAlign, true);    offset += 2;
    view.setUint16(offset, bitsPerSample, true); offset += 2;

    // data chunk
    writeString('data');
    view.setUint32(offset, pcmDataBytes, true);  offset += 4;

    // Write PCM samples (mix down to mono by averaging all channels)
    const channels = [];
    for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
        channels.push(audioBuffer.getChannelData(i));
    }

    let pcmSumSq = 0;
    let pcmNonZero = 0;
    for (let pos = 0; pos < numSamples; pos++) {
        // Average all channels into mono
        let sample = 0;
        for (let ch = 0; ch < channels.length; ch++) {
            sample += channels[ch][pos];
        }
        sample /= channels.length;
        sample = Math.max(-1, Math.min(1, sample));
        const pcmSample = sample < 0 ? Math.round(sample * 0x8000) : Math.round(sample * 0x7FFF);
        view.setInt16(offset, pcmSample, true);
        offset += 2;
        pcmSumSq += pcmSample * pcmSample;
        if (Math.abs(pcmSample) > 0) pcmNonZero++;
    }
    const pcmRms = Math.sqrt(pcmSumSq / numSamples);

    const wavBlob = new Blob([buffer], { type: 'audio/wav' });

    console.log(
        `[INTERVIEW] AUDIO_CONVERTED` +
        ` type=${wavBlob.type}` +
        ` size=${wavBlob.size}` +
        ` pcm_samples=${numSamples}` +
        ` nonzero_pcm=${pcmNonZero}` +
        ` rms_level=${pcmRms.toFixed(2)}` +
        ` sample_rate=${sampleRate}` +
        ` channels=${numOfChan}` +
        ` bits_per_sample=${bitsPerSample}`
    );

    if (pcmNonZero === 0) {
        console.warn('[INTERVIEW] WARNING: PCM output is completely silent. All samples are zero.');
    }

    // Return both the blob AND the RMS level so the caller can detect silent audio
    return { blob: wavBlob, rmsLevel: pcmRms };
}
