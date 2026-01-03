import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Play } from "lucide-react";
import { useYouTubePlayer } from "@/lib/youtube";
import { XIcon } from "./XIcon";

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
    const videoRef = useRef<HTMLVideoElement>(null);
    const isYouTube = item?.platform === "youtube" || item?.platform === "youtube_search";
    const link = item?.url || item?.canonical_url;
    const youtubeId = useMemo(() => {
        if (!isYouTube || !link) return null;
        return link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&?/]+)/)?.[1] || item?.external_id || item?.id || null;
    }, [isYouTube, link, item?.external_id, item?.id]);

    const youtube = useYouTubePlayer({
        videoId: youtubeId,
        preload: true,
        muted: false,
        onReady: () => {
            if (resumeTime > 0) {
                youtube.seekTo(resumeTime);
            }
        },
    });

    useEffect(() => {
        if (isOpen) {
            setIsPlaying(true);
        } else {
            setIsPlaying(false);
        }
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
        };

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
        if (!isPlaying) return;
        if (!isYouTube) return;
        if (resumeTime <= 0) return;
        if (youtube.isReady) {
            youtube.seekTo(resumeTime);
        }
    }, [isPlaying, isYouTube, resumeTime, youtube]);

    return (
        <div className="relative w-full bg-[#0A0A0A] px-5 pt-5 pb-4 shrink-0">
            <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.06] to-transparent pointer-events-none" />
            <div
                className={cn(
                    "relative mx-auto aspect-[9/16] rounded-2xl overflow-hidden bg-black ring-1 ring-white/10 group",
                    "transition-[height,box-shadow] duration-300 ease-out",
                    isMediaCollapsed
                        ? "shadow-[0_12px_30px_rgba(0,0,0,0.45)]"
                        : "shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
                )}
                style={{ height: mediaHeight ? `${mediaHeight}px` : "60vh" }}
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
                        <div className="absolute top-4 left-4 pointer-events-none">
                            <Badge variant="secondary" className="bg-yellow-100 text-yellow-900 border-none">
                                AI Overlay
                            </Badge>
                        </div>
                    </>
                ) : (
                    (() => {
                        if (isYouTube && youtubeId) {
                            if (youtube.isReady) {
                                youtube.play();
                                youtube.unmute();
                                if (resumeTime > 0) {
                                    youtube.seekTo(resumeTime);
                                }
                            } else {
                                youtube.play();
                            }
                            return <div ref={youtube.containerRef} className="w-full h-full" />;
                        }

                        return (
                            <video
                                ref={videoRef}
                                src={item.video_url || item.url}
                                className="w-full h-full object-cover"
                                controls
                                autoPlay
                                playsInline
                            >
                                Your browser does not support the video tag.
                            </video>
                        );
                    })()
                )}
            </div>

            <div className="absolute top-4 right-5 z-10">
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 bg-black/50 text-white hover:bg-black/70 rounded-full"
                    onClick={onClose}
                >
                    <XIcon className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
