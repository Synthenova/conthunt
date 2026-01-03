/**
 * TypeScript declarations for YouTube IFrame Player API
 * @see https://developers.google.com/youtube/iframe_api_reference
 */

declare global {
    interface Window {
        YT: typeof YT | undefined;
        onYouTubeIframeAPIReady: (() => void) | undefined;
    }

    // eslint-disable-next-line @typescript-eslint/no-namespace
    namespace YT {
        const PlayerState: {
            UNSTARTED: -1;
            ENDED: 0;
            PLAYING: 1;
            PAUSED: 2;
            BUFFERING: 3;
            CUED: 5;
        };

        interface PlayerOptions {
            width?: number | string;
            height?: number | string;
            videoId?: string;
            playerVars?: PlayerVars;
            events?: PlayerEvents;
        }

        interface PlayerVars {
            autoplay?: 0 | 1;
            controls?: 0 | 1 | 2;
            disablekb?: 0 | 1;
            enablejsapi?: 0 | 1;
            fs?: 0 | 1;
            iv_load_policy?: 1 | 3;
            loop?: 0 | 1;
            modestbranding?: 0 | 1;
            mute?: 0 | 1;
            origin?: string;
            playsinline?: 0 | 1;
            rel?: 0 | 1;
            showinfo?: 0 | 1;
            start?: number;
        }

        interface PlayerEvents {
            onReady?: (event: PlayerEvent) => void;
            onStateChange?: (event: OnStateChangeEvent) => void;
            onError?: (event: OnErrorEvent) => void;
            onPlaybackQualityChange?: (event: PlayerEvent) => void;
            onPlaybackRateChange?: (event: PlayerEvent) => void;
            onApiChange?: (event: PlayerEvent) => void;
        }

        interface PlayerEvent {
            target: Player;
            data?: number;
        }

        interface OnStateChangeEvent extends PlayerEvent {
            data: number;
        }

        interface OnErrorEvent extends PlayerEvent {
            data: number; // 2, 5, 100, 101, or 150
        }

        class Player {
            constructor(elementId: string | HTMLElement, options: PlayerOptions);

            // Queueing functions
            cueVideoById(videoId: string, startSeconds?: number): void;
            loadVideoById(videoId: string, startSeconds?: number): void;
            cueVideoByUrl(mediaContentUrl: string, startSeconds?: number): void;
            loadVideoByUrl(mediaContentUrl: string, startSeconds?: number): void;

            // Playback controls
            playVideo(): void;
            pauseVideo(): void;
            stopVideo(): void;
            seekTo(seconds: number, allowSeekAhead?: boolean): void;

            // Volume controls
            mute(): void;
            unMute(): void;
            isMuted(): boolean;
            setVolume(volume: number): void;
            getVolume(): number;

            // Playback status
            getPlayerState(): number;
            getCurrentTime(): number;
            getDuration(): number;
            getVideoLoadedFraction(): number;

            // Player element
            getIframe(): HTMLIFrameElement;
            destroy(): void;

            // Size
            setSize(width: number, height: number): void;
        }
    }
}

export type PlayerState = -1 | 0 | 1 | 2 | 3 | 5;

export interface YouTubePlayerInstance {
    id: string;
    player: YT.Player;
    videoId: string | null;
    inUse: boolean;
    lastUsed: number;
}

// Re-export YT namespace for module usage
export type { YT };
