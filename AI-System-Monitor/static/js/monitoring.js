/**
 * Monitoring Global Helpers and Utilities
 */

// Format numbers to fixed decimals
function formatDecimals(num, decimals = 1) {
    if (num === null || num === undefined || isNaN(num)) return '0.0';
    return Number(num).toFixed(decimals);
}

// Get status badge CSS class
function getStatusClass(status) {
    switch ((status || '').toUpperCase()) {
        case 'HEALTHY':
        case 'CONNECTED':
        case 'NORMAL':
            return 'status-healthy';
        case 'WARNING':
        case 'LATENCY':
            return 'status-warning';
        case 'CRITICAL':
        case 'DISCONNECTED':
            return 'status-critical';
        default:
            return 'bg-secondary text-light';
    }
}

// Play notification sound on critical transition (optional web audio oscillator)
function playAlertBeep() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, audioCtx.currentTime); // 880 Hz
        gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.15);
    } catch (e) {
        // AudioContext may be blocked before first user interaction
    }
}
