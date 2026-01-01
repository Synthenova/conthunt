"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { auth } from "@/lib/firebaseClient";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Check, Loader2, Sparkles, Play, Link as LinkIcon, Save, StickyNote, Plus } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useBoards } from "@/hooks/useBoards";
import { cn } from "@/lib/utils";

// Fun loading messages for AI analysis
const LOADING_MESSAGES = [
    "Watching your video with AI eyes...",
    "Extracting the good stuff...",
    "Finding the hooks and CTAs...",
    "Scanning for on-screen text...",
    "Analyzing engagement patterns...",
    "Decoding viral potential...",
    "Almost there, thinking hard...",
    "Crunching the content...",
    "AI brain at work...",
    "Uncovering hidden gems...",
];
const ANALYSIS_NOT_READY_MESSAGE = "Finalizing search results...";
const ANALYSIS_POLL_INTERVAL_MS = 2500;
const ANALYSIS_MAX_NOT_READY_RETRIES = 20;
const ANALYSIS_NOT_READY_STATUSES = new Set([404, 409, 425]);
const MEDIA_BASE_VH = 0.6;
const MEDIA_MIN_HEIGHT_PX = 320;
const MEDIA_MAX_HEIGHT_PX = 560;
const MEDIA_COLLAPSE_THRESHOLD = 1;
const MEDIA_COLLAPSE_RATIO = 0.5;

interface ContentDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    item: any | null;
    analysisDisabled?: boolean;
    resumeTime?: number;
}

