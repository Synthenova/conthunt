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
export type ClientDateFilter = "all" | "today" | "week" | "month" | "six_months" | "year";

interface BoardFilterBarProps {
    sort: ClientSortOption;
    onSortChange: (val: ClientSortOption) => void;
    dateFilter: ClientDateFilter;
    onDateFilterChange: (val: ClientDateFilter) => void;
    platforms: string[];
    selectedPlatforms: string[];
    onPlatformsChange: (val: string[]) => void;
}

export function BoardFilterBar({
    sort,
    onSortChange,
    dateFilter,
    onDateFilterChange,
    platforms,
    selectedPlatforms,
    onPlatformsChange,
}: BoardFilterBarProps) {

    const sortLabels: Record<ClientSortOption, string> = {
        default: "Relevancy",
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
        month: "This Month",
        six_months: "Past 6 Months",
        year: "Past Year"
    };

    return (
        <div className="flex items-center gap-2">
            <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="glass-button h-9 px-4 gap-2 text-xs font-medium border border-white/10 hover:border-white/20">
                        <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Sort:</span>
                        <span className="text-white">{sortLabels[sort]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-zinc-900 border-white/10 text-white min-w-[180px]">
                    <DropdownMenuLabel>Sort Results By</DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuRadioGroup value={sort} onValueChange={(val) => {
                        onSortChange(val as ClientSortOption);
                    }}>
                        {Object.entries(sortLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key} className="focus:bg-white/10 focus:text-white cursor-pointer">
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="glass-button h-9 px-4 gap-2 text-xs font-medium border border-white/10 hover:border-white/20">
                        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                        <span className="text-muted-foreground">Date:</span>
                        <span className="text-white">{filterLabels[dateFilter]}</span>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-zinc-900 border-white/10 text-white min-w-[180px]">
                    <DropdownMenuLabel>Filter By Date</DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuRadioGroup value={dateFilter} onValueChange={(val) => {
                        onDateFilterChange(val as ClientDateFilter);
                    }}>
                        {Object.entries(filterLabels).map(([key, label]) => (
                            <DropdownMenuRadioItem key={key} value={key} className="focus:bg-white/10 focus:text-white cursor-pointer">
                                {label}
                            </DropdownMenuRadioItem>
                        ))}
                    </DropdownMenuRadioGroup>
                </DropdownMenuContent>
            </DropdownMenu>

            {platforms.length > 0 && (
                <DropdownMenu modal={false}>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="glass-button h-9 px-4 gap-2 text-xs font-medium border border-white/10 hover:border-white/20">
                            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="text-muted-foreground">Platform:</span>
                            <span className="text-white">
                                {selectedPlatforms.length === 0 || selectedPlatforms.length === platforms.length
                                    ? "All"
                                    : `${selectedPlatforms.length} selected`}
                            </span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        align="end"
                        className="min-w-[180px] bg-zinc-900 border-white/10 text-white"
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
                                className="capitalize focus:bg-white/10 focus:text-white cursor-pointer"
                            >
                                {p.replace('_', ' ')}
                            </DropdownMenuCheckboxItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>
            )}
        </div>
    );
}
