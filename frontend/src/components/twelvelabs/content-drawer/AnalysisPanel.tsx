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
    onAnalyze: () => void;
}

export function AnalysisPanel({
    analysisResult,
    analyzing,
    polling,
    error,
    loadingMessage,
    analysisDisabled = false,
    onAnalyze,
}: AnalysisPanelProps) {
    return (
        <div className="space-y-4">
            {!analysisResult && !analyzing && !polling ? (
                <button
                    onClick={onAnalyze}
                    className="w-full glass-button-yellow h-12 text-base"
                    disabled={analysisDisabled}
                >
                    <Sparkles className="mr-2 h-4 w-4" />
                    {analysisDisabled ? "Analyze after search completes" : "Analyze with AI"}
                    {!analysisDisabled && <span className="ml-2 text-xs opacity-60">(1 credit)</span>}
                </button>
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
