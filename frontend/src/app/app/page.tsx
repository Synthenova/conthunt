"use client";

import { useState } from "react";
import { useTutorialAutoStart } from "@/hooks/useTutorialAutoStart";
import { HomeSearchBox } from "@/components/dashboard/HomeSearchBox";
import { TrendingTicker } from "@/components/dashboard/TrendingTicker";
import { VideoMarquee } from "@/components/dashboard/VideoMarquee";

const TICKERS = [
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
] as const;

export default function HomePage() {
    const [searchQuery, setSearchQuery] = useState("");

    // Auto-start home tutorial on first visit
    useTutorialAutoStart({ flowId: "home_tour" });

    const handleTickerClick = (label: string, hashtags: string) => {
        setSearchQuery(`Find viral videos for ${label} (${hashtags})`);
    };

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
                <HomeSearchBox value={searchQuery} onChange={setSearchQuery} />

                {/* Trending Tickers Stack */}
                <div className="mt-[calc(var(--spacing)*34)] w-full max-w-[96rem] flex flex-wrap justify-center gap-x-6 gap-y-8 max-h-[160px] overflow-hidden content-start">
                    {TICKERS.map((ticker, index) => (
                        <TrendingTicker
                            key={index}
                            label={ticker.label}
                            hashtags={ticker.hashtags}
                            trend={ticker.trend}
                            onClick={() => handleTickerClick(ticker.label, ticker.hashtags)}
                        />
                    ))}
                </div>

            </div>

            {/* Footer / Marquee Area */}
            <div className="w-full max-w-7xl mt-auto relative z-0">
                <VideoMarquee />
            </div>
        </div>
    );
}
