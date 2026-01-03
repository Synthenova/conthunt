import { Badge } from "@/components/ui/badge";

interface ContentMetadataProps {
    item: any;
}

export function ContentMetadata({ item }: ContentMetadataProps) {
    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3 overflow-hidden">
                    <div className="h-10 w-10 rounded-full bg-zinc-800 border border-zinc-700 overflow-hidden flex-shrink-0">
                        {item.creator_image ? (
                            <img
                                src={item.creator_image}
                                alt={item.creator_name || item.creator}
                                className="h-full w-full object-cover"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = "none";
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
                                className={`text-sm font-medium text-white truncate ${
                                    item.creator_url ? "hover:text-primary hover:underline cursor-pointer" : ""
                                }`}
                            >
                                {item.creator_name || item.creator || "Unknown Creator"}
                            </a>
                            <Badge variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider h-5 px-1.5 flex-shrink-0">
                                {item.platform || "Platform"}
                            </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground truncate">
                            {item.creator ? (item.creator.startsWith("@") ? item.creator : `@${item.creator}`) : ""}
                        </span>
                    </div>
                </div>
            </div>

            <h2 className="text-2xl font-semibold leading-snug text-white mb-3">
                {item.title || "Untitled Video"}
            </h2>

            <div className="flex flex-wrap gap-2 mb-4" />
        </div>
    );
}
