import { GlassCard } from "@/components/ui/glass-card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Play, Heart, MessageCircle, Share2, ExternalLink, Eye, MoreHorizontal } from "lucide-react";
import { useState, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface MediaCardProps {
    item: any;
    platform: string;
}

export function MediaCard({ item, platform }: MediaCardProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isCaptionExpanded, setIsCaptionExpanded] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);

    // Platform-specific field mapping
    const title = item.title || item.caption || item.description || "No Title";
    const thumbnail = item.thumbnail_url || item.cover_url || item.image_url;
    // Prefer direct media URL or fall back to platform link
    const videoUrl = item.video_url || item.media_url;
    const link = item.url || item.link || item.web_url; // Keep link for external button if needed

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
    const youtubeId = isYouTube && link ?
        (link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&?/]+)/)?.[1] || item.id) :
        null;

    const handleHover = (isHovering: boolean) => {
        setIsPlaying(isHovering);
        if (videoRef.current && !isYouTube) {
            if (isHovering) {
                videoRef.current.play().catch(() => { }); // Autoplay policies might block
            } else {
                videoRef.current.pause();
                videoRef.current.currentTime = 0;
            }
        }
    };

    return (
        <GlassCard
            className="group relative overflow-hidden h-full flex flex-col border-0 bg-black"
            onMouseEnter={() => handleHover(true)}
            onMouseLeave={() => handleHover(false)}
            hoverEffect={false} // Disable default glass hover effect for custom handling
        >
            <div className="relative w-full h-full">
                <AspectRatio ratio={9 / 16} className="h-full">
                    {/* Thumbnail */}
                    <img
                        src={thumbnail}
                        alt={title}
                        className={cn(
                            "absolute inset-0 w-full h-full object-cover transition-opacity duration-300",
                            isPlaying && (videoUrl || youtubeId) ? 'opacity-0' : 'opacity-100'
                        )}
                        loading="lazy"
                        referrerPolicy="no-referrer"
                    />

                    {/* Video Player - Regular video for TikTok/Instagram */}
                    {videoUrl && !isYouTube && (
                        <video
                            ref={videoRef}
                            src={videoUrl}
                            className={cn(
                                "absolute inset-0 w-full h-full object-cover transition-opacity duration-300",
                                isPlaying ? 'opacity-100' : 'opacity-0'
                            )}
                            muted
                            loop
                            playsInline
                        />
                    )}

                    {/* YouTube Embedded Player */}
                    {isYouTube && youtubeId && isPlaying && (
                        <iframe
                            src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1&mute=1&controls=0&modestbranding=1&playsinline=1&disablekb=1`}
                            className="absolute inset-0 w-full h-full pointer-events-none"
                            allow="autoplay; encrypted-media"
                            allowFullScreen
                        />
                    )}

                    {/* Gradient Overlay (Bottom) */}
                    {/* Hides on play for clean view */}
                    {/* Gradient Overlay (Bottom) */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none" />

                    {/* Checkbox / Selection Placeholder (Always Visible) */}
                    {/* Assuming the parent handles the actual checkbox rendering via absolute positioning on top of this card, 
                        but if we need to reserve space or handle it here, we leave top-left clear. 
                        For now, just the Platform Badge which hides on hover. */}

                    {/* Platform Badge */}
                    <div className="absolute top-3 left-3">
                        <Badge className="bg-black/50 backdrop-blur-md border-white/10 hover:bg-black/70 uppercase text-[10px]">
                            {platform.replace('_', ' ')}
                        </Badge>
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

                        <div className="flex flex-col items-center gap-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full bg-white/10 hover:bg-white/20 text-white" asChild>
                                <a href={link} target="_blank" rel="noopener noreferrer">
                                    <ExternalLink className="h-4 w-4" />
                                </a>
                            </Button>
                        </div>
                    </div>


                    {/* Bottom Info Section (Creator + Caption) */}
                    <div className="absolute bottom-0 left-0 right-12 p-3 flex flex-col gap-2 z-10">
                        {/* Creator Profile */}
                        <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-zinc-800 border-2 border-white/20 overflow-hidden flex-shrink-0">
                                {creatorImage ? (
                                    <img
                                        src={creatorImage}
                                        alt={creatorName}
                                        className="h-full w-full object-cover"
                                        onError={(e) => {
                                            (e.target as HTMLImageElement).style.display = 'none';
                                        }}
                                    />
                                ) : (
                                    <div className="h-full w-full flex items-center justify-center text-white/50 font-bold text-xs bg-black">
                                        {creatorName.substring(0, 1).toUpperCase()}
                                    </div>
                                )}
                            </div>
                            <span className="text-sm font-semibold text-white drop-shadow-md truncate">
                                {creatorName}
                            </span>
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

                        {/* Views display (optional, can stay here or be removed) */}
                        <div className="flex items-center gap-1 text-[10px] text-white/70">
                            <Play className="h-3 w-3 fill-white/70" /> {formatNumber(views)} views
                        </div>
                    </div>

                </AspectRatio>
            </div>
        </GlassCard>
    );
}

function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
}
