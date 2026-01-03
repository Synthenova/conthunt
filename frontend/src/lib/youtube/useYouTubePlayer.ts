"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { loadYouTubeAPI } from "./YouTubeAPILoader";
import type { PlayerState } from "./types";

const PLAYER_VARS: YT.PlayerVars = {
    autoplay: 1, // Start playing immediately (will be paused right away)
    controls: 0,
    disablekb: 1,
    enablejsapi: 1,
    fs: 0,
    iv_load_policy: 3,
    modestbranding: 1,
    mute: 1, // Must be muted for autoplay to work
    origin: typeof window !== "undefined" ? window.location.origin : "",
    playsinline: 1,
    rel: 0,
    showinfo: 0,
};

interface UseYouTubePlayerOptions {
    videoId: string | null;
    preload?: boolean;
    onReady?: () => void;
    onStateChange?: (state: PlayerState) => void;
    muted?: boolean;
}

interface UseYouTubePlayerReturn {
    containerRef: React.RefCallback<HTMLDivElement>;
    isReady: boolean;
    isPlaying: boolean;
    isPrimed: boolean;
    isVisible: boolean; // Whether the container is in viewport
    play: () => void;
    pause: () => void;
    seekTo: (seconds: number) => void;
    getCurrentTime: () => number;
    getDuration: () => number;
    mute: () => void;
    unmute: () => void;
    isMuted: () => boolean;
}

