"use client";

import { MediaCard } from "./MediaCard";
import { useSearchStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface SelectableMediaCardProps {
    item: any;
    platform: string;
}

export function SelectableMediaCard({ item, platform }: SelectableMediaCardProps) {
    const { selectedItems, toggleItemSelection } = useSearchStore();
    const isSelected = selectedItems.includes(item.id);
    const selectionMode = selectedItems.length > 0;
    const link = item.url || item.link || item.web_url;
    const platformLabel = formatPlatformLabel(platform);

    const handleSelect = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        toggleItemSelection(item.id);
    };

    return (
        <div className="relative group/select">
            {/* Selection + Platform */}
            <div className="absolute top-2 left-2 z-20 flex items-center gap-2">
                <button
                    onClick={handleSelect}
                    className={cn(
                        "h-6 w-6 rounded-md border-2 flex items-center justify-center overflow-hidden transition-[opacity,transform,width] duration-200",
                        isSelected
                            ? "bg-primary border-primary text-white scale-100 w-6 opacity-100"
                            : selectionMode
                                ? "bg-black/40 border-white/50 text-transparent hover:border-white hover:bg-black/60 scale-100 w-6 opacity-100"
                                : "bg-black/40 border-white/50 text-transparent hover:border-white hover:bg-black/60 scale-90 w-0 opacity-0 group-hover/select:w-6 group-hover/select:opacity-100 group-hover/select:scale-100"
                    )}
                >
                    <Check className="h-4 w-4" strokeWidth={3} />
                </button>
                {link ? (
                    <a
                        href={link}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`${platformLabel} link`}
                        title={platformLabel}
                    >
                        <Badge className="relative bg-black/50 backdrop-blur-md border-white/40 hover:bg-black/70 uppercase text-[10px] flex items-center gap-1 pr-2 transition-[padding] duration-200 group-hover/select:pr-5">
                            <i className={cn("bi", getPlatformIconClass(platform), "text-[14px]")} aria-hidden="true" />
                            <i className="bi bi-box-arrow-up-right text-[13px] opacity-0 transition-opacity duration-200 absolute right-1 group-hover/select:opacity-100" aria-hidden="true" />
                        </Badge>
                    </a>
                ) : (
                    <Badge className="bg-black/50 backdrop-blur-md border-white/40 hover:bg-black/70 uppercase text-[10px] flex items-center gap-1">
                        <i className={cn("bi", getPlatformIconClass(platform), "text-[14px]")} aria-hidden="true" />
                    </Badge>
                )}
            </div>

            {/* Selection Glow Effect */}
            {isSelected && (
                <div className="absolute inset-0 rounded-xl ring-2 ring-primary ring-offset-2 ring-offset-background z-10 pointer-events-none" />
            )}

            {/* Original Media Card */}
            <MediaCard item={item} platform={platform} showBadge={false} />
        </div>
    );
}

function getPlatformIconClass(platform: string): string {
    const normalized = platform.toLowerCase();
    if (normalized.includes("tiktok")) return "bi-tiktok";
    if (normalized.includes("instagram")) return "bi-instagram";
    if (normalized.includes("youtube")) return "bi-youtube";
    if (normalized.includes("pinterest")) return "bi-pinterest";
    return "bi-globe";
}

function formatPlatformLabel(platform: string): string {
    return platform.replace(/_/g, " ");
}
