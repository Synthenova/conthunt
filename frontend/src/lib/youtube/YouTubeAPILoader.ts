/**
 * YouTube IFrame API Loader
 * Loads the YouTube IFrame API script once and provides a promise-based interface.
 */

let loadPromise: Promise<void> | null = null;
let isLoaded = false;

/**
 * Load the YouTube IFrame API script.
 * Returns a promise that resolves when the API is ready.
 * Safe to call multiple times - will only load once.
 */
export function loadYouTubeAPI(): Promise<void> {
    if (isLoaded && typeof window !== 'undefined' && window.YT?.Player) {
        return Promise.resolve();
    }

    if (loadPromise) {
        return loadPromise;
    }

    loadPromise = new Promise((resolve, reject) => {
        if (typeof window === 'undefined') {
            reject(new Error('YouTube API can only be loaded in browser'));
            return;
        }

        // Check if already loaded
        if (window.YT?.Player) {
            isLoaded = true;
            resolve();
            return;
        }

        // Store any existing callback
        const existingCallback = window.onYouTubeIframeAPIReady;

        // Set up our callback
        window.onYouTubeIframeAPIReady = () => {
            isLoaded = true;
            resolve();
            // Call any existing callback
            if (existingCallback) {
                existingCallback();
            }
        };

        // Check if script already exists
        const existingScript = document.querySelector(
            'script[src="https://www.youtube.com/iframe_api"]'
        );

        if (existingScript) {
            // Script exists but API not ready yet, wait for callback
            return;
        }

        // Create and inject the script
        const script = document.createElement('script');
        script.src = 'https://www.youtube.com/iframe_api';
        script.async = true;
        script.onerror = () => {
            loadPromise = null;
            reject(new Error('Failed to load YouTube IFrame API'));
        };

        document.head.appendChild(script);
    });

    return loadPromise;
}

/**
 * Check if the YouTube API is currently loaded and ready
 */
export function isYouTubeAPIReady(): boolean {
    return isLoaded && typeof window !== 'undefined' && !!window.YT?.Player;
}

/**
 * Preload the YouTube API during idle time.
 * Call this early (e.g., in a layout or page component) to avoid delay on first hover.
 */
export function preloadYouTubeAPI(): void {
    if (typeof window === 'undefined') return;
    if (isLoaded || loadPromise) return;

    // Use requestIdleCallback if available, otherwise setTimeout
    const scheduleLoad = window.requestIdleCallback || ((cb: () => void) => setTimeout(cb, 100));

    scheduleLoad(() => {
        loadYouTubeAPI().catch(() => {
            // Ignore preload errors - will retry on actual use
        });
    });
}
