"use client";

import { MediaCard } from "./MediaCard";
import { useSearchStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRef } from "react";

interface SelectableMediaCardProps {
    item: any;
    platform: string;
    onOpen?: (item: any, resumeTime: number) => void;
    itemsById?: Record<string, any>;
}

const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';

export function SelectableMediaCard({ item, platform, onOpen, itemsById = {} }: SelectableMediaCardProps) {
    const { selectedItems, toggleItemSelection } = useSearchStore();
    const isSelected = selectedItems.includes(item.id);
    const selectionMode = selectedItems.length > 0;
    const link = item.url || item.link || item.web_url;
    const platformLabel = formatPlatformLabel(platform);
    const lastHoverTimeRef = useRef(0);
    const hoverStartRef = useRef<number | null>(null);

    const handleSelect = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        toggleItemSelection(item.id);
    };

    const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
        e.stopPropagation();
        const selected = (selectionMode && isSelected)
            ? selectedItems.map((id) => itemsById[id]).filter(Boolean)
            : [];
        const items = selected.length ? selected : [item];

        const payloadItems = items.map((payloadItem: any) => {
            const videoAsset = payloadItem.assets?.find((a: any) => a.asset_type === "video");
            return {
                id: payloadItem.id,
                title: payloadItem.title || payloadItem.caption || payloadItem.description || "Untitled video",
                platform: payloadItem.platform || platform,
                creator_handle: payloadItem.creator || payloadItem.creator_handle || payloadItem.creator_name,
                content_type: payloadItem.content_type,
                primary_text: payloadItem.primary_text || payloadItem.caption || payloadItem.description,
                media_asset_id: videoAsset?.id || payloadItem.media_asset_id || null,
            };
        });

        e.dataTransfer.setData(MEDIA_DRAG_TYPE, JSON.stringify({ items: payloadItems, source: "grid" }));
        e.dataTransfer.effectAllowed = "copy";
    };

    return (
        <div
            className="relative group/select"
            draggable
            onDragStart={handleDragStart}
            onClick={() => {
                if (!onOpen) return;
                const hoverStart = hoverStartRef.current;
                let resumeTime = 0;
                if (hoverStart !== null) {
                    const hoverDuration = (performance.now() - hoverStart) / 1000;
                    if (hoverDuration >= 0.6) {
                        resumeTime = Math.max(0, lastHoverTimeRef.current - 0.5);
                    }
                }
                onOpen(item, resumeTime);
            }}
        >
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
            <MediaCard
                item={item}
                platform={platform}
                showBadge={false}
                onHoverTimeChange={(seconds) => {
                    lastHoverTimeRef.current = seconds;
                }}
                onHoverStateChange={(isHovering) => {
                    hoverStartRef.current = isHovering ? performance.now() : null;
                }}
            />
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
