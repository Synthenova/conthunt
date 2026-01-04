import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
    const { mediaMuted, setMediaMuted } = useSearchStore();
    const isYouTube = item?.platform === "youtube" || item?.platform === "youtube_search";
    const creatorName = item?.creator_name || item?.creator || item?.author || item?.channel_title || "Unknown";
    const creatorHandle = item?.creator_handle || item?.username || item?.author_handle || item?.channel || item?.profile_name || "";
    const platformLabel = (item?.platform || "").replace(/_/g, " ").toUpperCase();
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
            console.log("[MediaSpotlight] YouTube onReady", { youtubeId: youtubeId?.slice(0, 11), resumeTime });
            if (resumeTime > 0) {
                youtube.seekTo(resumeTime);
            }
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
        console.log("[MediaSpotlight] Drawer open state change", {
            isOpen,
            title: item?.title,
            platform: item?.platform,
        });

        if (isOpen) {
            setIsPlaying(true);
        } else {
            setIsPlaying(false);
        }
        setIsFullscreen(false);
    }, [isOpen, item]);

    useEffect(() => {
        if (!isPlaying) return;
        if (resumeTime <= 0) return;
        if (!videoRef.current) return;

        const video = videoRef.current;
        const safeTime = Math.max(0, resumeTime);
        const seek = () => {
            if (!Number.isNaN(video.duration) && video.duration > 0) {
                video.currentTime = Math.min(safeTime, video.duration);
            } else {
                video.currentTime = safeTime;
            }
            video.play().catch(() => { });
            setCurrentTime(video.currentTime);
        };

        console.log("[MediaSpotlight] Seeking HTML5 video", { resumeTime, safeTime, duration: video.duration });

        if (video.readyState >= 1) {
            seek();
        } else {
            const onLoaded = () => {
                seek();
                video.removeEventListener("loadedmetadata", onLoaded);
            };
            video.addEventListener("loadedmetadata", onLoaded);
        }
    }, [isPlaying, resumeTime]);

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
            if (resumeTime > 0 && isReady) {
                seekTo(resumeTime);
            }
            if (!mediaMuted) {
                unmute();
            }
            const dur = getDuration();
            if (dur && dur > 0) {
                setDurationSeconds(dur);
            }
        } else {
            pause();
            seekTo(0);
            setCurrentTime(0);
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
                {!isPlaying ? (
                    <>
                        <img
                            src={item.thumbnail_url || item.thumbnail}
                            alt={item.title}
                            className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                                size="icon"
                                variant="ghost"
                                className="h-16 w-16 rounded-full bg-white/20 hover:bg-white/30 text-white backdrop-blur-sm"
                                onClick={() => setIsPlaying(true)}
                            >
                                <Play className="h-8 w-8 fill-current" />
                            </Button>
                        </div>
                        {/* <div className="absolute top-4 left-4 pointer-events-none">
                            <Badge variant="secondary" className="bg-yellow-100 text-yellow-900 border-none">
                                AI Overlay
                            </Badge>
                        </div> */}
                    </>
                ) : (
                    (() => {
                        if (isYouTube && youtubeId) {
                            return <div ref={containerRef} className="w-full h-full" />;
                        }

                        return (
                            <video
                                ref={videoRef}
                                src={videoSource}
                                className="w-full h-full object-contain bg-black"
                                autoPlay
                                playsInline
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
                        );
                    })()
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

                {/* Bottom overlay with timeline + creator info */}
                <div className="absolute inset-x-0 bottom-0 z-10 p-3 pt-4 bg-gradient-to-t from-black/70 via-black/40 to-transparent">
                    <div className="flex items-center gap-2 text-white mb-2">
                        <div className="flex flex-col leading-tight">
                            <span className="text-sm font-semibold">{creatorName}</span>
                            {creatorHandle && <span className="text-xs text-white/80">{creatorHandle}</span>}
                        </div>
                        {platformLabel && (
                            <span className="ml-auto text-[10px] px-2 py-1 rounded-full bg-white/15 uppercase tracking-wide">
                                {platformLabel}
                            </span>
                        )}
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
