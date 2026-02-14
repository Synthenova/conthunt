"use client";

import { useEffect, useState } from "react";
import { useTutorialAutoStart } from "@/hooks/useTutorialAutoStart";
import { HomeSearchBox } from "@/components/dashboard/HomeSearchBox";
import { TrendingTicker, TrendingTickerSkeleton } from "@/components/dashboard/TrendingTicker";
import { VideoMarquee } from "@/components/dashboard/VideoMarquee";
import { authFetch, BACKEND_URL } from "@/lib/api";
import { auth } from "@/lib/firebaseClient";
import { onAuthStateChanged } from "firebase/auth";

interface TrendingNiche {
    trend: 'up1' | 'up2' | 'down1' | 'down2';
    keyword: string;
    hashtags: string[];
}

const FALLBACK_TICKERS: { label: string; hashtags: string; trend: 'up1' | 'up2' | 'down1' | 'down2' }[] = [
    { label: "Key and Peele", hashtags: "#keysucks #keyandpeele #peelehumour", trend: "down1" },
    { label: "Nylon Canister", hashtags: "#cannister", trend: "up2" },
    { label: "Monster Energy", hashtags: "#gymtok #gymedit #aesthetics", trend: "up2" },
    { label: "TikTok Dance", hashtags: "#lovedance #fyp", trend: "down2" },
    { label: "Christmas Decor", hashtags: "#gymtok #aesthetics", trend: "down2" },
    { label: "Dark Gym Edit", hashtags: "#gymtok #gymedit #aesthetics", trend: "up2" },
    { label: "Wuthering Waves", hashtags: "#TGA #gacha #aemeath", trend: "up2" },
    { label: "Day in the Life", hashtags: "#gymtok #gymedit #aesthetics", trend: "down2" },
    { label: "Horrible Humor", hashtags: "#gymtok #gymedit #aesthetics", trend: "up2" },
    { label: "Claude Code", hashtags: "#happy #aicoding", trend: "down2" },
    { label: "Founder Led Content", hashtags: "#buildinpublic #foudnerfails", trend: "up2" },
    { label: "Power Puff Gags", hashtags: "#humour #laugh", trend: "down2" },
];

export default function HomePage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [trendingNiches, setTrendingNiches] = useState<TrendingNiche[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [deepResearchEnabled, setDeepResearchEnabled] = useState(false);

    // Auto-start home tutorial on first visit
    useTutorialAutoStart({ flowId: "home_tour" });

    useEffect(() => {
        let unsubscribe: () => void;

        const fetchNiches = async () => {
            try {
                if (!auth.currentUser) return;

                const response = await authFetch(`${BACKEND_URL}/v1/trending/niches`);
                if (response.ok) {
                    const data = await response.json();
                    if (Array.isArray(data) && data.length > 0) {
                        setTrendingNiches(data);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch trending niches:", error);
            } finally {
                setIsLoading(false);
            }
        };

        unsubscribe = onAuthStateChanged(auth, (user) => {
            if (user) {
                fetchNiches();
            } else {
                setIsLoading(false);
            }
        });

        return () => unsubscribe();
    }, []);

    const handleTickerClick = (label: string, hashtags: string) => {
        setSearchQuery(`Find viral videos for ${label} (${hashtags})`);
    };

    // Use fetched niches or fallback
    const displayItems = trendingNiches.length > 0
        ? trendingNiches.map(n => ({
            label: n.keyword,
            hashtags: n.hashtags.join(" "),
            trend: n.trend
        }))
        : FALLBACK_TICKERS;

    return (
        <div className="min-h-screen bg-black relative flex flex-col items-center overflow-hidden">

            {/* Top Navigation / Brand (Placeholder) */}
            <div className="absolute top-0 left-0 p-6 z-30">
                {/* Add logo or sidebar trigger here if needed */}
            </div>

            {/* Main Content Area */}
            <div className="flex-1 w-full max-w-7xl relative z-10 flex flex-col items-center pt-[15vh]">

                {/* Header Text */}
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-8 tracking-tight text-center">
                    What do we search today?
                </h1>

                {/* Search Box */}
                <HomeSearchBox
                    value={searchQuery}
                    onChange={setSearchQuery}
                    deepResearchEnabled={deepResearchEnabled}
                    onDeepResearchChange={setDeepResearchEnabled}
                />

                {/* Trending Tickers Stack */}
                <div className="mt-[calc(var(--spacing)*34)] w-full max-w-[96rem] flex flex-wrap justify-center gap-x-6 gap-y-8 max-h-[160px] overflow-hidden content-start">
                    {isLoading ? (
                        Array.from({ length: 12 }).map((_, index) => (
                            <TrendingTickerSkeleton key={index} />
                        ))
                    ) : (
                        displayItems.map((ticker, index) => (
                            <TrendingTicker
                                key={index}
                                label={ticker.label}
                                hashtags={ticker.hashtags}
                                trend={ticker.trend}
                                onClick={() => handleTickerClick(ticker.label, ticker.hashtags)}
                            />
                        ))
                    )}
                </div>

            </div>

            {/* Footer / Marquee Area */}
            <div className="w-full max-w-7xl mt-auto relative z-0">
                <VideoMarquee />
            </div>
        </div>
    );
}
