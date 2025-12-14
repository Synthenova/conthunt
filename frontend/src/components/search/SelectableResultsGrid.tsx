import { SelectableMediaCard } from "./SelectableMediaCard";
import { Skeleton } from "@/components/ui/skeleton";

interface SelectableResultsGridProps {
    results: any[];
    loading: boolean;
}

export function SelectableResultsGrid({ results, loading }: SelectableResultsGridProps) {
    if (loading) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {[...Array(10)].map((_, i) => (
                    <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                        <Skeleton className="h-full w-full" />
                    </div>
                ))}
            </div>
        );
    }

    if (!results || results.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
                <div className="h-24 w-24 rounded-full bg-white/5 flex items-center justify-center mb-4">
                    <span className="text-4xl">🔍</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">Ready to Hunt?</h3>
                <p className="text-muted-foreground max-w-sm">
                    Enter a keyword above to search across Instagram, TikTok, YouTube, and more simultaneously.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-20">
            {results.map((item, i) => (
                <div key={item.id || i} className="animate-in fade-in zoom-in duration-500" style={{ animationDelay: `${i * 50}ms` }}>
                    <SelectableMediaCard
                        item={item}
                        platform={item.platform || 'unknown'}
                    />
                </div>
            ))}
        </div>
    );
}
