import { GlassCard } from "@/components/ui/glass-card";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Play, Heart, MessageCircle, Share2, ExternalLink } from "lucide-react";
import { useState, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface MediaCardProps {
    item: any;
    platform: string;
}

export function MediaCard({ item, platform }: MediaCardProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);

    // Platform-specific field mapping
    const title = item.title || item.caption || item.description || "No Title";
    const thumbnail = item.thumbnail_url || item.cover_url || item.image_url;
    // Prefer direct media URL or fall back to platform link
    const videoUrl = item.video_url || item.media_url;
    const link = item.url || item.link || item.web_url;

    // Stats
    const views = item.view_count || item.play_count || 0;
    const likes = item.like_count || item.digg_count || 0;
    const comments = item.comment_count || 0;

    const handleHover = (isHovering: boolean) => {
        setIsPlaying(isHovering);
        if (videoRef.current) {
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
            className="group relative overflow-hidden h-full flex flex-col"
            onMouseEnter={() => handleHover(true)}
            onMouseLeave={() => handleHover(false)}
            hoverEffect={true}
        >
            {/* Visual Header */}
            <div className="relative w-full">
                <AspectRatio ratio={9 / 16}>
                    {/* Thumbnail */}
                    <img
                        src={thumbnail}
                        alt={title}
                        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${isPlaying && videoUrl ? 'opacity-0' : 'opacity-100'}`}
                        loading="lazy"
                        referrerPolicy="no-referrer"
                    />

                    {/* Video Player (Hidden until hover) */}
                    {videoUrl && (
                        <video
                            ref={videoRef}
                            src={videoUrl}
                            className={`absolute inset-0 w-full h-full object-cover ${isPlaying ? 'opacity-100' : 'opacity-0'}`}
                            muted
                            loop
                            playsInline
                        />
                    )}

                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent pointer-events-none" />

                    {/* Platform Badge */}
                    <Badge className="absolute top-3 left-3 bg-black/50 backdrop-blur-md border-white/10 hover:bg-black/70 uppercase text-[10px]">
                        {platform.replace('_', ' ')}
                    </Badge>

                    {/* Play Icon Hint */}
                    {!isPlaying && (
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="h-12 w-12 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center">
                                <Play className="h-5 w-5 fill-white text-white ml-1" />
                            </div>
                        </div>
                    )}

                    {/* Stats Overlay */}
                    <div className="absolute bottom-3 left-3 right-3 flex justify-between text-xs text-white/90">
                        <div className="flex gap-3">
                            <span className="flex items-center gap-1"><Play className="h-3 w-3" /> {formatNumber(views)}</span>
                            <span className="flex items-center gap-1"><Heart className="h-3 w-3" /> {formatNumber(likes)}</span>
                        </div>
                    </div>
                </AspectRatio>
            </div>

            {/* Content Body */}
            <div className="p-4 flex flex-col flex-1 gap-2">
                <h3 className="font-semibold text-sm line-clamp-2 leading-tight text-white group-hover:text-primary transition-colors">
                    {title}
                </h3>

                <div className="mt-auto pt-2 flex items-center justify-between border-t border-white/5">
                    <p className="text-[10px] text-muted-foreground font-mono truncate max-w-[120px]">
                        {item.id || "ID: --"}
                    </p>
                    <Button
                        size="icon-sm"
                        variant="ghost"
                        className="h-7 w-7 text-white/50 hover:text-white hover:bg-white/10"
                        asChild
                    >
                        <a href={link} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                    </Button>
                </div>
            </div>
        </GlassCard>
    );
}

function formatNumber(num: number): string {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num.toString();
}
