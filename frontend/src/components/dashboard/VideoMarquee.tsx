"use client"

import { useEffect, useState, useRef } from "react"
import { cn } from "@/lib/utils"
import { authFetch, BACKEND_URL } from "@/lib/api"
import { auth } from "@/lib/firebaseClient"
import { onAuthStateChanged } from "firebase/auth"
import { MediaCard } from "@/components/search/MediaCard"

interface TrendingVideo {
    id: string;
    title: string;
    thumbnail_url: string | null;
    video_url: string | null;
    duration: number;
    platform: string;
    author: {
        id: string;
        uniqueId: string;
        nickname: string;
        avatar: string | null;
    };
    creator_name: string;
    creator_image: string | null;
    view_count: number;
    like_count: number;
    comment_count: number;
    share_count: number;
}

const FALLBACK_VIDEOS: TrendingVideo[] = Array(8).fill(null).map((_, i) => ({
    id: `fallback-${i}`,
    title: "Trending viral video",
    thumbnail_url: "/placeholder.svg?height=400&width=225",
    video_url: null,
    duration: 0,
    platform: "youtube",
    author: {
        id: "0",
        uniqueId: "creator",
        nickname: "Creator",
        avatar: null
    },
    creator_name: "Creator",
    creator_image: null,
    view_count: 0,
    like_count: 0,
    comment_count: 0,
    share_count: 0,
}));

export function VideoMarquee() {
    const [videos, setVideos] = useState<TrendingVideo[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isPaused, setIsPaused] = useState(false);

    // Fetch trending videos on mount with auth wait
    useEffect(() => {
        let unsubscribe: () => void;

        const fetchTrending = async () => {
            try {
                if (!auth.currentUser) return;

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
                setVideos(FALLBACK_VIDEOS);
                setIsLoading(false);
            }
        });

        return () => unsubscribe();
    }, []);

    // Triple the items for seamless loop
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
        <div className="w-full relative overflow-hidden h-[400px] mt-auto group/marquee">
            {/* Gradient Masks */}
            <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-black to-transparent z-10 pointer-events-none" />
            <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-black to-transparent z-10 pointer-events-none" />

            {/* Marquee Track */}
            <div
                className={cn(
                    "flex gap-4 absolute left-0 top-0 h-full items-center",
                    // Use CSS animation but pause on hover over the container
                    // Note: MediaCard interaction might conflict if we pause the whole marquee,
                    // but usually you want to pause marquee to watch a video.
                    "animate-marquee",
                    isPaused && "paused" // Add class support or inline style
                )}
                style={{
                    animationPlayState: isPaused ? 'paused' : 'running',
                }}
                onMouseEnter={() => setIsPaused(true)}
                onMouseLeave={() => setIsPaused(false)}
            >
                {infiniteItems.map((video, i) => (
                    <div
                        key={`${video.id}-${i}`}
                        className="flex-shrink-0 w-[225px] h-[350px]"
                    >
                        <MediaCard
                            item={video}
                            platform={video.platform || "tiktok"}
                            showBadge={false}
                        // readOnly={true} // Removed to enable hover effects and mute button
                        />
                    </div>
                ))}
            </div>

            {/* Bottom fade for page integration */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black to-transparent pointer-events-none z-20" />
        </div>
    )
}
