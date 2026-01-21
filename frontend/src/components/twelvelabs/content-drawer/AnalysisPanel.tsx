import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles } from "lucide-react";
import { ANALYSIS_NOT_READY_MESSAGE } from "./useContentAnalysis";

interface AnalysisPanelProps {
    analysisResult: any;
    analyzing: boolean;
    polling: boolean;
    error: string | null;
    loadingMessage: string;
    analysisDisabled?: boolean;
    analysisDisabledReason?: string;
    onAnalyze: () => void;
}

export function AnalysisPanel({
    analysisResult,
    analyzing,
    polling,
    error,
    loadingMessage,
    analysisDisabled = false,
    analysisDisabledReason,
    onAnalyze,
}: AnalysisPanelProps) {
    return (
        <div className="space-y-4">
            {!analysisResult && !analyzing && !polling ? (
                <div className="relative group w-full">
                    <button
                        onClick={onAnalyze}
                        className="w-full glass-button-white h-12 text-base text-black disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={analysisDisabled}
                        data-tutorial="analyse_button"
                    >
                        <Sparkles className="mr-2 h-4 w-4 text-black" />
                        {analysisDisabled ? (analysisDisabledReason || "Analyze after search completes") : "Analyze with AI"}
                        {!analysisDisabled && <span className="ml-2 text-xs opacity-60 text-black">(1 credit)</span>}
                    </button>
                    {analysisDisabled && analysisDisabledReason && (
                        <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-zinc-800 border border-white/10 text-xs text-white rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                            {analysisDisabledReason}
                        </div>
                    )}
                </div>
            ) : null}

            {(analyzing || polling) && (
                <div className="flex flex-col items-center justify-center py-8">
                    <Loader2 className="h-10 w-10 text-white animate-spin" />
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
                        onClick={onAnalyze}
                        className="ml-auto text-red-300 hover:text-white hover:bg-red-900/30"
                    >
                        Retry
                    </Button>
                </div>
            )}

            {analysisResult && analysisResult.status === "completed" && (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="h-4 w-4 text-white" />
                        <h3 className="font-semibold text-white">AI Extract</h3>
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
                                        <Badge
                                            key={tag}
                                            variant="secondary"
                                            className="bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border-none font-mono text-xs"
                                        >
                                            {tag.startsWith("#") ? tag : `#${tag}`}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {analysisResult && analysisResult.status === "failed" && (
                <div className="p-4 rounded-lg bg-red-900/20 border border-red-900/50 text-red-200 text-sm">
                    <p className="font-medium mb-1">Analysis Failed</p>
                    <p className="text-xs text-red-300/70">{analysisResult.error || "Unknown error occurred"}</p>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={onAnalyze}
                        className="mt-3 border-red-800 text-red-300 hover:bg-red-900/30"
                    >
                        Try Again
                    </Button>
                </div>
            )}
        </div>
    );
}

function AnalysisSection({ title, content }: { title: string; content: string | null }) {
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
