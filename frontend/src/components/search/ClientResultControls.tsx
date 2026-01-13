import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
    DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";
import { ArrowUpDown, Calendar, Filter } from "lucide-react";

export type ClientSortOption = "default" | "views" | "likes" | "shares" | "comments" | "newest";
export type ClientDateFilter =
    | "all"
    | "today"
    | "yesterday"
    | "week"
    | "this_week"
    | "month"
    | "this_month"
    | "three_months"
    | "six_months"
    | "year";

interface ClientResultControlsProps {
    sort: ClientSortOption;
    onSortChange: (val: ClientSortOption) => void;
    dateFilter: ClientDateFilter;
    onDateFilterChange: (val: ClientDateFilter) => void;
    platforms: string[];
    selectedPlatforms: string[];
    onPlatformsChange: (val: string[]) => void;
    totalResults: number;
}

export function ClientResultControls({
    sort,
    onSortChange,
    dateFilter,
    onDateFilterChange,
    platforms,
    selectedPlatforms,
    onPlatformsChange,
    totalResults
}: ClientResultControlsProps) {

    const sortLabels: Record<ClientSortOption, string> = {
        default: "Relevancy",
        views: "Most Viewed",
        likes: "Most Liked",
        shares: "Most Shared",
        comments: "Most Commented",
        newest: "Newest First"
    };

    const filterLabels: Record<ClientDateFilter, string> = {
        all: "All Time",
        today: "Today",
        yesterday: "Yesterday",
        week: "Last 7 Days",
        this_week: "This Week",
        month: "Last 30 Days",
        this_month: "This Month",
        three_months: "Last 3 Months",
        six_months: "Last 6 Months",
        year: "Last Year"
    };

    return (
        <div className="flex items-center gap-2 py-2 px-1">
            <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 gap-2 bg-white/5 border border-white/10 text-xs">
                        <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Sort:</span>
                        <span className="font-medium text-white">{sortLabels[sort]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="bg-zinc-900 border-white/10 text-white">
                    <DropdownMenuLabel>Sort Results By</DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuRadioGroup value={sort} onValueChange={(val) => {
                        onSortChange(val as ClientSortOption);
                    }}>
                        {Object.entries(sortLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key} className="focus:bg-white/10 focus:text-white">
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 gap-2 bg-white/5 border border-white/10 text-xs">
                        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Date:</span>
                        <span className="font-medium text-white">{filterLabels[dateFilter]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="bg-zinc-900 border-white/10 text-white">
                    <DropdownMenuLabel>Filter By Date</DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuRadioGroup value={dateFilter} onValueChange={(val) => {
                        onDateFilterChange(val as ClientDateFilter);
                    }}>
                        {Object.entries(filterLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key} className="focus:bg-white/10 focus:text-white">
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            {platforms.length > 0 && (
                <DropdownMenu modal={false}>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 gap-2 bg-white/5 border border-white/10 text-xs text-white">
                            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="text-muted-foreground">Platform:</span>
                            <span className="font-medium">
                                {selectedPlatforms.length === 0 || selectedPlatforms.length === platforms.length
                                    ? "All"
                                    : `${selectedPlatforms.length} selected`}
                            </span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        align="start"
                        className="min-w-[160px] bg-zinc-900 border-white/10 text-white"
                    >
                        <DropdownMenuLabel>Filter By Platform</DropdownMenuLabel>
                        <DropdownMenuSeparator className="bg-white/10" />
                        {platforms.map((p) => (
                            <DropdownMenuCheckboxItem
                                key={p}
                                checked={selectedPlatforms.includes(p)}
                                onCheckedChange={(checked) => {
                                    if (checked) {
                                        onPlatformsChange([...selectedPlatforms, p]);
                                    } else {
                                        onPlatformsChange(selectedPlatforms.filter(x => x !== p));
                                    }
                                }}
                                onSelect={(e) => e.preventDefault()}
                                className="capitalize focus:bg-white/10 focus:text-white"
                            >
                                {p.replace('_', ' ')}
                            </DropdownMenuCheckboxItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            )}

            <div className="ml-auto text-xs text-muted-foreground">
                Showing {totalResults} results
            </div>
        </div>
    );
}
