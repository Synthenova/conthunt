"use client";

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { loadYouTubeAPI, isYouTubeAPIReady } from "./YouTubeAPILoader";
import type { YT, YouTubePlayerInstance } from "./types";

const POOL_SIZE = 3;
const PLAYER_VARS: YT.PlayerVars = {
    autoplay: 0,
    controls: 0,
    disablekb: 1,
    enablejsapi: 1,
    fs: 0,
    iv_load_policy: 3,
    modestbranding: 1,
    mute: 1, // Start muted to allow autoplay
    origin: typeof window !== "undefined" ? window.location.origin : "",
    playsinline: 1,
    rel: 0,
    showinfo: 0,
};

interface YouTubePlayerPoolContextValue {
    isReady: boolean;
    acquirePlayer: (videoId: string, onReady?: () => void) => YouTubePlayerInstance | null;
    releasePlayer: (instanceId: string) => void;
    getPlayer: (instanceId: string) => YouTubePlayerInstance | null;
}

const YouTubePlayerPoolContext = createContext<YouTubePlayerPoolContextValue | null>(null);

export function useYouTubePlayerPool() {
    const context = useContext(YouTubePlayerPoolContext);
    if (!context) {
        throw new Error("useYouTubePlayerPool must be used within YouTubePlayerPoolProvider");
    }
    return context;
}

interface YouTubePlayerPoolProviderProps {
    children: React.ReactNode;
}

export function YouTubePlayerPoolProvider({ children }: YouTubePlayerPoolProviderProps) {
    const [isReady, setIsReady] = useState(false);
    const poolRef = useRef<YouTubePlayerInstance[]>([]);
    const containerRef = useRef<HTMLDivElement | null>(null);
    const initializingRef = useRef(false);
    const pendingCallbacksRef = useRef<Map<string, () => void>>(new Map());

    // Initialize the pool
    useEffect(() => {
        if (initializingRef.current) return;
        initializingRef.current = true;

        const initPool = async () => {
            try {
                await loadYouTubeAPI();

                if (!containerRef.current || !window.YT?.Player) {
                    console.error("YouTube API not available");
                    return;
                }

                // Create pool instances
                const instances: YouTubePlayerInstance[] = [];

                for (let i = 0; i < POOL_SIZE; i++) {
                    const id = `yt-pool-player-${i}`;

                    // Create container div for the player
                    const playerDiv = document.createElement("div");
                    playerDiv.id = id;
                    playerDiv.style.cssText = "position: absolute; width: 100%; height: 100%; top: 0; left: 0;";
                    containerRef.current.appendChild(playerDiv);

                    // Create the player
                    const player = new window.YT.Player(id, {
                        width: "100%",
                        height: "100%",
                        playerVars: PLAYER_VARS,
                        events: {
                            onReady: () => {
                                const callback = pendingCallbacksRef.current.get(id);
                                if (callback) {
                                    callback();
                                    pendingCallbacksRef.current.delete(id);
                                }
                            },
                            onStateChange: (event) => {
                                // Handle state changes if needed
                            },
                        },
                    });

                    instances.push({
                        id,
                        player,
                        videoId: null,
                        inUse: false,
                        lastUsed: 0,
                    });
                }

                poolRef.current = instances;
                setIsReady(true);
            } catch (error) {
                console.error("Failed to initialize YouTube player pool:", error);
            }
        };

        initPool();

        return () => {
            // Cleanup players on unmount
            poolRef.current.forEach((instance) => {
                try {
                    instance.player.destroy();
                } catch (e) {
                    // Ignore cleanup errors
                }
            });
            poolRef.current = [];
        };
    }, []);

    const acquirePlayer = useCallback(
        (videoId: string, onReady?: () => void): YouTubePlayerInstance | null => {
            if (!isReady) return null;

            const pool = poolRef.current;

            // First, try to find an instance already loaded with this video
            let instance = pool.find((p) => p.videoId === videoId && !p.inUse);

            // If not found, find any available instance
            if (!instance) {
                instance = pool.find((p) => !p.inUse);
            }

            // If still not found, evict the least recently used
            if (!instance) {
                const sorted = [...pool].sort((a, b) => a.lastUsed - b.lastUsed);
                instance = sorted[0];
            }

            if (!instance) return null;

            // Mark as in use
            instance.inUse = true;
            instance.lastUsed = Date.now();

            // Load the video if different
            if (instance.videoId !== videoId) {
                instance.videoId = videoId;
                try {
                    instance.player.loadVideoById(videoId, 0);
                    instance.player.pauseVideo(); // Pause immediately, let caller control play
                } catch (e) {
                    console.error("Error loading video:", e);
                }
            }

            if (onReady) {
                onReady();
            }

            return instance;
        },
        [isReady]
    );

    const releasePlayer = useCallback((instanceId: string) => {
        const instance = poolRef.current.find((p) => p.id === instanceId);
        if (instance) {
            instance.inUse = false;
            try {
                instance.player.pauseVideo();
                instance.player.seekTo(0, true);
            } catch (e) {
                // Ignore errors
            }
        }
    }, []);

    const getPlayer = useCallback((instanceId: string): YouTubePlayerInstance | null => {
        return poolRef.current.find((p) => p.id === instanceId) || null;
    }, []);

    const contextValue: YouTubePlayerPoolContextValue = {
        isReady,
        acquirePlayer,
        releasePlayer,
        getPlayer,
    };

    return (
        <YouTubePlayerPoolContext.Provider value={contextValue}>
            {/* Hidden container for pool players */}
            <div
                ref={containerRef}
                style={{
                    position: "fixed",
                    top: "-9999px",
                    left: "-9999px",
                    width: "320px",
                    height: "180px",
                    overflow: "hidden",
                    pointerEvents: "none",
                    opacity: 0,
                }}
                aria-hidden="true"
            />
            {children}
        </YouTubePlayerPoolContext.Provider>
    );
}
