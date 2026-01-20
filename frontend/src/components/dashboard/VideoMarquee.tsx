"use client"

import { useEffect, useState, useRef } from "react"
import { cn } from "@/lib/utils"
import { authFetch, BACKEND_URL } from "@/lib/api"
import { auth } from "@/lib/firebaseClient"
import { onAuthStateChanged } from "firebase/auth"

interface TrendingVideo {
    id: string;
    description: string;
    thumbnail: string | null;
    dynamicCover: string | null;
    videoUrl: string | null;
    duration: number;
    author: {
        id: string;
        uniqueId: string;
        nickname: string;
        avatar: string | null;
    };
    stats: {
        views: number;
        likes: number;
        comments: number;
        shares: number;
    };
}

const FALLBACK_VIDEOS: TrendingVideo[] = Array(8).fill(null).map((_, i) => ({
    id: `fallback-${i}`,
    description: "Trending viral video",
    thumbnail: "/placeholder.svg?height=400&width=225",
    dynamicCover: null,
    videoUrl: null,
    duration: 0,
    author: {
        id: "0",
        uniqueId: "creator",
        nickname: "Creator",
        avatar: null
    },
    stats: { views: 0, likes: 0, comments: 0, shares: 0 }
}));

export function VideoMarquee() {
    const [videos, setVideos] = useState<TrendingVideo[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isPaused, setIsPaused] = useState(false);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
    const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);

    // Fetch trending videos on mount with auth wait
    useEffect(() => {
        let unsubscribe: () => void;

        const fetchTrending = async () => {
            try {
                // Determine if we are authenticated to decide which endpoint or method to use
                // For now, we assume this component is used in dashboard where auth is required.
                // If auth is not ready, authFetch will fail. 
                // We wait for the first auth state emission.

                if (!auth.currentUser) {
                    // If not immediately logged in, wait for listener
                    return;
                }

                const response = await authFetch(`${BACKEND_URL}/v1/trending/tiktok?count=20`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.items && data.items.length > 0) {
                        setVideos(data.items);
                    } else {
                        setVideos(FALLBACK_VIDEOS);
                    }
                } else {
                    console.error("Trending API returned error:", response.status);
                    setVideos(FALLBACK_VIDEOS);
                }
            } catch (error) {
                console.error("Failed to fetch trending videos:", error);
                setVideos(FALLBACK_VIDEOS);
            } finally {
                setIsLoading(false);
            }
        };

        unsubscribe = onAuthStateChanged(auth, (user) => {
            if (user) {
                fetchTrending();
            } else {
                // If checking auth failed or user logged out, show fallbacks? 
                // Or maybe this component shouldn't render. 
                // For safety, show fallbacks.
                setVideos(FALLBACK_VIDEOS);
                setIsLoading(false);
            }
        });

        return () => unsubscribe();
    }, []);

    // Handle video hover
    const handleMouseEnter = (index: number) => {
        setIsPaused(true);
        setHoveredIndex(index);

        // Play the video
        const video = videoRefs.current[index];
        if (video) {
            video.play().catch(() => { });
        }
    };

    const handleMouseLeave = (index: number) => {
        setIsPaused(false);
        setHoveredIndex(null);

        // Pause the video
        const video = videoRefs.current[index];
        if (video) {
            video.pause();
            video.currentTime = 0;
        }
    };

    // Double the items for seamless loop
    const infiniteItems = [...videos, ...videos, ...videos];

    if (isLoading) {
        return (
            <div className="w-full relative overflow-hidden h-[400px] mt-auto flex items-center justify-center">
                <div className="text-zinc-500 text-sm">Loading trending videos...</div>
            </div>
        );
    }

    if (videos.length === 0) {
        return null;
    }

    return (
        <div className="w-full relative overflow-hidden h-[400px] mt-auto">

            {/* Gradient Masks */}
            <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-black to-transparent z-10 pointer-events-none" />
            <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-black to-transparent z-10 pointer-events-none" />

            {/* Marquee Track */}
            <div
                className={cn(
                    "flex gap-4 absolute left-0 top-0 h-full items-center",
                    !isPaused && "animate-marquee"
                )}
                style={{
                    animationPlayState: isPaused ? 'paused' : 'running',
                }}
            >
                {infiniteItems.map((video, i) => (
                    <div
                        key={`${video.id}-${i}`}
                        className="flex-shrink-0 w-[225px] h-[350px] relative group overflow-hidden rounded-xl bg-white/5 border border-white/10 cursor-pointer transition-all duration-300 hover:scale-105 hover:border-white/30"
                        onMouseEnter={() => handleMouseEnter(i)}
                        onMouseLeave={() => handleMouseLeave(i)}
                    >
                        {/* Bottom Gradient */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10 pointer-events-none" />

                        {/* Thumbnail (shown when not hovered) */}
                        {hoveredIndex !== i && (
                            <img
                                src={video.dynamicCover || video.thumbnail || '/placeholder.svg?height=400&width=225'}
                                alt={video.description || 'Trending video'}
                                className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-300"
                            />
                        )}

                        {/* Video (shown when hovered) */}
                        {hoveredIndex === i && video.videoUrl && (
                            <video
                                ref={(el) => { videoRefs.current[i] = el; }}
                                src={video.videoUrl}
                                className="w-full h-full object-cover"
                                muted
                                loop
                                playsInline
                            />
                        )}

                        {/* Video Info Overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-3 z-20">
                            {/* Author */}
                            <div className="flex items-center gap-2 mb-2">
                                {video.author.avatar && (
                                    <img
                                        src={video.author.avatar}
                                        alt={video.author.nickname}
                                        className="w-6 h-6 rounded-full object-cover"
                                    />
                                )}
                                <span className="text-white text-xs font-medium truncate">
                                    @{video.author.uniqueId || video.author.nickname}
                                </span>
                            </div>

                            {/* Description */}
                            <p className="text-white/80 text-xs line-clamp-2 leading-tight">
                                {video.description}
                            </p>

                            {/* Stats */}
                            <div className="flex items-center gap-3 mt-2 text-white/60 text-[10px]">
                                <span>{formatCount(video.stats.views)} views</span>
                                <span>{formatCount(video.stats.likes)} likes</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Bottom fade for page integration */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black to-transparent pointer-events-none z-20" />
        </div>
    )
}

function formatCount(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}
