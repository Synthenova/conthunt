"use client";

import { AsyncImage } from "@/components/ui/async-image";
import { GlassCard } from "@/components/ui/glass-card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Play, Heart, MessageCircle, Share2, Volume2, VolumeX } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSearchStore } from "@/lib/store";
import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";
import { useYouTubePlayer } from "@/lib/youtube";

interface MediaCardProps {
    item: any;
    platform: string;
    showBadge?: boolean;
    onHoverTimeChange?: (seconds: number) => void;
    onHoverStateChange?: (isHovering: boolean) => void;
}

export function MediaCard({
    item,
    platform,
    showBadge = true,
    onHoverTimeChange,
    onHoverStateChange,
}: MediaCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isCaptionExpanded, setIsCaptionExpanded] = useState(false);
    const { mediaMuted, setMediaMuted } = useSearchStore();
    const videoRef = useRef<HTMLVideoElement>(null);
    const timelineRef = useRef<HTMLDivElement>(null);
    const [isScrubbing, setIsScrubbing] = useState(false);
    const [durationSeconds, setDurationSeconds] = useState<number | null>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const youtubeTimeIntervalRef = useRef<number | null>(null);

    useEffect(() => {
        const el = cardRef.current;
        if (!el) return;

        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    setIsVisible(entry.isIntersecting);
                }
            },
            {
                rootMargin: "200px",
                threshold: 0,
            }
        );

        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    // Platform-specific field mapping
    const title = item.title || item.caption || item.description || "No Title";
    const thumbnail = item.thumbnail_url || item.cover_url || item.image_url;
    const videoUrl = item.video_url || item.media_url;
    const link = item.url || item.link || item.web_url;
    const platformLabel = formatPlatformLabel(platform);

    // Stats
    const views = item.view_count || item.play_count || 0;
    const likes = item.like_count || item.digg_count || 0;
    const comments = item.comment_count || 0;
    const shares = item.share_count || 0;

    // Creator
    const creatorName = item.creator_name || item.creator || "Unknown";
    const creatorImage = item.creator_image;

    // YouTube detection - extract video ID from URL
    const isYouTube = platform === 'youtube' || platform === 'youtube_search';
    const youtubeId = useMemo(() => {
        if (!isYouTube || !link) return null;
        return link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&?/]+)/)?.[1] || item.id || null;
    }, [isYouTube, link, item.id]);

    // Use YouTube Player hook - lazy load (no preload) for performance
    const shouldMuteYoutube = mediaMuted || !isPlaying;

    const youtube = useYouTubePlayer({
        videoId: youtubeId,
        preload: true,
        muted: shouldMuteYoutube,
        onReady: () => {
            // Get duration from player
            const dur = youtube.getDuration();
            if (dur && dur > 0) {
                setDurationSeconds(dur);
            }
        },
    });

    const resolvedDurationSeconds = useMemo(() => {
        const raw = item?.duration || item?.duration_seconds || item?.duration_ms || item?.length_seconds || item?.length || item?.video_length;
        if (typeof raw === "number") return raw > 1000 ? raw / 1000 : raw;
        if (typeof raw === "string") {
            const parsed = parseFloat(raw);
            if (!Number.isNaN(parsed)) return parsed;
        }
        return null;
    }, [item]);

    useEffect(() => {
        if (resolvedDurationSeconds) {
            setDurationSeconds(resolvedDurationSeconds);
        }
    }, [resolvedDurationSeconds]);

    // Start/stop YouTube time tracking
    const startYouTubeTimeTracking = useCallback(() => {
        if (youtubeTimeIntervalRef.current) return;
        youtubeTimeIntervalRef.current = window.setInterval(() => {
            if (!youtube.isReady) return;
            const time = youtube.getCurrentTime();
            const dur = youtube.getDuration();
            if (dur && dur > 0 && !durationSeconds) {
                setDurationSeconds(dur);
            }
            setCurrentTime(time);
            onHoverTimeChange?.(time);
        }, 100);
    }, [youtube, durationSeconds, onHoverTimeChange]);

    const stopYouTubeTimeTracking = useCallback(() => {
        if (youtubeTimeIntervalRef.current) {
            window.clearInterval(youtubeTimeIntervalRef.current);
            youtubeTimeIntervalRef.current = null;
        }
    }, []);

    useEffect(() => {
        return () => {
            stopYouTubeTimeTracking();
        };
    }, [stopYouTubeTimeTracking]);

    const handleHover = useCallback((isHovering: boolean) => {
        setIsPlaying(isHovering);
        onHoverStateChange?.(isHovering);

        // Handle non-YouTube videos
        if (videoRef.current && !isYouTube) {
            if (isHovering) {
                onHoverTimeChange?.(0);
                videoRef.current.play().catch(() => { });
            } else {
                videoRef.current.pause();
                videoRef.current.currentTime = 0;
                setCurrentTime(0);
            }
        }

        // Handle YouTube videos
        if (isYouTube && youtubeId) {
            if (isHovering) {
                youtube.play();
                startYouTubeTimeTracking();
            } else {
                stopYouTubeTimeTracking();
                youtube.pause();
                youtube.seekTo(0);
                setCurrentTime(0);
            }
        }
    }, [isYouTube, youtubeId, youtube, onHoverStateChange, onHoverTimeChange, startYouTubeTimeTracking, stopYouTubeTimeTracking]);

    useEffect(() => {
        if (!isVisible && isPlaying) {
            handleHover(false);
        }
    }, [isVisible, isPlaying, handleHover]);

    useEffect(() => {
        const handleVisibility = () => {
            if (document.hidden) {
                handleHover(false);
            }
        };
        const handleBlur = () => {
            handleHover(false);
        };

        document.addEventListener("visibilitychange", handleVisibility);
        window.addEventListener("blur", handleBlur);
        return () => {
            document.removeEventListener("visibilitychange", handleVisibility);
            window.removeEventListener("blur", handleBlur);
        };
    }, [handleHover]);

    // Sync mute for native video
    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.muted = mediaMuted;
        }
    }, [mediaMuted]);

    // Sync mute for YouTube (handled by hook automatically via muted prop)

    const handleScrub = useCallback((clientX: number) => {
        if (!durationSeconds || !timelineRef.current) return;
        const rect = timelineRef.current.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
        const newTime = ratio * durationSeconds;

        setCurrentTime(newTime);
        onHoverTimeChange?.(newTime);

        if (videoRef.current && !isYouTube) {
            videoRef.current.currentTime = newTime;
            videoRef.current.play().catch(() => { });
            return;
        }

        if (isYouTube && youtube.isReady) {
            youtube.seekTo(newTime);
            youtube.play();
        }
    }, [durationSeconds, isYouTube, youtube, onHoverTimeChange]);

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
    }, [isScrubbing, handleScrub]);

    const handleMouseEnter = useCallback(() => {
        handleHover(true);
    }, [handleHover]);

    const handleMouseLeave = useCallback((e: React.MouseEvent) => {
        // Check if we're actually leaving the card vs entering a child element
        // relatedTarget is the element we're entering - if it's inside the card, ignore
        const relatedTarget = e.relatedTarget as Node | null;
        if (relatedTarget && cardRef.current?.contains(relatedTarget)) {
            return;
        }
        handleHover(false);
    }, [handleHover]);

    return (
        <div
            ref={cardRef}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <GlassCard
                className="group relative overflow-hidden h-full flex flex-col border-0 bg-surface/80 shadow-xl shadow-black/20"
                hoverEffect={false}
            >
                <div className="relative w-full h-full">
                    <AspectRatio ratio={9 / 16} className="h-full">
                        {/* Thumbnail */}
                        <AsyncImage
                            src={thumbnail}
                            alt={title}
                            className={cn(
                                "absolute inset-0 w-full h-full object-cover transition-opacity duration-300",
                                // For YouTube: only hide thumbnail when player is primed (ready to show)
                                // For other videos: hide when playing
                                isPlaying && (youtubeId ? youtube.isPrimed : videoUrl) ? 'opacity-0' : 'opacity-100'
                            )}
                            referrerPolicy="no-referrer"
                        />

                        {/* Video Player - Regular video for TikTok/Instagram */}
                        {videoUrl && !isYouTube && isVisible && (
                            <video
                                ref={videoRef}
                                src={videoUrl}
                                className={cn(
                                    "absolute inset-0 w-full h-full object-cover transition-opacity duration-300",
                                    isPlaying ? 'opacity-100' : 'opacity-0'
                                )}
                                muted={mediaMuted}
                                loop
                                playsInline
                                preload="none"
                                onLoadedMetadata={() => {
                                    if (videoRef.current) {
                                        const dur = videoRef.current.duration;
                                        if (dur && !Number.isNaN(dur)) {
                                            setDurationSeconds(dur);
                                        }
                                    }
                                }}
                                onTimeUpdate={() => {
                                    if (videoRef.current) {
                                        setCurrentTime(videoRef.current.currentTime);
                                        onHoverTimeChange?.(videoRef.current.currentTime);
                                    }
                                }}
                            />
                        )}

                        {/* YouTube Player Container - Primes on mount */}
                        {isYouTube && youtubeId && (
                            <div
                                ref={youtube.containerRef}
                                className={cn(
                                    "absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-200",
                                    isPlaying && youtube.isPrimed ? "opacity-100" : "opacity-0"
                                )}
                            />
                        )}

                        {/* YouTube Loading Spinner - Shows while priming */}
                        {isYouTube && youtubeId && isPlaying && !youtube.isPrimed && (
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
                                <div className="h-10 w-10 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                            </div>
                        )}

                        {/* Gradient Overlay (Bottom) */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none" />

                        {/* Mute Toggle */}
                        <div className="absolute top-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none group-hover:pointer-events-auto">
                            <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-full bg-black/40 hover:bg-black/60 text-white"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setMediaMuted(!mediaMuted);
                                }}
                            >
                                {mediaMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
                            </Button>
                        </div>

                        {/* Right Side Stats Bar */}
                        <div className="absolute bottom-4 right-2 flex flex-col gap-4 items-center z-10">
                            {likes > 0 && (
                                <div className="flex flex-col items-center gap-1">
                                    <Heart className="h-6 w-6 text-white drop-shadow-md" />
                                    <span className="text-[10px] font-medium text-white drop-shadow-md">{formatNumber(likes)}</span>
                                </div>
                            )}

                            {comments > 0 && (
                                <div className="flex flex-col items-center gap-1">
                                    <MessageCircle className="h-6 w-6 text-white drop-shadow-md" />
                                    <span className="text-[10px] font-medium text-white drop-shadow-md">{formatNumber(comments)}</span>
                                </div>
                            )}

                            {shares > 0 && (
                                <div className="flex flex-col items-center gap-1">
                                    <Share2 className="h-6 w-6 text-white drop-shadow-md" />
                                    <span className="text-[10px] font-medium text-white drop-shadow-md">{formatNumber(shares)}</span>
                                </div>
                            )}
                        </div>

                        {/* Bottom Info Section (Creator + Caption) */}
                        <div className="absolute bottom-0 left-0 right-12 p-3 flex flex-col gap-2 z-10">
                            {/* Creator Profile */}
                            <div className="flex items-center gap-2">
                                <div className="h-8 w-8 rounded-full bg-zinc-800 border-2 border-white/20 overflow-hidden flex-shrink-0">
                                    {creatorImage ? (
                                        <AsyncImage
                                            src={creatorImage}
                                            alt={creatorName}
                                            className="h-full w-full object-cover"
                                        />
                                    ) : (
                                        <div className="h-full w-full flex items-center justify-center text-white/50 font-bold text-xs bg-black">
                                            {creatorName.substring(0, 1).toUpperCase()}
                                        </div>
                                    )}
                                </div>
                                <span className="text-sm font-semibold text-white drop-shadow-md truncate max-w-[120px]">
                                    {creatorName}
                                </span>
                                {/* Platform Name Link */}
                                {link && (
                                    <>
                                        <span className="text-white/50 text-[10px]">•</span>
                                        <a
                                            href={link}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-xs text-white/90 hover:text-white underline drop-shadow-md truncate max-w-[100px] uppercase font-medium"
                                            onClick={(e) => e.stopPropagation()}
                                        >
                                            {platformLabel}
                                        </a>
                                    </>
                                )}
                            </div>

                            {/* Caption */}
                            <div
                                className="text-xs text-white/90 drop-shadow-sm cursor-pointer"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsCaptionExpanded(!isCaptionExpanded);
                                }}
                            >
                                <p className={cn(
                                    "leading-relaxed transition-all duration-300",
                                    isCaptionExpanded ? "" : "line-clamp-1"
                                )}>
                                    {title}
                                </p>
                                {!isCaptionExpanded && title && title.length > 50 && (
                                    <span className="text-[10px] text-white/70">more</span>
                                )}
                            </div>

                            {/* Views display */}
                            <div className="flex items-center gap-1 text-[10px] text-white/70">
                                <Play className="h-3 w-3 fill-white/70" /> {formatNumber(views)} views
                            </div>
                        </div>

                        {/* Timeline (hover play only) */}
                        {isPlaying && durationSeconds && (
                            <div
                                ref={timelineRef}
                                className="absolute bottom-0 left-0 right-0 h-1.5 bg-white/25 overflow-hidden z-20 cursor-pointer"
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

                    </AspectRatio>
                </div>
            </GlassCard>
        </div>
    );
}

function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
}

function formatPlatformLabel(platform: string): string {
    return platform.replace(/_/g, " ");
}

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes("tiktok")) return FaTiktok;
    if (normalized.includes("instagram")) return FaInstagram;
    if (normalized.includes("youtube")) return FaYoutube;
    if (normalized.includes("pinterest")) return FaPinterest;
    return FaGlobe;
}
