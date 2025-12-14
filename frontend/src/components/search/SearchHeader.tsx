import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Loader2 } from "lucide-react";
import { useSearchStore } from "@/lib/store";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

interface SearchHeaderProps {
    onSearch: () => void;
    isLoading: boolean;
}

export function SearchHeader({ onSearch, isLoading }: SearchHeaderProps) {
    const { query, setQuery, platformInputs, togglePlatform } = useSearchStore();

    const platforms = [
        { key: 'instagram_reels', label: 'Instagram' },
        { key: 'tiktok_keyword', label: 'TikTok' },
        { key: 'youtube', label: 'YouTube' },
        { key: 'pinterest', label: 'Pinterest' },
    ];

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            onSearch();
        }
    };

    return (
        <div className="flex flex-col gap-4 w-full max-w-4xl mx-auto">
            <div className="relative group">
                <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative flex items-center bg-background/50 backdrop-blur-xl border border-white/10 rounded-full px-2 py-2 shadow-2xl">
                    <div className="pl-4">
                        <Search className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <Input
                        placeholder="Search for trends, topics, or hashtags..."
                        className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 h-10 text-lg px-4"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    <Button
                        size="lg"
                        onClick={onSearch}
                        disabled={isLoading || !query.trim()}
                        className="rounded-full px-8 bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_0_20px_rgba(var(--primary),0.3)]"
                    >
                        {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                        Search
                    </Button>
                </div>
            </div>

            {/* Platform Toggles */}
            <div className="flex flex-wrap items-center justify-center gap-4 animate-in fade-in slide-in-from-top-2 duration-700">
                {platforms.map((p) => (
                    <div key={p.key} className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-full border border-white/5 hover:bg-white/10 transition-colors">
                        <Switch
                            id={p.key}
                            checked={platformInputs[p.key as keyof typeof platformInputs]}
                            onCheckedChange={() => togglePlatform(p.key as any)}
                            className="scale-75 data-[state=checked]:bg-primary"
                        />
                        <Label htmlFor={p.key} className="text-xs font-medium cursor-pointer text-muted-foreground">
                            {p.label}
                        </Label>
                    </div>
                ))}
            </div>
        </div>
    );
}