export function ContentDrawer({
    isOpen,
    onClose,
    item,
    analysisDisabled = false,
    resumeTime = 0,
}: ContentDrawerProps) {
    const viewportRef = useRef<HTMLDivElement>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [polling, setPolling] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0]);
    const [mediaHeight, setMediaHeight] = useState<number | null>(null);
    const [isMediaCollapsed, setIsMediaCollapsed] = useState(false);
    const analysisNotReadyRetries = useRef(0);
    const videoRef = useRef<HTMLVideoElement>(null);
    const youtubeRef = useRef<HTMLIFrameElement>(null);
    const lastSeekTimeRef = useRef<number | null>(null);
    const baseMediaHeightRef = useRef(0);
    const scrollRafRef = useRef<number | null>(null);
    const isYouTube = item?.platform === 'youtube' || item?.platform === 'youtube_search';
    const link = item?.url || item?.canonical_url;
    const youtubeId = isYouTube && link
        ? (link.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^&?/]+)/)?.[1] || item?.external_id || item?.id)
        : null;

    const handleYouTubeSeek = (seekTime: number) => {
        if (!youtubeRef.current) return;
        if (seekTime <= 0) return;
        if (lastSeekTimeRef.current === seekTime) return;
        youtubeRef.current.contentWindow?.postMessage(
            JSON.stringify({ event: "command", func: "seekTo", args: [seekTime, true] }),
            "*"
        );
        lastSeekTimeRef.current = seekTime;
    };

    // Board Management
    const [isBoardPopoverOpen, setIsBoardPopoverOpen] = useState(false);
    const [newBoardName, setNewBoardName] = useState("");
    const [showNewBoardInput, setShowNewBoardInput] = useState(false);

    const {
        boards,
        isLoadingBoards,
        createBoard,
        addToBoard,
        isAddingToBoard,
        isCreatingBoard,
        refetchBoards
    } = useBoards({ checkItemId: item?.id });

    const handleCreateBoard = async () => {
        if (!newBoardName.trim()) return;
        try {
            const newBoard = await createBoard({ name: newBoardName.trim() });
            // Add current item to the new board immediately
            if (item?.id) {
                await addToBoard({ boardId: newBoard.id, contentItemIds: [item.id] });
                // Refetch to update status
                refetchBoards();
            }
            setNewBoardName("");
            setShowNewBoardInput(false);
        } catch (error) {
            console.error("Failed to create board:", error);
        }
    };

    const handleToggleBoard = async (board: any) => {
        if (!item?.id) return;

        // If already has item, maybe we want to allow removing? 
        // For now, prompt said "dim it out", so we assume add-only or just disable.
        // But let's support adding if not present.
        if (board.has_item) return;

        try {
            await addToBoard({ boardId: board.id, contentItemIds: [item.id] });
            refetchBoards();
        } catch (error) {
            console.error("Failed to add to board:", error);
        }
    };

    // Rotate loading messages
    useEffect(() => {
        if (!analyzing && !polling) return;

        const interval = setInterval(() => {
            setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]);
        }, 2500);

        return () => clearInterval(interval);
    }, [analyzing, polling]);

    // Fetch analysis status (used for initial call and polling)
    const fetchAnalysis = useCallback(async () => {
        if (!item) return null;

        const user = auth.currentUser;
        if (!user) return null;

        // Get media_asset_id from the video asset in the assets array
        const videoAsset = item.assets?.find((a: any) => a.asset_type === 'video');
        const mediaAssetId = videoAsset?.id;

        if (!mediaAssetId) {
            // For older YouTube content without video asset, suggest re-searching
            const isYouTube = item.platform === 'youtube' || item.platform === 'youtube_search';
            if (isYouTube) {
                throw new Error("YouTube video analysis requires a fresh search. Please search again to enable analysis.");
            }
            throw new Error("No video asset found for this content");
        }

        const token = await user.getIdToken();
        const { BACKEND_URL } = await import('@/lib/api');

        const response = await fetch(`${BACKEND_URL}/v1/video-analysis/${mediaAssetId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (ANALYSIS_NOT_READY_STATUSES.has(response.status)) {
            return { status: "not_ready" };
        }

        if (!response.ok) {
            const detail = await response.json().catch(() => null);
            throw new Error(detail?.detail || (response.status === 401 ? "Unauthorized" : "Analysis failed"));
        }

        return await response.json();
    }, [item]);

    // Polling effect - poll when status is 'processing'
    useEffect(() => {
        if (!polling) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await fetchAnalysis();
                if (!data) return;
                setAnalysisResult(data);

                if (data?.status === "not_ready") {
                    analysisNotReadyRetries.current += 1;
                    if (analysisNotReadyRetries.current >= ANALYSIS_MAX_NOT_READY_RETRIES) {
                        setPolling(false);
                        setError("Search is still saving results. Please try again in a moment.");
                    }
                    return;
                }

                analysisNotReadyRetries.current = 0;
                if (data?.status !== 'processing') {
                    setPolling(false);
                    clearInterval(pollInterval);
                }
            } catch (err) {
                console.error("Polling error:", err);
                // Don't stop polling on transient errors
            }
        }, ANALYSIS_POLL_INTERVAL_MS);

        return () => clearInterval(pollInterval);
    }, [polling, fetchAnalysis]);

    // Reset state when item changes
    useEffect(() => {
        if (isOpen && item) {
            setAnalysisResult(null);
            setError(null);
            setAnalyzing(false);
            setPolling(false);
            setIsPlaying(true);
            setIsMediaCollapsed(false);
            analysisNotReadyRetries.current = 0;
            lastSeekTimeRef.current = null;
        }
    }, [isOpen, item]);

    useEffect(() => {
        if (!isOpen) {
            setIsPlaying(false);
        }
    }, [isOpen]);

    const setHeightFromBase = useCallback((collapsed: boolean) => {
        const baseHeight = baseMediaHeightRef.current;
        if (!baseHeight) return;
        const ratio = collapsed ? MEDIA_COLLAPSE_RATIO : 1;
        setMediaHeight(Math.round(baseHeight * ratio));
    }, []);

    useEffect(() => {
        if (!isOpen) return;

        const updateBaseHeight = () => {
            const baseHeight = Math.min(
                MEDIA_MAX_HEIGHT_PX,
                Math.max(MEDIA_MIN_HEIGHT_PX, window.innerHeight * MEDIA_BASE_VH)
            );
            baseMediaHeightRef.current = baseHeight;
            setHeightFromBase(isMediaCollapsed);
        };

        updateBaseHeight();
        window.addEventListener("resize", updateBaseHeight);

        return () => {
            window.removeEventListener("resize", updateBaseHeight);
        };
    }, [isOpen, isMediaCollapsed, setHeightFromBase]);

    useEffect(() => {
        if (!isOpen) return;
        setHeightFromBase(isMediaCollapsed);
    }, [isOpen, isMediaCollapsed, setHeightFromBase]);

    const handleViewportScroll = useCallback(() => {
        if (scrollRafRef.current !== null) return;
        scrollRafRef.current = requestAnimationFrame(() => {
            scrollRafRef.current = null;
            const viewport = viewportRef.current;
            if (!viewport) return;
            const shouldCollapse = viewport.scrollTop > MEDIA_COLLAPSE_THRESHOLD;
            setIsMediaCollapsed(prev => (prev === shouldCollapse ? prev : shouldCollapse));
        });
    }, []);

    const handleViewportScrollEvent = useCallback(() => {
        handleViewportScroll();
    }, [handleViewportScroll]);

    useEffect(() => {
        if (!isPlaying) return;
        if (resumeTime <= 0) return;
        if (!videoRef.current) return;

        const video = videoRef.current;
        const safeTime = Math.max(0, resumeTime);
        const seek = () => {
            if (!Number.isNaN(video.duration) && video.duration > 0) {
                video.currentTime = Math.min(safeTime, video.duration);
            } else {
                video.currentTime = safeTime;
            }
            video.play().catch(() => { });
        };

        if (video.readyState >= 1) {
            seek();
        } else {
            const onLoaded = () => {
                seek();
                video.removeEventListener("loadedmetadata", onLoaded);
            };
            video.addEventListener("loadedmetadata", onLoaded);
        }
    }, [isPlaying, resumeTime]);

    useEffect(() => {
        if (!isPlaying) return;
        if (!isYouTube) return;
        if (resumeTime <= 0) return;
        handleYouTubeSeek(resumeTime);
    }, [isPlaying, isYouTube, resumeTime]);

    const handleAnalyze = async () => {
        if (!item || analyzing || polling || analysisDisabled) return;  // Guard against duplicate calls

        setAnalyzing(true);
        setError(null);
        setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]);
        analysisNotReadyRetries.current = 0;

        try {
            const data = await fetchAnalysis();
            setAnalysisResult(data);

            if (data?.status === "not_ready") {
                setLoadingMessage(ANALYSIS_NOT_READY_MESSAGE);
            }

            // If status is processing or not_ready, start polling
            if (data?.status === 'processing' || data?.status === "not_ready") {
                setPolling(true);
            }
        } catch (err) {
            setError("Failed to analyze video. Please try again.");
            console.error(err);
        } finally {
            setAnalyzing(false);
        }
    };

    if (!item) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md md:max-w-lg lg:max-w-xl p-0 gap-0 overflow-hidden bg-[#0A0A0A] border-l-border flex flex-col h-full">
                {/* Media Spotlight */}
                <div className="relative w-full bg-[#0A0A0A] px-5 pt-5 pb-4 shrink-0">
                    <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.06] to-transparent pointer-events-none" />
                    <div
                        className={cn(
                            "relative mx-auto aspect-[9/16] rounded-2xl overflow-hidden bg-black ring-1 ring-white/10 group",
                            "transition-[height,box-shadow] duration-300 ease-out",
                            isMediaCollapsed
                                ? "shadow-[0_12px_30px_rgba(0,0,0,0.45)]"
                                : "shadow-[0_20px_50px_rgba(0,0,0,0.6)]"
                        )}
                        style={{ height: mediaHeight ? `${mediaHeight}px` : "60vh" }}
                    >
                        {!isPlaying ? (
                            <>
                                <img
                                    src={item.thumbnail_url || item.thumbnail}
                                    alt={item.title}
                                    className="w-full h-full object-cover"
                                />
                                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="h-16 w-16 rounded-full bg-white/20 hover:bg-white/30 text-white backdrop-blur-sm"
                                        onClick={() => setIsPlaying(true)}
                                    >
                                        <Play className="h-8 w-8 fill-current" />
                                    </Button>
                                </div>
                                {/* Overlay Badges */}
                                <div className="absolute top-4 left-4 pointer-events-none">
                                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-900 border-none">
                                        AI Overlay
                                    </Badge>
                                </div>
                            </>
                        ) : (
                            (() => {
                                if (isYouTube && youtubeId) {
                                    return (
                                        <iframe
                                            ref={youtubeRef}
                                            src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1&modestbranding=1&playsinline=1&enablejsapi=1`}
                                            className="w-full h-full"
                                            allow="autoplay; encrypted-media; fullscreen"
                                            allowFullScreen
                                            onLoad={() => handleYouTubeSeek(resumeTime)}
                                        />
                                    );
                                }

                                return (
                                    <video
                                        ref={videoRef}
                                        src={item.video_url || item.url}
                                        className="w-full h-full object-cover"
                                        controls
                                        autoPlay
                                        playsInline
                                    >
                                        Your browser does not support the video tag.
                                    </video>
                                );
                            })()
                        )}
                    </div>

                    <div className="absolute top-4 right-5 z-10">
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 bg-black/50 text-white hover:bg-black/70 rounded-full"
                            onClick={onClose}
                        >
                            <XIcon className="h-4 w-4" />
                        </Button>
                    </div>
                </div>

                <ScrollArea
                    className="flex-1 min-h-0 bg-[#0E0E0E]"
                    viewportRef={viewportRef}
                    onViewportScroll={handleViewportScrollEvent}
                >
                    <div className="px-5 pt-6 pb-8 space-y-6 border-t border-white/5 bg-gradient-to-b from-white/[0.03] to-transparent rounded-t-3xl">
                        {/* Title & Metadata */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3 overflow-hidden">
                                    {/* Creator Avatar */}
                                    <div className="h-10 w-10 rounded-full bg-zinc-800 border border-zinc-700 overflow-hidden flex-shrink-0">
                                        {item.creator_image ? (
                                            <img
                                                src={item.creator_image}
                                                alt={item.creator_name || item.creator}
                                                className="h-full w-full object-cover"
                                                onError={(e) => {
                                                    // Fallback if image fails
                                                    (e.target as HTMLImageElement).style.display = 'none';
                                                }}
                                            />
                                        ) : (
                                            <div className="h-full w-full flex items-center justify-center text-zinc-500 font-bold text-xs">
                                                {(item.creator_name || item.creator || "?").substring(0, 1).toUpperCase()}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex flex-col min-w-0">
                                        <div className="flex items-center gap-2">
                                            <a
                                                href={item.creator_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className={`text-sm font-medium text-white truncate ${item.creator_url ? 'hover:text-primary hover:underline cursor-pointer' : ''}`}
                                            >
                                                {item.creator_name || item.creator || 'Unknown Creator'}
                                            </a>
                                            <Badge variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider h-5 px-1.5 flex-shrink-0">
                                                {item.platform || 'Platform'}
                                            </Badge>
                                        </div>
                                        <span className="text-xs text-muted-foreground truncate">
                                            {item.creator ? (item.creator.startsWith('@') ? item.creator : `@${item.creator}`) : ''}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <h2 className="text-2xl font-semibold leading-snug text-white mb-3">
                                {item.title || "Untitled Video"}
                            </h2>

                            <div className="flex flex-wrap gap-2 mb-4">
                                {/* Real hashtags from analysis will appear here if available, otherwise we show nothing or maybe platform badge is enough */}
                            </div>
                        </div>

                        {/* Metrics Panel */}
                        <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.view_count || item.views || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Views</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.like_count || item.likes || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Likes</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.comment_count || item.comments || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Comments</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">
                                    {(() => {
                                        const views = Number(item.view_count || item.views || 0);
                                        const likes = Number(item.like_count || item.likes || 0);
                                        const comments = Number(item.comment_count || item.comments || 0);
                                        const shares = Number(item.share_count || item.shares || 0); // Include shares if available

                                        if (views === 0) return "0%";
                                        const rate = ((likes + comments + shares) / views) * 100;
                                        return rate.toFixed(2) + "%";
                                    })()}
                                </div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Eng.</div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="space-y-3">
                            <Popover open={isBoardPopoverOpen} onOpenChange={setIsBoardPopoverOpen}>
                                <PopoverTrigger asChild>
                                    <Button className="w-full bg-[#1E1E1E] hover:bg-[#2A2A2A] text-white border border-[#333] h-12 text-base font-medium transition-all">
                                        <Save className="mr-2 h-4 w-4 text-zinc-400" />
                                        Save to Board
                                    </Button>
                                </PopoverTrigger>
                                <PopoverContent className="w-72 p-0 bg-zinc-900/95 backdrop-blur-xl border-white/10" align="center" side="top">
                                    <div className="p-3 border-b border-white/10">
                                        <h4 className="font-semibold text-sm text-white">Save to Board</h4>
                                    </div>
                                    <div className="max-h-60 overflow-y-auto p-2">
                                        {isLoadingBoards ? (
                                            <div className="flex items-center justify-center py-8">
                                                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                            </div>
                                        ) : boards.length === 0 ? (
                                            <div className="text-center py-6 text-sm text-muted-foreground">
                                                No boards yet
                                            </div>
                                        ) : (
                                            <div className="space-y-1">
                                                {boards.map((board) => (
                                                    <button
                                                        key={board.id}
                                                        onClick={() => handleToggleBoard(board)}
                                                        disabled={board.has_item || isAddingToBoard}
                                                        className={`
                                                            w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors
                                                            ${board.has_item
                                                                ? 'opacity-50 cursor-not-allowed bg-white/5'
                                                                : 'hover:bg-white/10 text-white'
                                                            }
                                                        `}
                                                    >
                                                        <div className={`
                                                            h-5 w-5 rounded border-2 flex items-center justify-center
                                                            ${board.has_item
                                                                ? 'bg-primary border-primary'
                                                                : 'border-white/30'
                                                            }
                                                        `}>
                                                            {board.has_item && (
                                                                <Check className="h-3 w-3 text-white" />
                                                            )}
                                                        </div>
                                                        <div className="flex-1 min-w-0">
                                                            <div className="font-medium truncate text-white">{board.name}</div>
                                                            <div className="text-xs text-muted-foreground">
                                                                {board.item_count} items
                                                            </div>
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    {/* Create New Board */}
                                    <div className="p-2 border-t border-white/10">
                                        {showNewBoardInput ? (
                                            <div className="flex gap-2">
                                                <Input
                                                    placeholder="Board name..."
                                                    value={newBoardName}
                                                    onChange={(e) => setNewBoardName(e.target.value)}
                                                    onKeyDown={(e) => e.key === 'Enter' && handleCreateBoard()}
                                                    className="h-9 bg-white/5 border-white/10 text-white"
                                                    autoFocus
                                                />
                                                <Button
                                                    size="sm"
                                                    onClick={handleCreateBoard}
                                                    disabled={!newBoardName.trim() || isCreatingBoard}
                                                    className="h-9"
                                                >
                                                    {isCreatingBoard ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <Check className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => setShowNewBoardInput(true)}
                                                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-primary hover:bg-primary/10 transition-colors"
                                            >
                                                <Plus className="h-4 w-4" />
                                                Create new board
                                            </button>
                                        )}
                                    </div>
                                </PopoverContent>
                            </Popover>

                            {/* <div className="grid grid-cols-2 gap-3">
                                <Button
                                    variant="outline"
                                    className="border-dashed border-zinc-700 hover:bg-zinc-900/50 hover:border-zinc-600 text-zinc-400 hover:text-white h-10"
                                    onClick={() => {
                                        const link = item.url || item.canonical_url;
                                        if (link) window.open(link, '_blank', 'noopener,noreferrer');
                                    }}
                                    disabled={!item.url && !item.canonical_url}
                                >
                                    <LinkIcon className="mr-2 h-3.5 w-3.5" /> Open link
                                </Button>
                                <Button variant="outline" className="border-dashed border-zinc-700 hover:bg-zinc-900/50 hover:border-zinc-600 text-zinc-400 hover:text-white h-10">
                                    <StickyNote className="mr-2 h-3.5 w-3.5" /> Add note
                                </Button>
                            </div> */}
                        </div>

                        {/* AI Analysis Section */}
                        <div className="space-y-4">
                            {!analysisResult && !analyzing && !polling ? (
                                <Button
                                    onClick={handleAnalyze}
                                    variant="outline"
                                    className="w-full h-12 border-dashed border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/30 text-zinc-400 hover:text-zinc-200 transition-all group"
                                    disabled={analysisDisabled}
                                >
                                    <Sparkles className="mr-2 h-4 w-4 text-yellow-500 group-hover:scale-110 transition-transform" />
                                    {analysisDisabled ? "Analyze after search completes" : "Analyze with AI"}
                                    {!analysisDisabled && <span className="ml-2 text-xs text-zinc-600">(1 credit)</span>}
                                </Button>
                            ) : null}

                            {(analyzing || polling) && (
                                <div className="flex flex-col items-center justify-center p-8 border border-dashed border-yellow-900/50 rounded-xl bg-gradient-to-b from-yellow-900/10 to-zinc-900/30">
                                    <div className="relative">
                                        <Loader2 className="h-10 w-10 text-yellow-500 animate-spin" />
                                        <Sparkles className="h-4 w-4 text-yellow-400 absolute -top-1 -right-1 animate-pulse" />
                                    </div>
                                    <p className="text-sm text-zinc-300 mt-4 text-center font-medium transition-all duration-300">
                                        {analysisResult?.status === "not_ready" ? ANALYSIS_NOT_READY_MESSAGE : loadingMessage}
                                    </p>
                                    <p className="text-xs text-zinc-500 mt-1">This may take 10-30 seconds</p>
                                </div>
                            )}

                            {error && (
                                <div className="p-4 rounded-lg bg-red-900/20 border border-red-900/50 text-red-200 text-sm mb-4 flex items-center gap-2">
                                    <span>⚠️</span> {error}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleAnalyze}
                                        className="ml-auto text-red-300 hover:text-white hover:bg-red-900/30"
                                    >
                                        Retry
                                    </Button>
                                </div>
                            )}

                            {analysisResult && analysisResult.status === 'completed' && (
                                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Sparkles className="h-4 w-4 text-yellow-500" />
                                        <h3 className="font-semibold text-white">AI Extract</h3>
                                        <Badge variant="outline" className="ml-auto text-[10px] border-green-800 text-green-400">
                                            Complete
                                        </Badge>
                                    </div>

                                    <div className="space-y-4">
                                        <AnalysisSection title="HOOK" content={analysisResult.analysis?.hook} />
                                        <AnalysisSection title="CTA" content={analysisResult.analysis?.call_to_action} />
                                        <AnalysisSection title="KEY TOPICS" content={analysisResult.analysis?.key_topics?.join(", ")} />
                                        <AnalysisSection title="ON-SCREEN TEXT" content={analysisResult.analysis?.on_screen_texts?.join(", ")} />
                                        <AnalysisSection title="SUMMARY" content={analysisResult.analysis?.summary} />
                                        {analysisResult.analysis?.hashtags?.length > 0 && (
                                            <div className="space-y-1.5">
                                                <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">HASHTAGS</h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {analysisResult.analysis.hashtags.map((tag: string) => (
                                                        <Badge key={tag} variant="secondary" className="bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border-none font-mono text-xs">
                                                            {tag.startsWith('#') ? tag : `#${tag}`}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {analysisResult && analysisResult.status === 'failed' && (
                                <div className="p-4 rounded-lg bg-red-900/20 border border-red-900/50 text-red-200 text-sm">
                                    <p className="font-medium mb-1">Analysis Failed</p>
                                    <p className="text-xs text-red-300/70">{analysisResult.error || "Unknown error occurred"}</p>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={handleAnalyze}
                                        className="mt-3 border-red-800 text-red-300 hover:bg-red-900/30"
                                    >
                                        Try Again
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}

function AnalysisSection({ title, content }: { title: string, content: string | null }) {
    if (!content) return null;
    return (
        <div className="space-y-1.5">
            <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">{title}</h4>
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 text-sm text-zinc-300 leading-relaxed">
                {content}
            </div>
        </div>
    );
}

function XIcon({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M18 6 6 18" /><path d="m6 6 18 18" /></svg>
    )
}

function formatMetric(num: number): string {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}
