"use client";

import * as React from "react";
import { LayoutDashboard, Search, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";

interface BoardOption {
    id: string;
    name: string;
}

interface SearchOption {
    id: string;
    query: string;
    inputs?: Record<string, unknown>;
}

interface MentionDropdownProps {
    boards: BoardOption[];
    searches: SearchOption[];
    isLoadingBoards: boolean;
    isLoadingSearches: boolean;
    query?: string;
    onSelect: (type: 'board' | 'search', item: any) => void;
}

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return FaTiktok;
    if (normalized.includes('instagram')) return FaInstagram;
    if (normalized.includes('youtube')) return FaYoutube;
    if (normalized.includes('pinterest')) return FaPinterest;
    return FaGlobe;
}

export function MentionDropdown({
    boards,
    searches,
    isLoadingBoards,
    isLoadingSearches,
    query,
    onSelect
}: MentionDropdownProps) {
    const [isBoardsOpen, setIsBoardsOpen] = React.useState(false);
    const [isSearchesOpen, setIsSearchesOpen] = React.useState(false);

    React.useEffect(() => {
        if (query && query.trim().length > 0) {
            setIsBoardsOpen(true);
            setIsSearchesOpen(true);
        } else {
            setIsBoardsOpen(false);
            setIsSearchesOpen(false);
        }
    }, [query]);

    return (
        <div className="absolute bottom-full left-4 right-4 mb-2 z-20 w-fit min-w-[300px] animate-in fade-in slide-in-from-bottom-2">
            <div className="bg-zinc-900 text-foreground rounded-md border border-white/10 p-1 shadow-md overflow-hidden">
                {/* Boards Section */}
                <Collapsible
                    open={isBoardsOpen}
                    onOpenChange={setIsBoardsOpen}
                    className="space-y-1"
                >
                    <CollapsibleTrigger asChild>
                        <Button
                            variant="ghost"
                            className="w-full justify-between h-8 px-2 text-sm font-medium hover:bg-zinc-800 hover:text-foreground rounded-sm"
                        >
                            <span className="flex items-center gap-2">
                                <LayoutDashboard className="h-4 w-4 text-muted-foreground" />
                                <span>Boards</span>
                            </span>
                            <ChevronRight className={cn(
                                "h-4 w-4 text-muted-foreground transition-transform duration-200",
                                isBoardsOpen && "rotate-90"
                            )} />
                        </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                        <div className="max-h-48 overflow-y-auto px-1 py-1 space-y-0.5">
                            {isLoadingBoards ? (
                                <div className="text-xs text-muted-foreground px-2 py-1.5">Loading boards...</div>
                            ) : boards.length === 0 ? (
                                <div className="text-xs text-muted-foreground px-2 py-1.5">No boards found</div>
                            ) : (
                                boards.map((board) => (
                                    <button
                                        key={board.id}
                                        onClick={() => onSelect('board', board)}
                                        className="w-full text-left px-2 py-1.5 rounded-sm hover:bg-zinc-800 hover:text-foreground text-sm flex items-center gap-2 group transition-colors outline-none focus:bg-zinc-800 focus:text-foreground"
                                    >
                                        <div className="w-1 h-1 rounded-full bg-muted-foreground/50 group-hover:bg-primary transition-colors" />
                                        <span className="truncate">{board.name}</span>
                                    </button>
                                ))
                            )}
                        </div>
                    </CollapsibleContent>
                </Collapsible>

                <div className="h-px bg-border my-1" />

                {/* Searches Section */}
                <Collapsible
                    open={isSearchesOpen}
                    onOpenChange={setIsSearchesOpen}
                    className="space-y-1"
                >
                    <CollapsibleTrigger asChild>
                        <Button
                            variant="ghost"
                            className="w-full justify-between h-8 px-2 text-sm font-medium hover:bg-zinc-800 hover:text-foreground rounded-sm"
                        >
                            <span className="flex items-center gap-2">
                                <Search className="h-4 w-4 text-muted-foreground" />
                                <span>Searches</span>
                            </span>
                            <ChevronRight className={cn(
                                "h-4 w-4 text-muted-foreground transition-transform duration-200",
                                isSearchesOpen && "rotate-90"
                            )} />
                        </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                        <div className="max-h-48 overflow-y-auto px-1 py-1 space-y-0.5">
                            {isLoadingSearches ? (
                                <div className="text-xs text-muted-foreground px-2 py-1.5">Loading searches...</div>
                            ) : searches.length === 0 ? (
                                <div className="text-xs text-muted-foreground px-2 py-1.5">No searches found</div>
                            ) : (
                                searches.map((search) => {
                                    const platforms = Object.keys(search.inputs || {}).map((key) => getPlatformIcon(key));
                                    const uniquePlatforms = Array.from(new Set(platforms));
                                    return (
                                        <button
                                            key={search.id}
                                            onClick={() => onSelect('search', search)}
                                            className="w-full text-left px-2 py-1.5 rounded-sm hover:bg-zinc-800 hover:text-foreground text-sm flex items-center justify-between gap-2 group transition-colors outline-none focus:bg-zinc-800 focus:text-foreground"
                                        >
                                            <div className="flex items-center gap-2 min-w-0">
                                                <div className="w-1 h-1 rounded-full bg-muted-foreground/50 group-hover:bg-primary transition-colors flex-shrink-0" />
                                                <span className="truncate">{search.query}</span>
                                            </div>
                                            <span className="flex items-center gap-1 text-muted-foreground flex-shrink-0">
                                                {uniquePlatforms.map((Icon, idx) => (
                                                    <Icon key={`${search.id}-icon-${idx}`} className="text-[10px]" />
                                                ))}
                                            </span>
                                        </button>
                                    );
                                })
                            )}
                        </div>
                    </CollapsibleContent>
                </Collapsible>
            </div>
        </div>
    );
}
