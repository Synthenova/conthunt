"use client";

import { MediaCard } from "./MediaCard";
import { useSearchStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRef, memo } from "react";
import { trackSearchResultClicked } from "@/lib/telemetry/tracking";

import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";
import { ExternalLink } from "lucide-react";

interface SelectableMediaCardProps {
    item: any;
    platform: string;
    searchId?: string;
    totalResults?: number;
    onOpen?: (item: any, resumeTime: number) => void;
    // We use a ref to avoid re-rendering every card when new items are appended
    itemsByIdRef?: React.MutableRefObject<Record<string, any>>;
    onError?: (id: string) => void;
}

const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';

export const SelectableMediaCard = memo(function SelectableMediaCard({
    item,
    platform,
    searchId,
    totalResults,
    onOpen,
    itemsByIdRef,
    onError,
}: SelectableMediaCardProps) {
    const { selectedItems, toggleItemSelection } = useSearchStore();
    const isSelected = selectedItems.includes(item.id);
    const selectionMode = selectedItems.length > 0;
    const link = item.url || item.link || item.web_url;
    const platformLabel = formatPlatformLabel(platform);
    const lastHoverTimeRef = useRef(0);
    const hoverStartRef = useRef<number | null>(null);

    const PlatformIcon = getPlatformIcon(platform);
    const videoAssetId = item.assets?.find((a: any) => a.asset_type === 'video')?.id;

    const handleSelect = (e: React.MouseEvent) => {
        e.stopPropagation();
        e.preventDefault();
        toggleItemSelection(item.id);
    };

    const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
        e.stopPropagation();
        const itemsMap = itemsByIdRef?.current || {};
        const selected = (selectionMode && isSelected)
            ? selectedItems.map((id) => itemsMap[id]).filter(Boolean)
            : [];
        const items = selected.length ? selected : [item];

        const payloadItems = items.map((payloadItem: any) => {
            const videoAsset = payloadItem.assets?.find((a: any) => a.asset_type === "video");
            const thumb =
                payloadItem.thumbnail ||
                payloadItem.thumbnail_url ||
                payloadItem.cover_url ||
                payloadItem.image_url ||
                payloadItem.cover ||
                payloadItem.image ||
                payloadItem.poster ||
                payloadItem.preview_image ||
                payloadItem.cover_image ||
                null;
            return {
                id: payloadItem.id,
                title: payloadItem.title || payloadItem.caption || payloadItem.description || "Untitled video",
                platform: payloadItem.platform || platform,
                creator_handle: payloadItem.creator || payloadItem.creator_handle || payloadItem.creator_name,
                content_type: payloadItem.content_type,
                primary_text: payloadItem.primary_text || payloadItem.caption || payloadItem.description,
                media_asset_id: videoAsset?.id || payloadItem.media_asset_id || null,
                thumbnail_url: thumb,
            };
        });

        e.dataTransfer.setData(MEDIA_DRAG_TYPE, JSON.stringify({ items: payloadItems, source: "grid" }));
        e.dataTransfer.effectAllowed = "copy";

        // Build custom drag preview: stacked full-size thumbs (up to 5)
        const preview = document.createElement("div");
        preview.style.position = "absolute";
        preview.style.top = "-9999px";
        preview.style.left = "-9999px";
        const layerWidth = 320;
        const layerHeight = 200;
        const offset = 12;
        const maxThumbs = Math.min(payloadItems.length, 5);
        const stackWidth = layerWidth + offset * (maxThumbs - 1);
        const stackHeight = layerHeight + offset * (maxThumbs - 1);
        preview.style.width = `${stackWidth}px`;
        preview.style.height = `${stackHeight}px`;
        preview.style.pointerEvents = "none";
        preview.style.zIndex = "9999";

        for (let i = 0; i < maxThumbs; i++) {
            const thumb = payloadItems[i]?.thumbnail_url;
            const layer = document.createElement("div");
            layer.style.position = "absolute";
            layer.style.top = `${i * offset}px`;
            layer.style.left = `${i * offset}px`;
            layer.style.width = `${layerWidth}px`;
            layer.style.height = `${layerHeight}px`;
            layer.style.borderRadius = "16px";
            layer.style.boxShadow = "0 12px 32px rgba(0,0,0,0.35)";
            layer.style.background = thumb
                ? `center / cover no-repeat url("${thumb}")`
                : "linear-gradient(135deg, #1f1f1f, #2a2a2a)";
            layer.style.border = "1px solid rgba(255,255,255,0.15)";
            preview.appendChild(layer);
        }

        if (payloadItems.length > 5) {
            const badge = document.createElement("div");
            badge.textContent = `+${payloadItems.length - 5}`;
            badge.style.position = "absolute";
            badge.style.bottom = "12px";
            badge.style.right = "18px";
            badge.style.padding = "6px 14px";
            badge.style.borderRadius = "999px";
            badge.style.background = "rgba(0,0,0,0.8)";
            badge.style.color = "white";
            badge.style.fontSize = "13px";
            badge.style.fontWeight = "700";
            badge.style.border = "1px solid rgba(255,255,255,0.2)";
            preview.appendChild(badge);
        }

        document.body.appendChild(preview);
        e.dataTransfer.setDragImage(preview, 36, 36);
        setTimeout(() => {
            if (preview.parentNode) {
                preview.parentNode.removeChild(preview);
            }
        }, 0);
    };

    return (
        <div
            data-media-id={item.id}
            data-media-asset-id={videoAssetId}
            className="relative group/select"
            draggable
            onDragStart={handleDragStart}
            onClick={() => {
                trackSearchResultClicked(
                    String(searchId || item.search_id || "unknown_search"),
                    platform,
                    typeof item.rank === "number" ? item.rank : 0,
                    totalResults || 0
                );
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
            {/* Selection Checkbox */}
            <div className="absolute top-2 left-2 z-20">
                <button
                    onClick={handleSelect}
                    data-tutorial="video_checkbox"
                    className={cn(
                        "h-6 w-6 rounded-md border-2 flex items-center justify-center overflow-hidden transition-opacity duration-200",
                        isSelected
                            ? "bg-primary border-primary text-primary-foreground opacity-100"
                            : selectionMode
                                ? "bg-black/40 border-white/50 text-transparent hover:border-white hover:bg-black/60 opacity-100"
                                : "bg-black/40 border-white/50 text-transparent hover:border-white hover:bg-black/60 opacity-0 group-hover/select:opacity-100"
                    )}
                >
                    <Check className="h-4 w-4" strokeWidth={3} />
                </button>
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
                onError={() => onError?.(item.id)}
            />
        </div>
    );
});

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes("tiktok")) return FaTiktok;
    if (normalized.includes("instagram")) return FaInstagram;
    if (normalized.includes("youtube")) return FaYoutube;
    if (normalized.includes("pinterest")) return FaPinterest;
    return FaGlobe;
}

function formatPlatformLabel(platform: string): string {
    return platform.replace(/_/g, " ");
}
