import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Play, Volume2, VolumeX, X } from "lucide-react";
import { useYouTubePlayer } from "@/lib/youtube";
import { useSearchStore } from "@/lib/store";

interface MediaSpotlightProps {
    item: any;
    isOpen: boolean;
    onClose: () => void;
    mediaHeight: number | null;
    isMediaCollapsed: boolean;
    resumeTime?: number;
}

export function MediaSpotlight({
    item,
    isOpen,
    onClose,
    mediaHeight,
    isMediaCollapsed,
    resumeTime = 0,
}: MediaSpotlightProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [isScrubbing, setIsScrubbing] = useState(false);
    const [durationSeconds, setDurationSeconds] = useState<number | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const timelineRef = useRef<HTMLDivElement>(null);
    const mediaShellRef = useRef<HTMLDivElement>(null);
    const clickTimeoutRef = useRef<number | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const timeSyncRef = useRef<number | null>(null);
    const lastIsPlayingRef = useRef<boolean>(false);
    const hasAppliedResumeRef = useRef(false);
    const { mediaMuted, setMediaMuted } = useSearchStore();
    const isYouTube = item?.platform === "youtube" || item?.platform === "youtube_search";
    const link = item?.url || item?.link || item?.web_url || item?.canonical_url;
    const videoSource = item?.video_url || item?.media_url || item?.url;
    const youtubeId = useMemo(() => {
        if (!isYouTube || !link) return null;
        const matchedId = link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&?/]+)/)?.[1];
        return matchedId || item?.external_id || item?.id || null;
    }, [isYouTube, link, item?.external_id, item?.id]);

    useEffect(() => {
        console.log("[MediaSpotlight] YouTube detection", {
            platform: item?.platform,
            link,
            youtubeId: youtubeId?.slice(0, 11),
            fallbackId: item?.external_id || item?.id,
            isYouTube,
        });
    }, [item?.platform, link, youtubeId, isYouTube, item?.external_id, item?.id]);

    const youtube = useYouTubePlayer({
        videoId: youtubeId,
        preload: true,
        muted: mediaMuted,
        onReady: () => {
            console.log("[MediaSpotlight] YouTube onReady", { youtubeId: youtubeId?.slice(0, 11) });
            const dur = youtube.getDuration();
            if (dur && dur > 0) {
                setDurationSeconds(dur);
            }
        },
    });
    const {
        containerRef,
        play,
        pause,
        seekTo,
        unmute,
        isReady,
        isPrimed,
        getCurrentTime,
        getDuration,
    } = youtube;

    useEffect(() => {
        if (isOpen) {
            setIsPlaying(true);
            hasAppliedResumeRef.current = false;
        } else {
            setIsPlaying(false);
            hasAppliedResumeRef.current = false;
            setCurrentTime(0);
            if (videoRef.current) {
                videoRef.current.pause();
                videoRef.current.currentTime = 0;
            }
            if (isYouTube && youtubeId) {
                pause();
                seekTo(0);
            }
        }
        setIsFullscreen(false);
    }, [isOpen, item?.id, isYouTube, youtubeId, pause, seekTo]);

    useEffect(() => {
        if (isYouTube || !videoRef.current) return;
        const video = videoRef.current;

        if (isPlaying) {
            if (!hasAppliedResumeRef.current && resumeTime > 0) {
                const safeTime = Math.max(0, resumeTime);
                const applySeek = () => {
                    if (!Number.isNaN(video.duration) && video.duration > 0) {
                        video.currentTime = Math.min(safeTime, video.duration);
                    } else {
                        video.currentTime = safeTime;
                    }
                    setCurrentTime(video.currentTime);
                    hasAppliedResumeRef.current = true;
                };

                if (video.readyState >= 1) {
                    applySeek();
                } else {
                    const onLoaded = () => {
                        applySeek();
                        video.removeEventListener("loadedmetadata", onLoaded);
                    };
                    video.addEventListener("loadedmetadata", onLoaded);
                }
            }
            video.play().catch(() => { });
        } else {
            video.pause();
        }
    }, [isPlaying, resumeTime, isYouTube]);

    // Sync mute state for HTML5 video
    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.muted = mediaMuted;
        }
    }, [mediaMuted]);

    useEffect(() => {
        if (!isYouTube || !youtubeId) return;

        console.log("[MediaSpotlight] Toggle YouTube playback", {
            isPlaying,
            youtubeId: youtubeId?.slice(0, 11),
            isReady,
            isPrimed,
            resumeTime,
            mediaMuted,
        });

        if (lastIsPlayingRef.current === isPlaying && !isPrimed) {
            // Avoid spamming when not yet primed and state hasn't changed
            return;
        }
        lastIsPlayingRef.current = isPlaying;

        if (isPlaying) {
            if (!isPrimed) {
                // Let the hook finish priming; it will replay once ready
                play();
                return;
            }
            play();
            if (resumeTime > 0 && isReady && !hasAppliedResumeRef.current) {
                seekTo(resumeTime);
                hasAppliedResumeRef.current = true;
            }
            // unmute(); // Handled by useYouTubePlayer hook via muted prop
            const dur = getDuration();
            if (dur && dur > 0) {
                setDurationSeconds(dur);
            }
        } else {
            pause();
        }
    }, [isYouTube, youtubeId, isPlaying, resumeTime, isPrimed, isReady, play, pause, seekTo, unmute, mediaMuted, getDuration]);

    useEffect(() => {
        if (!isYouTube || !youtubeId) return;
        if (!isPlaying || !isPrimed) {
            if (timeSyncRef.current) {
                window.clearInterval(timeSyncRef.current);
                timeSyncRef.current = null;
            }
            return;
        }

        if (timeSyncRef.current) return;

        timeSyncRef.current = window.setInterval(() => {
            const current = getCurrentTime();
            const duration = getDuration();
            if (duration && duration > 0 && !durationSeconds) {
                setDurationSeconds(duration);
            }
            setCurrentTime(current);
            console.log("[MediaSpotlight] YouTube time sync", {
                youtubeId: youtubeId?.slice(0, 11),
                current: Number.isFinite(current) ? current.toFixed(2) : current,
                duration: Number.isFinite(duration) ? duration.toFixed(2) : duration,
                isPlaying,
                isPrimed,
            });
        }, 200);

        return () => {
            if (timeSyncRef.current) {
                window.clearInterval(timeSyncRef.current);
                timeSyncRef.current = null;
            }
        };
    }, [isYouTube, youtubeId, isPlaying, isPrimed, getCurrentTime, getDuration, durationSeconds]);

    const handleScrub = (clientX: number) => {
        if (!durationSeconds || !timelineRef.current) return;
        const rect = timelineRef.current.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
        const newTime = ratio * durationSeconds;
        setCurrentTime(newTime);
        setIsPlaying(true);
        console.log("[MediaSpotlight] Scrub seek", { newTime, durationSeconds });

        if (isYouTube && youtubeId && isPrimed) {
            seekTo(newTime);
            play();
            return;
        }

        if (videoRef.current) {
            videoRef.current.currentTime = newTime;
            videoRef.current.play().catch(() => { });
        }
    };

    useEffect(() => {
        if (!isScrubbing) return;
        const handleMouseMove = (e: MouseEvent) => handleScrub(e.clientX);
        const handleTouchMove = (e: TouchEvent) => {
            const touch = e.touches[0];
            if (!touch) return;
            handleScrub(touch.clientX);
        };
        const stop = () => setIsScrubbing(false);

        window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", stop);
        window.addEventListener("touchmove", handleTouchMove);
        window.addEventListener("touchend", stop);
        window.addEventListener("touchcancel", stop);

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", stop);
            window.removeEventListener("touchmove", handleTouchMove);
            window.removeEventListener("touchend", stop);
            window.removeEventListener("touchcancel", stop);
        };
    }, [isScrubbing]);

    useEffect(() => {
        return () => {
            if (clickTimeoutRef.current) {
                window.clearTimeout(clickTimeoutRef.current);
                clickTimeoutRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        const handler = () => {
            const fsElement = document.fullscreenElement;
            setIsFullscreen(!!fsElement);
        };
        document.addEventListener("fullscreenchange", handler);
        return () => {
            document.removeEventListener("fullscreenchange", handler);
        };
    }, []);

    const toggleFullscreen = () => {
        const el = mediaShellRef.current;
        if (!el) return;
        if (!document.fullscreenElement) {
            el.requestFullscreen?.().catch((err) => console.error("Fullscreen request failed", err));
        } else {
            document.exitFullscreen?.().catch((err) => console.error("Exit fullscreen failed", err));
        }
    };

    return (
        <div className="relative w-full bg-[#0A0A0A] px-5 pt-5 pb-4 shrink-0">
            <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.06] to-transparent pointer-events-none" />
            <div
                ref={mediaShellRef}
                className={cn(
                    "relative mx-auto aspect-[9/16] rounded-2xl overflow-hidden bg-black ring-1 ring-white/10 group",
                    "transition-[height,box-shadow] duration-500 ease-in-out",
                    isMediaCollapsed
                        ? "shadow-[0_12px_30px_rgba(0,0,0,0.45)]"
                        : "shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
                )}
                style={{ height: mediaHeight ? `${mediaHeight}px` : "60vh" }}
                onClick={() => {
                    // Delay single-click action to allow double-click fullscreen to win
                    if (clickTimeoutRef.current) {
                        window.clearTimeout(clickTimeoutRef.current);
                        clickTimeoutRef.current = null;
                    }
                    clickTimeoutRef.current = window.setTimeout(() => {
                        setIsPlaying((prev) => {
                            const next = !prev;
                            console.log("[MediaSpotlight] Click toggle play", { next });
                            return next;
                        });
                        clickTimeoutRef.current = null;
                    }, 220);
                }}
                onDoubleClick={(e) => {
                    e.stopPropagation();
                    if (clickTimeoutRef.current) {
                        window.clearTimeout(clickTimeoutRef.current);
                        clickTimeoutRef.current = null;
                    }
                    console.log("[MediaSpotlight] Double click fullscreen toggle");
                    toggleFullscreen();
                }}
            >
                {isYouTube && youtubeId ? (
                    <div
                        ref={containerRef}
                        className="absolute inset-0 w-full h-full pointer-events-none"
                    />
                ) : videoSource ? (
                    <video
                        ref={videoRef}
                        src={videoSource}
                        className="absolute inset-0 w-full h-full object-contain bg-black pointer-events-none"
                        muted={mediaMuted}
                        playsInline
                        preload="metadata"
                        onPlay={() => console.log("[MediaSpotlight] HTML5 video playing", { src: videoSource })}
                        onTimeUpdate={() => {
                            if (videoRef.current) {
                                setCurrentTime(videoRef.current.currentTime);
                                if (!durationSeconds && videoRef.current.duration) {
                                    setDurationSeconds(videoRef.current.duration);
                                }
                            }
                        }}
                        onLoadedMetadata={() => {
                            if (videoRef.current && videoRef.current.duration) {
                                setDurationSeconds(videoRef.current.duration);
                            }
                        }}
                        onError={(error) => console.error("[MediaSpotlight] HTML5 video error", error)}
                    >
                        Your browser does not support the video tag.
                    </video>
                ) : null}

                {!isPlaying && currentTime <= 0.01 && (
                    <>
                        <img
                            src={item.thumbnail_url || item.thumbnail}
                            alt={item.title}
                            className="absolute inset-0 w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                                size="icon"
                                variant="ghost"
                                className="h-16 w-16 rounded-full bg-white/20 hover:bg-white/30 text-white backdrop-blur-sm"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsPlaying(true);
                                }}
                            >
                                <Play className="h-8 w-8 fill-current" />
                            </Button>
                        </div>
                    </>
                )}

                {/* Mute toggle */}
                <div className="absolute top-3 right-3 z-20">
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 rounded-full bg-black/50 text-white hover:bg-black/70"
                        onClick={(e) => {
                            e.stopPropagation();
                            setMediaMuted(!mediaMuted);
                        }}
                    >
                        {mediaMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                    </Button>
                </div>

                {/* Bottom overlay with timeline + playback time */}
                <div className="absolute inset-x-0 bottom-0 z-10 p-3 pt-4 bg-gradient-to-t from-black/70 via-black/40 to-transparent">
                    <div className="flex items-center justify-end text-white mb-2">
                        <span className="text-xs font-medium font-mono text-white/90 drop-shadow-md">
                            {formatTime(currentTime)} / {formatTime(durationSeconds || 0)}
                        </span>
                    </div>
                    {durationSeconds && (
                        <div
                            ref={timelineRef}
                            className="h-2 bg-white/25 rounded-full overflow-hidden cursor-pointer"
                            onMouseDown={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsScrubbing(true);
                                handleScrub(e.clientX);
                            }}
                            onMouseUp={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                setIsScrubbing(false);
                            }}
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleScrub(e.clientX);
                            }}
                            onTouchStart={(e) => {
                                e.stopPropagation();
                                setIsScrubbing(true);
                                const clientX = e.touches[0]?.clientX;
                                if (clientX !== undefined) handleScrub(clientX);
                            }}
                            onTouchEnd={(e) => {
                                e.stopPropagation();
                                setIsScrubbing(false);
                            }}
                            onTouchCancel={(e) => {
                                e.stopPropagation();
                                setIsScrubbing(false);
                            }}
                        >
                            <div
                                className="h-full bg-white"
                                style={{ width: `${Math.min(100, Math.max(0, (currentTime / durationSeconds) * 100))}%` }}
                            />
                        </div>
                    )}
                </div>
            </div>

            <div className="absolute top-4 right-5 z-10">
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 bg-black/50 text-white hover:bg-black/70 rounded-full"
                    onClick={onClose}
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}

function formatTime(seconds: number): string {
    if (!seconds || isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}
