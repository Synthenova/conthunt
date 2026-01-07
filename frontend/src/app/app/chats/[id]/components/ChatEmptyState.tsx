
import { Loader2, Search } from "lucide-react";

interface ChatEmptyStateProps {
    state: "loading" | "empty";
}

export function ChatEmptyState({ state }: ChatEmptyStateProps) {
    if (state === "loading") {
        return (
            <div className="min-h-[70vh] flex items-center justify-center">
                <div className="flex flex-col items-center gap-3 text-center">
                    <div className="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center text-muted-foreground">
                        <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                    <div className="space-y-1">
                        <h3 className="text-base font-semibold text-white">Loading chat</h3>
                        <p className="text-sm text-muted-foreground">Fetching your conversation history and results.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-[70vh] flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-center">
                <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center text-muted-foreground">
                    <Search className="h-8 w-8" />
                </div>
                <div className="space-y-1">
                    <h3 className="text-lg font-semibold text-white">Canvas</h3>
                    <p className="text-sm text-muted-foreground">
                        Start a conversation to search for content. Results will appear here as you explore.
                    </p>
                </div>
            </div>
        </div>
    );
}