export function useYouTubePlayer({
    videoId,
    preload = true,
    onReady,
    onStateChange,
    muted = true,
}: UseYouTubePlayerOptions): UseYouTubePlayerReturn {
    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isPrimed, setIsPrimed] = useState(false);
    const [isVisible, setIsVisible] = useState(false);
    const playerRef = useRef<YT.Player | null>(null);
    const isReadyRef = useRef(false); // Track ready state in ref for sync access
    const containerElRef = useRef<HTMLDivElement | null>(null);
    const playerDivRef = useRef<HTMLDivElement | null>(null);
    const videoIdRef = useRef(videoId);
    const initializingRef = useRef(false);
    const onReadyRef = useRef(onReady);
    const onStateChangeRef = useRef(onStateChange);
    const preloadRef = useRef(preload);
    const hasPrimedRef = useRef(false);
    const observerRef = useRef<IntersectionObserver | null>(null);
    const hasBeenVisibleRef = useRef(false); // Track if ever been visible
    const pendingPlayRef = useRef(false); // Track if play was requested before ready

    // Keep refs updated
    useEffect(() => {
        videoIdRef.current = videoId;
    }, [videoId]);

    useEffect(() => {
        onReadyRef.current = onReady;
    }, [onReady]);

    useEffect(() => {
        onStateChangeRef.current = onStateChange;
    }, [onStateChange]);

    useEffect(() => {
        preloadRef.current = preload;
    }, [preload]);

    const createPlayer = useCallback(async () => {
        if (!containerElRef.current || !videoIdRef.current) return;
        if (playerRef.current) return;
        if (initializingRef.current) return;

        initializingRef.current = true;

        try {
            await loadYouTubeAPI();

            if (!containerElRef.current || !window.YT?.Player) {
                initializingRef.current = false;
                return;
            }

            if (!playerDivRef.current) {
                const div = document.createElement("div");
                div.style.cssText = "width: 100%; height: 100%;";
                containerElRef.current.appendChild(div);
                playerDivRef.current = div;
            }

            const player = new window.YT.Player(playerDivRef.current, {
                width: "100%",
                height: "100%",
                videoId: videoIdRef.current,
                playerVars: PLAYER_VARS,
                events: {
                    onReady: () => {
                        isReadyRef.current = true;
                        setIsReady(true);
                        onReadyRef.current?.();

                        // If play was requested before ready, play now
                        if (pendingPlayRef.current && hasPrimedRef.current) {
                            pendingPlayRef.current = false;
                            try {
                                playerRef.current?.playVideo();
                            } catch (e) {
                                // Ignore
                            }
                        }
                    },
                    onStateChange: (event) => {
                        const state = event.data as PlayerState;

                        // When video starts playing for the first time, pause it immediately
                        if (state === 1 && !hasPrimedRef.current) {
                            hasPrimedRef.current = true;
                            event.target.pauseVideo();
                            event.target.seekTo(0, true);
                            setIsPrimed(true);
                            setIsPlaying(false);

                            // If play was requested, play now that we're primed
                            if (pendingPlayRef.current) {
                                pendingPlayRef.current = false;
                                setTimeout(() => {
                                    try {
                                        playerRef.current?.playVideo();
                                    } catch (e) {
                                        // Ignore
                                    }
                                }, 50);
                            }
                            return;
                        }

                        setIsPlaying(state === 1);
                        onStateChangeRef.current?.(state);
                    },
                },
            });

            playerRef.current = player;
        } catch (error) {
            console.error("Failed to create YouTube player:", error);
        } finally {
            initializingRef.current = false;
        }
    }, []);

    const play = useCallback(() => {
        // If player doesn't exist, create it and mark pending play
        if (!playerRef.current) {
            pendingPlayRef.current = true;
            createPlayer();
            return;
        }

        // If player exists but not ready, wait for ready
        if (!isReadyRef.current) {
            pendingPlayRef.current = true;
            return;
        }

        // If primed and ready, play immediately
        try {
            playerRef.current.playVideo();
        } catch (e) {
            console.error("Error playing video:", e);
        }
    }, [createPlayer]);

    const pause = useCallback(() => {
        if (!playerRef.current) return;
        try {
            playerRef.current.pauseVideo();
        } catch (e) {
            // Ignore
        }
    }, []);

    const seekTo = useCallback((seconds: number) => {
        if (!playerRef.current) return;
        try {
            playerRef.current.seekTo(seconds, true);
        } catch (e) {
            // Ignore
        }
    }, []);

    const getCurrentTime = useCallback((): number => {
        if (!playerRef.current) return 0;
        try {
            return playerRef.current.getCurrentTime();
        } catch (e) {
            return 0;
        }
    }, []);

    const getDuration = useCallback((): number => {
        if (!playerRef.current) return 0;
        try {
            return playerRef.current.getDuration();
        } catch (e) {
            return 0;
        }
    }, []);

    const mutePlayer = useCallback(() => {
        if (!playerRef.current) return;
        try {
            playerRef.current.mute();
        } catch (e) {
            // Ignore
        }
    }, []);

    const unmutePlayer = useCallback(() => {
        if (!playerRef.current) return;
        try {
            playerRef.current.unMute();
        } catch (e) {
            // Ignore
        }
    }, []);

    const isMutedPlayer = useCallback((): boolean => {
        if (!playerRef.current) return true;
        try {
            return playerRef.current.isMuted();
        } catch (e) {
            return true;
        }
    }, []);

    // Sync mute state
    useEffect(() => {
        if (!isReady || !playerRef.current) return;
        if (muted) {
            mutePlayer();
        } else {
            unmutePlayer();
        }
    }, [muted, isReady, mutePlayer, unmutePlayer]);

    // Set up Intersection Observer
    useEffect(() => {
        if (!preload) return;

        // Clean up previous observer
        if (observerRef.current) {
            observerRef.current.disconnect();
        }

        // Create new observer with rootMargin to preload slightly before visible
        observerRef.current = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsVisible(true);
                        hasBeenVisibleRef.current = true;

                        // Create player when visible
                        if (preloadRef.current && videoIdRef.current && !playerRef.current && !initializingRef.current) {
                            createPlayer();
                        }
                    } else {
                        setIsVisible(false);
                    }
                });
            },
            {
                // Start loading when within 200px of viewport
                rootMargin: "200px",
                threshold: 0,
            }
        );

        // Observe container when available
        if (containerElRef.current) {
            observerRef.current.observe(containerElRef.current);
        }

        return () => {
            if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
            }
        };
    }, [preload, createPlayer]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (playerRef.current) {
                try {
                    playerRef.current.destroy();
                } catch (e) {
                    // Ignore
                }
                playerRef.current = null;
            }
            playerDivRef.current = null;
            hasPrimedRef.current = false;
            if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
            }
        };
    }, []);

    // Handle video ID changes
    useEffect(() => {
        if (isReady && playerRef.current && videoId && videoIdRef.current !== videoId) {
            videoIdRef.current = videoId;
            hasPrimedRef.current = false;
            setIsPrimed(false);
            try {
                playerRef.current.loadVideoById(videoId, 0);
            } catch (e) {
                console.error("Error loading new video:", e);
            }
        }
    }, [videoId, isReady]);

    const containerRef = useCallback((el: HTMLDivElement | null) => {
        // Clean up old observation
        if (containerElRef.current && observerRef.current) {
            observerRef.current.unobserve(containerElRef.current);
        }

        containerElRef.current = el;

        // Start observing new element
        if (el && observerRef.current) {
            observerRef.current.observe(el);
        }
    }, []);

    return {
        containerRef,
        isReady,
        isPlaying,
        isPrimed,
        isVisible,
        play,
        pause,
        seekTo,
        getCurrentTime,
        getDuration,
        mute: mutePlayer,
        unmute: unmutePlayer,
        isMuted: isMutedPlayer,
    };
}
