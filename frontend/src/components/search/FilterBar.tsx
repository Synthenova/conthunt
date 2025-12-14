import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { useSearchStore } from "@/lib/store";
import { Badge } from "@/components/ui/badge";
import { PLATFORM_CONFIG } from "@/lib/platform-config";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { ChevronDown, SlidersHorizontal, ArrowUpDown } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

export function FilterBar() {
    const { limit, setLimit, platformInputs, filters, setFilter, sortBy, setSort } = useSearchStore();

    // Get enabled platforms that have config
    const activePlatforms = Object.entries(platformInputs)
        .filter(([key, enabled]) => enabled && PLATFORM_CONFIG[key])
        .map(([key]) => key);

    return (
        <div className="w-full max-w-4xl space-y-4">
            {/* Platform Filters */}
            {activePlatforms.length > 0 && (
                <ScrollArea className="w-full whitespace-nowrap rounded-xl border border-white/5 bg-white/5 backdrop-blur-sm">
                    <div className="flex w-max space-x-4 p-4">
                        {activePlatforms.map((platformKey) => {
                            const config = PLATFORM_CONFIG[platformKey];
                            const platformFilters = filters[platformKey] || {};
                            const currentSort = sortBy[platformKey];

                            if (config.filters.length === 0 && config.sorts.length === 0) return null;

                            return (
                                <div key={platformKey} className="flex items-center gap-2 border-r border-white/10 pr-4 last:border-0">
                                    <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mr-2">
                                        {config.label}
                                    </div>

                                    {/* Sort Dropdown */}
                                    {config.sorts.length > 0 && (
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="sm" className="h-8 gap-1 bg-white/5 border border-white/10">
                                                    <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                                                    <span className="text-xs">
                                                        {config.sorts.find(s => s.key === currentSort)?.label || "Sort"}
                                                    </span>
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="start">
                                                <DropdownMenuLabel>Sort by</DropdownMenuLabel>
                                                <DropdownMenuSeparator />
                                                <DropdownMenuRadioGroup value={currentSort} onValueChange={(val) => setSort(platformKey, val)}>
                                                    {config.sorts.map((option) => (
                                                        <DropdownMenuRadioItem key={option.key} value={option.key}>
                                                            {option.label}
                                                        </DropdownMenuRadioItem>
                                                    ))}
                                                </DropdownMenuRadioGroup>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    )}

                                    {/* Filter Dropdowns */}
                                    {config.filters.map((filter) => (
                                        <DropdownMenu key={filter.key}>
                                            <DropdownMenuTrigger asChild>
                                                <Button variant="ghost" size="sm" className="h-8 gap-1 bg-white/5 border border-white/10">
                                                    <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
                                                    <span className="text-xs">
                                                        {filter.type === 'select' && filter.options
                                                            ? (filter.options.find(o => o.value === platformFilters[filter.key])?.label || filter.label)
                                                            : filter.label}
                                                    </span>
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="start">
                                                <DropdownMenuLabel>{filter.label}</DropdownMenuLabel>
                                                <DropdownMenuSeparator />
                                                {filter.type === 'select' && filter.options && (
                                                    <DropdownMenuRadioGroup
                                                        value={platformFilters[filter.key] || ""}
                                                        onValueChange={(val) => setFilter(platformKey, filter.key, val)}
                                                    >
                                                        {filter.options.map((option) => (
                                                            <DropdownMenuRadioItem key={option.value} value={option.value}>
                                                                {option.label}
                                                            </DropdownMenuRadioItem>
                                                        ))}
                                                    </DropdownMenuRadioGroup>
                                                )}
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    ))}
                                </div>
                            );
                        })}
                    </div>
                    <ScrollBar orientation="horizontal" />
                </ScrollArea>
            )}
        </div>
    );
}
