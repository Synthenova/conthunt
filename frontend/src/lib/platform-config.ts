
export const PLATFORM_CONFIG: Record<string, PlatformConfig> = {
    tiktok_top: {
        label: "TikTok Top",
        filters: [
            {
                key: "publish_time",
                label: "Date Posted",
                type: "select",
                options: [
                    { label: "All Time", value: "all-time" }, // Default: all
                    { label: "Yesterday", value: "yesterday" },
                    { label: "This Week", value: "this-week" },
                    { label: "This Month", value: "this-month" },
                    { label: "Last 3 Months", value: "last-3-months" },
                    { label: "Last 6 Months", value: "last-6-months" },
                ]
            },
            {
                key: "region",
                label: "Region",
                type: "select",
                options: [
                    { label: "United States (US)", value: "US" },
                    { label: "United Kingdom (GB)", value: "GB" },
                    { label: "France (FR)", value: "FR" },
                    { label: "Canada (CA)", value: "CA" },
                    { label: "Australia (AU)", value: "AU" }
                ]
            }
        ],
        sorts: [
            { key: "relevance", label: "Relevance" },
            { key: "most-liked", label: "Most Liked" },
            { key: "date-posted", label: "Date Posted" },
            { key: "client:views", label: "Most Viewed (Client)" }
        ]
    },
    youtube: {
        label: "YouTube Shorts",
        filters: [], // Shorts filter is hardcoded in backend, other filters don't work with it
        sorts: []    // Sort options don't work with filter param
    },
    instagram_reels: {
        label: "Instagram Reels",
        filters: [], // Instagram typically has limited public search filters via these scrapers
        sorts: []
    },
    tiktok_keyword: {
        label: "TikTok Keyword",
        filters: [
            {
                key: "publish_time",
                label: "Date Posted",
                type: "select",
                options: [
                    { label: "All Time", value: "0" },
                    { label: "Yesterday", value: "1" },
                    { label: "This Week", value: "7" },
                    { label: "This Month", value: "30" },
                    { label: "Last 3 Months", value: "90" },
                    { label: "Last 6 Months", value: "180" },
                ]
            },
            {
                key: "sort_type",
                label: "Sort By",
                type: "select", // Some APIs treat sort as a filter param or sort param
                options: [
                    { label: "Relevance", value: "0" },
                    { label: "Most Liked", value: "1" },
                    { label: "Newest", value: "2" },
                ]
            }
        ],
        sorts: [] // Handled via filter 'sort_type' for this specific endpoint usually, but we'll normalize if possible.
    }
};

export interface PlatformConfig {
    label: string;
    filters: FilterConfig[];
    sorts: SortOption[];
}

export interface FilterConfig {
    key: string;
    label: string;
    type: "select" | "text" | "number";
    options?: { label: string; value: string }[];
}

export interface SortOption {
    key: string;
    label: string;
}
