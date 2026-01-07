
import { useRef, useCallback, useState } from "react";
import { Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatTabsProps {
    displaySearches: Array<{ id: string; label: string; sort_order?: number | null }>;
    activeSearchId: string | null;
    setActiveSearchId: (id: string | null) => void;
    handleTabDelete: (id: string) => void;
    streamingSearchIds: Record<string, boolean>;
}

export function ChatTabs({
    displaySearches,
    activeSearchId,
    setActiveSearchId,
    handleTabDelete,
    streamingSearchIds
}: ChatTabsProps) {
    const tabsScrollRef = useRef<HTMLDivElement>(null);
    const [hoveredTabId, setHoveredTabId] = useState<string | null>(null);

    // Drag-to-scroll logic
    const isDraggingTabs = useRef(false);
    const wasDragged = useRef(false);
    const dragStartX = useRef(0);
    const scrollStartX = useRef(0);

    const handleTabsMouseDown = useCallback((e: React.MouseEvent) => {
        const el = tabsScrollRef.current;
        if (!el) return;
        isDraggingTabs.current = true;
        wasDragged.current = false;
        dragStartX.current = e.clientX;
        scrollStartX.current = el.scrollLeft;
        el.style.cursor = 'grabbing';
        el.style.userSelect = 'none';
    }, []);

    const handleTabsMouseMove = useCallback((e: React.MouseEvent) => {
        if (!isDraggingTabs.current) return;
        const el = tabsScrollRef.current;
        if (!el) return;
        const dx = e.clientX - dragStartX.current;
        if (Math.abs(dx) > 3) {
            wasDragged.current = true;
        }
        el.scrollLeft = scrollStartX.current - dx;
    }, []);

    const handleTabsMouseUp = useCallback(() => {
        isDraggingTabs.current = false;
        const el = tabsScrollRef.current;
        if (el) {
            el.style.cursor = 'grab';
            el.style.userSelect = '';
        }
    }, []);

    const handleTabsMouseLeave = useCallback(() => {
        if (isDraggingTabs.current) {
            handleTabsMouseUp();
        }
    }, [handleTabsMouseUp]);

    return (
        <div className="flex-1 min-w-0 flex justify-start">
            <div
                ref={tabsScrollRef}
                className="flex p-1 bg-white/5 glass-nav rounded-xl relative h-10 items-center w-fit max-w-full overflow-x-auto scrollbar-hide cursor-grab"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                onMouseDown={handleTabsMouseDown}
                onMouseMove={handleTabsMouseMove}
                onMouseUp={handleTabsMouseUp}
                onMouseLeave={handleTabsMouseLeave}
            >
                {displaySearches.map((search) => (
                    <button
                        key={search.id}
                        type="button"
                        onClick={() => {
                            if (wasDragged.current) return;
                            setActiveSearchId(search.id);
                        }}
                        onMouseEnter={(e) => {
                            setHoveredTabId(search.id);
                            e.currentTarget.style.width = `${e.currentTarget.offsetWidth}px`;
                        }}
                        onMouseLeave={(e) => {
                            setHoveredTabId(null);
                            e.currentTarget.style.width = '';
                        }}
                        className={cn(
                            "relative px-4 h-8 flex items-center justify-center text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0 group/tab",
                            activeSearchId === search.id ? "text-white" : "text-gray-500 hover:text-gray-300"
                        )}
                    >
                        {activeSearchId === search.id && (
                            <div className="absolute inset-0 rounded-lg glass-pill" />
                        )}
                        <span
                            className={cn(
                                "relative z-10 flex items-center gap-2 overflow-hidden transition-all",
                            )}
                            style={{
                                maxWidth: hoveredTabId === search.id ? "calc(100% - 5px)" : "100%",
                                maskImage: hoveredTabId === search.id
                                    ? "linear-gradient(to right, #fff 90%, transparent)"
                                    : "linear-gradient(to right, #fff 100%, transparent)",
                                WebkitMaskImage: hoveredTabId === search.id
                                    ? "linear-gradient(to right, #fff 90%, transparent)"
                                    : "linear-gradient(to right, #fff 100%, transparent)",
                                transition: "max-width 0.15s ease, mask-image 0.15s ease, -webkit-mask-image 0.15s ease",
                            }}
                        >
                            <span className="whitespace-nowrap truncate">{search.label}</span>
                            {/* Only show loader for active search (we only track streaming for active) */}
                            {search.id === activeSearchId && streamingSearchIds[search.id] && (
                                <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />
                            )}
                        </span>
                        {/* X replaces end of text on hover */}
                        <span
                            role="button"
                            tabIndex={0}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleTabDelete(search.id);
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                    e.stopPropagation();
                                    handleTabDelete(search.id);
                                }
                            }}
                            className={cn(
                                "absolute right-2 z-20 flex items-center justify-center cursor-pointer opacity-0 transition-opacity",
                                hoveredTabId === search.id ? "opacity-100" : "opacity-0",
                                activeSearchId === search.id
                                    ? "text-white/70 hover:text-white"
                                    : "text-gray-400 hover:text-white"
                            )}
                            aria-label={`Remove ${search.label}`}
                        >
                            <X size={12} />
                        </span>
                    </button>
                ))}
            </div>
        </div>
    );
}
