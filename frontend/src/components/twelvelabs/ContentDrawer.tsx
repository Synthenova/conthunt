"use client";

import { useEffect, useState } from "react";
import { auth } from "@/lib/firebaseClient";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, Play, Link as LinkIcon, Save, StickyNote, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface ContentDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    item: any | null;
}

export function ContentDrawer({ isOpen, onClose, item }: ContentDrawerProps) {
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);

    // Reset analysis state when item changes
    useEffect(() => {
        if (isOpen && item) {
            setAnalysisResult(null);
            setError(null);
            setAnalyzing(false);
            setIsPlaying(false);

            // If item already has analysis data, use it (future optimization)
        }
    }, [isOpen, item]);

    const handleAnalyze = async () => {
        if (!item) return;

        setAnalyzing(true);
        setError(null);

        try {
            const user = auth.currentUser;
            if (!user) {
                throw new Error("User not authenticated");
            }
            const token = await user.getIdToken();

            // Updated API endpoint based on task documentation
            const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/v1/video-analysis/${item.id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) throw new Error("Unauthorized");
                throw new Error('Analysis failed');
            }

            const data = await response.json();

            // Since the API is async and returns status="processing" initially, 
            // for the MVP we might just show "Processing" or handle the immediate response.
            // If the backend returns cached result immediately, we can display it.
            // For now, let's assume we get the result object or a status.

            setAnalysisResult(data);

            // Use polling or websocket in a real prod scenario if status is processing
            // For this implementation, we will display what we have or a "Processing started" message
            // If the data has 'analysis' field, we show it.

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
                                <Button variant="outline" className="border-dashed border-zinc-700 hover:bg-zinc-900/50 hover:border-zinc-600 text-zinc-400 hover:text-white h-10">
                                    <LinkIcon className="mr-2 h-3.5 w-3.5" /> Copy link
                                </Button>
                                <Button variant="outline" className="border-dashed border-zinc-700 hover:bg-zinc-900/50 hover:border-zinc-600 text-zinc-400 hover:text-white h-10">
                                    <StickyNote className="mr-2 h-3.5 w-3.5" /> Add note
                                </Button>
                            </div>
                        </div>

                        {/* AI Analysis Section */}
                        <div className="space-y-4">
                            {!analysisResult && !analyzing ? (
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

                            {analyzing && (
                                <div className="flex flex-col items-center justify-center p-8 border border-dashed border-zinc-800 rounded-xl bg-zinc-900/20 animate-pulse">
                                    <Loader2 className="h-8 w-8 text-yellow-500 animate-spin mb-3" />
                                    <p className="text-sm text-zinc-400">Analyzing video content...</p>
                                </div>
                            )}

                            {error && (
                                <div className="p-4 rounded-lg bg-red-900/20 border border-red-900/50 text-red-200 text-sm mb-4">
                                    {error}
                                </div>
                            )}

                            {analysisResult && (
                                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Sparkles className="h-4 w-4 text-yellow-500" />
                                        <h3 className="font-semibold text-white">AI Extract</h3>
                                    </div>

                                    {/* Mocking structure if not yet populated from backend fully */}
                                    <div className="space-y-4">
                                        <AnalysisSection title="HOOK" content={analysisResult.analysis?.hook || analysisResult?.hook} />
                                        <AnalysisSection title="CTA" content={analysisResult.analysis?.call_to_action || analysisResult?.call_to_action} />
                                        <AnalysisSection title="KEY CLAIMS" content={analysisResult.analysis?.key_topics?.join(", ")} />
                                        <AnalysisSection title="ON-SCREEN TEXT" content={analysisResult.analysis?.on_screen_texts?.join(", ")} />
                                    </div>

                                    {analysisResult.status === 'processing' && (
                                        <div className="p-3 bg-yellow-900/20 border border-yellow-900/30 rounded text-yellow-200 text-xs mt-2">
                                            Analysis is processing in background. Results will appear here once ready.
                                        </div>
                                    )}
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
