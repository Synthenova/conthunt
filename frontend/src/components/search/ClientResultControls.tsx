import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuLabel,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ArrowUpDown, Calendar, Filter } from "lucide-react";

export type ClientSortOption = "default" | "views" | "likes" | "shares" | "comments" | "newest";
export type ClientDateFilter = "all" | "today" | "week" | "month";

interface ClientResultControlsProps {
    sort: ClientSortOption;
    onSortChange: (val: ClientSortOption) => void;
    dateFilter: ClientDateFilter;
    onDateFilterChange: (val: ClientDateFilter) => void;
    totalResults: number;
}

export function ClientResultControls({
    sort,
    onSortChange,
    dateFilter,
    onDateFilterChange,
    totalResults
}: ClientResultControlsProps) {
    if (totalResults === 0) return null;

    const sortLabels: Record<ClientSortOption, string> = {
        default: "Default API Sort",
        views: "Most Viewed",
        likes: "Most Liked",
        shares: "Most Shared",
        comments: "Most Commented",
        newest: "Newest First"
    };

    const filterLabels: Record<ClientDateFilter, string> = {
        all: "Any Date",
        today: "Today",
        week: "This Week",
        month: "This Month"
    };

    return (
        <div className="flex items-center gap-2 py-2 px-1">
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 gap-2 bg-white/5 border border-white/10 text-xs">
                        <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Sort Results:</span>
                        <span className="font-medium text-white">{sortLabels[sort]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                    <DropdownMenuLabel>Sort Results By</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuRadioGroup value={sort} onValueChange={(val) => onSortChange(val as ClientSortOption)}>
                        {Object.entries(sortLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key}>
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 gap-2 bg-white/5 border border-white/10 text-xs">
                        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Filter Results:</span>
                        <span className="font-medium text-white">{filterLabels[dateFilter]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                    <DropdownMenuLabel>Filter Results By Date</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuRadioGroup value={dateFilter} onValueChange={(val) => onDateFilterChange(val as ClientDateFilter)}>
                        {Object.entries(filterLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key}>
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            <div className="ml-auto text-xs text-muted-foreground">
                Showing {totalResults} results
            </div>
        </div>
    );
}
