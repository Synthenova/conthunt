import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Sparkles, ChevronDown, ChevronRight, Clock, Users, Box, Clapperboard, Music, Eye, FileText } from "lucide-react";
import { ANALYSIS_NOT_READY_MESSAGE } from "./useContentAnalysis";
import { useState } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

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
    if (!analysisResult && !analyzing && !polling) {
        return (
            <div className="relative group w-full">
                <button
                    onClick={onAnalyze}
                    className="w-full glass-button-white h-12 text-base text-black disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
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
        );
    }

    if (analyzing || polling) {
        return (
            <div className="flex flex-col items-center justify-center py-8">
                <Loader2 className="h-10 w-10 text-white animate-spin" />
                <p className="text-sm text-zinc-300 mt-4 text-center font-medium transition-all duration-300">
                    {analysisResult?.status === "not_ready" ? ANALYSIS_NOT_READY_MESSAGE : loadingMessage}
                </p>
                <p className="text-xs text-zinc-500 mt-1">This may take 10-30 seconds</p>
            </div>
        );
    }

    if (error || (analysisResult && analysisResult.status === "failed")) {
        return (
            <div className="p-4 rounded-lg bg-red-900/20 border border-red-900/50 text-red-200 text-sm flex flex-col items-start gap-2">
                <div className="flex items-center gap-2 font-medium">
                    <span>⚠️</span> Analysis Failed
                </div>
                <p className="text-xs text-red-300/70">{error || analysisResult?.error || "Unknown error occurred"}</p>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onAnalyze}
                    className="mt-2 text-red-300 hover:text-white hover:bg-red-900/30 self-end"
                >
                    Retry
                </Button>
            </div>
        );
    }

    if (analysisResult && analysisResult.status === "completed" && analysisResult.analysis) {
        const data = analysisResult.analysis;

        // Check if data is a string (new markdown format) or object (legacy JSON format)
        const isMarkdown = typeof data === "string";

        if (isMarkdown) {
            // NEW: Render markdown content
            return (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
                        <Sparkles className="h-4 w-4 text-blue-400" />
                        <h3 className="font-semibold text-white">AI Analysis</h3>
                    </div>
                    <div className="prose prose-sm prose-invert max-w-none prose-headings:text-zinc-200 prose-headings:font-semibold prose-h2:text-base prose-h2:mt-4 prose-h2:mb-2 prose-h3:text-sm prose-p:text-zinc-300 prose-p:leading-relaxed prose-li:text-zinc-300 prose-strong:text-zinc-200 prose-ul:my-1 prose-li:my-0">
                        <ReactMarkdown>{data}</ReactMarkdown>
                    </div>
                </div>
            );
        }

        // LEGACY: Handle old JSON format
        const isLegacy = !data.overall_assessment && (data.hook || data.call_to_action || Array.isArray(data.key_topics));

        return (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/10">
                    <Sparkles className="h-4 w-4 text-blue-400" />
                    <h3 className="font-semibold text-white">AI Analysis</h3>
                </div>

                {isLegacy ? (
                    // Legacy View
                    <div className="space-y-4">
                        <AnalysisSection title="HOOK" content={data.hook} icon={<Sparkles className="w-3 h-3" />} />
                        <AnalysisSection title="CTA" content={data.call_to_action} icon={<Sparkles className="w-3 h-3" />} />
                        <AnalysisSection title="KEY TOPICS" content={Array.isArray(data.key_topics) ? data.key_topics.join(", ") : data.key_topics} icon={<Box className="w-3 h-3" />} />
                        <AnalysisSection
                            title="ON-SCREEN TEXT"
                            content={Array.isArray(data.on_screen_texts) ? data.on_screen_texts.join(", ") : data.on_screen_texts}
                            icon={<FileText className="w-3 h-3" />}
                        />
                        <AnalysisSection title="SUMMARY" content={data.summary} icon={<FileText className="w-3 h-3" />} />

                        {data.hashtags?.length > 0 && (
                            <div className="space-y-1.5">
                                <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-1">
                                    <Sparkles className="w-3 h-3" /> HASHTAGS
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                    {data.hashtags.map((tag: string) => (
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
                        <div className="p-3 rounded bg-blue-900/10 border border-blue-900/30 text-[10px] text-blue-300 mt-4">
                            This analysis was generated with an older version of the AI. Re-analyze to get deeper insights.
                        </div>
                    </div>
                ) : (
                    // V2 JSON View (legacy but not oldest)
                    <>
                        {/* Summary & Themes (High Level) */}
                        <div className="space-y-4">
                            <AnalysisSection
                                title="SUMMARY"
                                content={data.overall_assessment?.summary}
                                icon={<FileText className="w-3 h-3" />}
                            />

                            {data.content_and_themes?.themes?.length > 0 && (
                                <div className="space-y-1.5">
                                    <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-1">
                                        <Sparkles className="w-3 h-3" /> THEMES
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {data.content_and_themes.themes.map((theme: string, i: number) => (
                                            <Badge key={i} variant="secondary" className="bg-zinc-900 text-zinc-300 border-zinc-800 text-xs font-normal">
                                                {theme}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Detailed Sections (Collapsible) */}
                        <div className="space-y-2">
                            <SimpleAccordion title="Metadata" icon={<Clock className="w-3 h-3" />}>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <MetaItem label="Duration" value={data.metadata?.duration_estimated} />
                                    <MetaItem label="Type" value={data.metadata?.video_type} />
                                    <MetaItem label="Resolution" value={data.metadata?.resolution_quality} />
                                    <MetaItem label="Aspect" value={data.metadata?.aspect_ratio} />
                                </div>
                            </SimpleAccordion>

                            <SimpleAccordion title="Transcript & Text" icon={<FileText className="w-3 h-3" />}>
                                <div className="space-y-3">
                                    {data.transcript?.spoken_dialogue?.length > 0 && (
                                        <div>
                                            <h5 className="text-xs font-semibold text-zinc-400 mb-1">Spoken</h5>
                                            <ul className="space-y-1">
                                                {data.transcript.spoken_dialogue.map((line: any, i: number) => (
                                                    <li key={i} className="text-xs text-zinc-300">
                                                        <span className="text-zinc-500 font-mono text-[10px] mr-1">[{line.timestamp_start}]</span>
                                                        <span className="text-zinc-400">{line.speaker}:</span> {line.text}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {data.transcript?.on_screen_text?.length > 0 && (
                                        <div>
                                            <h5 className="text-xs font-semibold text-zinc-400 mb-1">On-Screen</h5>
                                            <ul className="space-y-1">
                                                {data.transcript.on_screen_text.map((item: any, i: number) => (
                                                    <li key={i} className="text-xs text-zinc-300">
                                                        <span className="text-zinc-500 font-mono text-[10px] mr-1">[{item.timestamp_start}]</span>
                                                        {item.text}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </SimpleAccordion>

                            <SimpleAccordion title="Characters" icon={<Users className="w-3 h-3" />}>
                                <div className="space-y-3">
                                    {data.characters?.map((char: any, i: number) => (
                                        <div key={i} className="text-xs bg-zinc-900/50 p-2 rounded border border-zinc-800">
                                            <div className="font-semibold text-white">{char.name || char.id} <span className="font-normal text-zinc-500">({char.role})</span></div>
                                            <div className="text-zinc-400 mt-1">{char.description}</div>
                                            {char.expressions_observed?.length > 0 && (
                                                <div className="flex gap-1 mt-1 flex-wrap">
                                                    {char.expressions_observed.map((exp: string, j: number) => (
                                                        <span key={j} className="text-[10px] bg-zinc-800 px-1 rounded text-zinc-400">{exp}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </SimpleAccordion>

                            <SimpleAccordion title="Scenes" icon={<Clapperboard className="w-3 h-3" />}>
                                <div className="space-y-2">
                                    {data.scenes?.map((scene: any, i: number) => (
                                        <div key={i} className="text-xs border border-zinc-800/50 p-2 rounded hover:bg-zinc-900/40 transition-colors">
                                            <div className="flex justify-between text-zinc-500 font-mono text-[10px] mb-1">
                                                <span>Scene {scene.scene_number}</span>
                                                <span>{scene.timestamp_start} - {scene.timestamp_end}</span>
                                            </div>
                                            <div className="text-zinc-300 font-medium">{scene.primary_subject}</div>
                                            <div className="text-zinc-400 mt-0.5">{scene.location}</div>
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {scene.actions_occurring?.map((act: any, j: number) => (
                                                    <span key={j} className="text-zinc-500 italic">• {act.action}</span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </SimpleAccordion>

                            <SimpleAccordion title="Visuals & Audio" icon={<Eye className="w-3 h-3" />}>
                                <div className="space-y-3 text-xs">
                                    <div className="grid grid-cols-2 gap-2">
                                        <MetaItem label="Lighting" value={data.visual_and_cinematographic_analysis?.lighting_design?.primary_style} />
                                        <MetaItem label="Camera" value={data.visual_and_cinematographic_analysis?.camera_work?.overall_style} />
                                        <MetaItem label="Color" value={data.visual_and_cinematographic_analysis?.color_grading?.look} />
                                        <MetaItem label="Editing" value={data.visual_and_cinematographic_analysis?.editing_style?.pacing} />
                                    </div>
                                    <div className="border-t border-zinc-800 pt-2">
                                        <h5 className="font-semibold text-zinc-400 mb-1 flex items-center gap-1"><Music className="w-3 h-3" /> Audio</h5>
                                        <div className="grid grid-cols-2 gap-2">
                                            <MetaItem label="Music" value={data.audio_analysis?.music?.genre} />
                                            <MetaItem label="Mood" value={data.audio_analysis?.music?.mood} />
                                        </div>
                                    </div>
                                </div>
                            </SimpleAccordion>

                            <SimpleAccordion title="Timeline" icon={<Clock className="w-3 h-3" />}>
                                <div className="space-y-2 pl-2 border-l border-zinc-800 ml-1">
                                    {data.timeline_summary?.intro && (
                                        <TimelineItem time={data.timeline_summary.intro.timestamp} text={data.timeline_summary.intro.description} label="Intro" />
                                    )}
                                    {data.timeline_summary?.key_moments?.map((m: any, i: number) => (
                                        <TimelineItem key={i} time={m.timestamp} text={m.description} />
                                    ))}
                                    {data.timeline_summary?.climax && (
                                        <TimelineItem time={data.timeline_summary.climax.timestamp} text={data.timeline_summary.climax.description} label="Climax" />
                                    )}
                                    {data.timeline_summary?.conclusion && (
                                        <TimelineItem time={data.timeline_summary.conclusion.timestamp} text={data.timeline_summary.conclusion.description} label="End" />
                                    )}
                                </div>
                            </SimpleAccordion>
                        </div>
                    </>
                )}
            </div>
        );
    }

    return null;
}

function AnalysisSection({ title, content, icon }: { title: string; content: string | null; icon?: React.ReactNode }) {
    if (!content) return null;
    return (
        <div className="space-y-1.5">
            <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-1">
                {icon} {title}
            </h4>
            <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 text-sm text-zinc-300 leading-relaxed">
                {content}
            </div>
        </div>
    );
}

function MetaItem({ label, value }: { label: string, value?: string }) {
    if (!value) return null;
    return (
        <div className="flex flex-col">
            <span className="text-[10px] text-zinc-500 uppercase">{label}</span>
            <span className="text-zinc-300 truncate" title={value}>{value}</span>
        </div>
    )
}

function TimelineItem({ time, text, label }: { time?: string, text?: string, label?: string }) {
    if (!text) return null;
    return (
        <div className="text-xs relative">
            <div className="absolute -left-[13px] top-1.5 w-1.5 h-1.5 rounded-full bg-zinc-700"></div>
            <div className="text-zinc-500 font-mono text-[10px]">
                {time} {label && <span className="text-blue-400 ml-1 uppercase border border-blue-900/50 bg-blue-900/20 px-1 rounded-[2px]">{label}</span>}
            </div>
            <div className="text-zinc-300">{text}</div>
        </div>
    )
}

function SimpleAccordion({ title, children, icon }: { title: string; children: React.ReactNode; icon?: React.ReactNode }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <Collapsible open={isOpen} onOpenChange={setIsOpen} className="border border-zinc-800 rounded-lg bg-zinc-900/20 overflow-hidden">
            <CollapsibleTrigger className="flex items-center justify-between w-full p-3 text-left hover:bg-zinc-900/40 transition-colors">
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                    {icon} {title}
                </span>
                <ChevronRight className={cn("h-4 w-4 text-zinc-500 transition-transform duration-200", isOpen && "rotate-90")} />
            </CollapsibleTrigger>
            <CollapsibleContent className="animate-collapsible-down">
                <div className="p-3 pt-0 border-t border-zinc-800/50 mt-2">
                    {children}
                </div>
            </CollapsibleContent>
        </Collapsible>
    )
}

