"use client";

import { useEffect, useState, useCallback } from "react";
import { auth } from "@/lib/firebaseClient";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Play, Link as LinkIcon, Save, StickyNote, Plus } from "lucide-react";
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

interface ContentDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    item: any | null;
}

export function ContentDrawer({ isOpen, onClose, item }: ContentDrawerProps) {
    const [analyzing, setAnalyzing] = useState(false);
    const [polling, setPolling] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0]);

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
            throw new Error("No video asset found for this content");
        }

        const token = await user.getIdToken();
        const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

        const response = await fetch(`${apiUrl}/v1/video-analysis/${mediaAssetId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(response.status === 401 ? "Unauthorized" : "Analysis failed");
        }

        return await response.json();
    }, [item]);

    // Polling effect - poll when status is 'processing'
    useEffect(() => {
        if (!polling || analysisResult?.status !== 'processing') {
            setPolling(false);
            return;
        }

        const pollInterval = setInterval(async () => {
            try {
                const data = await fetchAnalysis();
                setAnalysisResult(data);

                if (data?.status !== 'processing') {
                    setPolling(false);
                    clearInterval(pollInterval);
                }
            } catch (err) {
                console.error("Polling error:", err);
                // Don't stop polling on transient errors
            }
        }, 4000);  // Poll every 4 seconds

        return () => clearInterval(pollInterval);
    }, [polling, analysisResult?.status, fetchAnalysis]);

    // Reset state when item changes
    useEffect(() => {
        if (isOpen && item) {
            setAnalysisResult(null);
            setError(null);
            setAnalyzing(false);
            setPolling(false);
            setIsPlaying(false);
        }
    }, [isOpen, item]);

    const handleAnalyze = async () => {
        if (!item || analyzing || polling) return;  // Guard against duplicate calls

        setAnalyzing(true);
        setError(null);
        setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]);

        try {
            const data = await fetchAnalysis();
            setAnalysisResult(data);

            // If status is processing, start polling
            if (data?.status === 'processing') {
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
                {/* Header / Media Area */}
                {/* Header / Media Area */}
                <div className="relative h-60 w-full bg-black flex items-center justify-center group shrink-0">
                    {!isPlaying ? (
                        <>
                            <img
                                src={item.thumbnail_url || item.thumbnail}
                                alt={item.title}
                                className="w-full h-full object-contain"
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
                        <video
                            src={item.video_url || item.url}
                            className="w-full h-full object-contain"
                            controls
                            autoPlay
                        >
                            Your browser does not support the video tag.
                        </video>
                    )}

                    <div className="absolute top-4 right-14 z-10">
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

                <ScrollArea className="flex-1 min-h-0">
                    <div className="p-6 space-y-6">
                        {/* Title & Metadata */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <Badge variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-400 font-mono text-xs uppercase tracking-wider">
                                    {item.platform || 'Unknown Platform'}
                                </Badge>
                                <span className="text-muted-foreground text-xs">@{item.creator_username || 'creator'}</span>
                            </div>

                            <h2 className="text-xl font-semibold leading-tight text-white mb-3">
                                {item.title || "Untitled Video"}
                            </h2>

                            <div className="flex flex-wrap gap-2 mb-4">
                                {['#skincare', '#routine', '#glowup', '#beauty'].map(tag => (
                                    <Badge key={tag} variant="secondary" className="bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border-none font-mono text-xs">
                                        {tag}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* Metrics Panel */}
                        <div className="grid grid-cols-4 gap-4 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.views || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Views</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.likes || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Likes</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.comments || 0)}</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Comments</div>
                            </div>
                            <div className="text-center">
                                <div className="text-lg font-bold text-white mb-1">{formatMetric(item.engagement_rate || 0)}%</div>
                                <div className="text-xs text-muted-foreground uppercase tracking-wider font-mono">Eng.</div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="space-y-3">
                            <Button className="w-full bg-[#1E1E1E] hover:bg-[#2A2A2A] text-white border border-[#333] h-12 text-base font-medium transition-all">
                                <Save className="mr-2 h-4 w-4 text-zinc-400" />
                                Save to Board
                            </Button>

                            <div className="grid grid-cols-2 gap-3">
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
                            </div>
                        </div>

                        {/* AI Analysis Section */}
                        <div className="space-y-4">
                            {!analysisResult && !analyzing && !polling ? (
                                <Button
                                    onClick={handleAnalyze}
                                    variant="outline"
                                    className="w-full h-12 border-dashed border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/30 text-zinc-400 hover:text-zinc-200 transition-all group"
                                >
                                    <Sparkles className="mr-2 h-4 w-4 text-yellow-500 group-hover:scale-110 transition-transform" />
                                    Analyze with AI
                                    <span className="ml-2 text-xs text-zinc-600">(1 credit)</span>
                                </Button>
                            ) : null}

                            {(analyzing || polling) && (
                                <div className="flex flex-col items-center justify-center p-8 border border-dashed border-yellow-900/50 rounded-xl bg-gradient-to-b from-yellow-900/10 to-zinc-900/30">
                                    <div className="relative">
                                        <Loader2 className="h-10 w-10 text-yellow-500 animate-spin" />
                                        <Sparkles className="h-4 w-4 text-yellow-400 absolute -top-1 -right-1 animate-pulse" />
                                    </div>
                                    <p className="text-sm text-zinc-300 mt-4 text-center font-medium transition-all duration-300">
                                        {loadingMessage}
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
