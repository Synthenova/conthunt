"use client";

import Image from "next/image";
import { cn } from "@/lib/utils";

interface TrendingTickerProps {
    label: string;
    hashtags: string;
    trend: 'up1' | 'up2' | 'down1' | 'down2';
    onClick?: () => void;
}

export function TrendingTicker({ label, hashtags, trend, onClick }: TrendingTickerProps) {
    return (
        <div
            onClick={onClick}
            className={cn(
                "flex flex-col items-center justify-center relative min-w-[200px] transition-all duration-200",
                onClick ? "cursor-pointer hover:scale-105 active:scale-95" : ""
            )}
        >
            {/* Top Row: Icon + Label */}
            <div className="flex flex-row justify-center items-center gap-[5px] h-[24px] pr-[10px]">
                {/* Icon */}
                <div className={`w-[14px] h-[14px] relative flex items-center justify-center flex-none ${trend === 'down1' ? 'mt-[8px]' : ''}`}>
                    <img
                        src={`/${trend}.png`}
                        alt={trend}
                        className="w-[14px] h-[14px] object-contain"
                    />
                </div>

                {/* Label */}
                <span className="font-bold text-[16px] md:text-[18px] leading-tight text-center tracking-[-0.02em] text-white whitespace-nowrap">
                    {label}
                </span>
            </div>

            {/* Bottom Row: Hashtags */}
            <div className="flex items-center justify-center mt-1">
                <span className="font-medium text-[14px] md:text-[16px] leading-tight text-center tracking-[-0.02em] text-[#616161] whitespace-nowrap px-2">
                    {hashtags}
                </span>
            </div>
        </div>
    );
}
