import type { ClientDateFilter, ClientSortOption } from "@/components/search/ClientResultControls";

export interface ClientFilters {
    sort?: ClientSortOption;
    dateFilter?: ClientDateFilter;
    platforms?: string[];
}

type PlatformInputs = Record<string, Record<string, any>>;

const TIKTOK_SORT_MAP: Record<ClientSortOption, string | null> = {
    default: "relevance",
    views: "most-liked",
    likes: "most-liked",
    shares: "most-liked",
    comments: "most-liked",
    newest: "date-posted",
};

const TIKTOK_DATE_MAP: Record<ClientDateFilter, string | null> = {
    all: null,
    today: "this-week",
    yesterday: "yesterday",
    week: "this-week",
    month: "this-month",
    three_months: "last-3-months",
    six_months: "last-6-months",
    year: "all-time",
};

const PLATFORM_SLUGS = {
    tiktok: ["tiktok_top", "tiktok_keyword"],
    instagram: ["instagram_reels"],
    youtube: ["youtube"],
};

function resolvePlatformSlugs(platforms?: string[]) {
    const selected = (platforms || [])
        .map((p) => p.toLowerCase())
        .filter(Boolean);
    if (!selected.length) {
        return Object.values(PLATFORM_SLUGS).flat();
    }
    return selected.flatMap((platform) => {
        if (platform.includes("tiktok")) return PLATFORM_SLUGS.tiktok;
        if (platform.includes("instagram")) return PLATFORM_SLUGS.instagram;
        if (platform.includes("youtube")) return PLATFORM_SLUGS.youtube;
        return [];
    });
}

export function mapClientFiltersToPlatformInputs(filters: ClientFilters): PlatformInputs {
    const inputs: PlatformInputs = {};
    const slugs = resolvePlatformSlugs(filters.platforms);
    const tiktokSort = TIKTOK_SORT_MAP[filters.sort ?? "default"];
    const tiktokDate = TIKTOK_DATE_MAP[filters.dateFilter ?? "all"];

    for (const slug of slugs) {
        if (slug === "tiktok_top") {
            inputs[slug] = {};
            if (tiktokDate) inputs[slug].publish_time = tiktokDate;
            if (tiktokSort) inputs[slug].sort_by = tiktokSort;
        } else if (slug === "tiktok_keyword") {
            inputs[slug] = {};
            if (tiktokDate) inputs[slug].date_posted = tiktokDate;
            if (tiktokSort) inputs[slug].sort_by = tiktokSort;
        } else if (slug === "youtube") {
            inputs[slug] = { filter: "shorts" };
        } else if (slug === "instagram_reels") {
            inputs[slug] = {};
        }
    }

    return inputs;
}

export function formatFiltersFence(filters: ClientFilters): string {
    const tokens: string[] = ["filters"];
    const inputs = mapClientFiltersToPlatformInputs(filters);
    Object.entries(inputs).forEach(([platform, params]) => {
        Object.entries(params).forEach(([key, value]) => {
            if (value === undefined || value === null || value === "") return;
            tokens.push(`${platform}.${key}=${value}`);
        });
    });

    return `\`\`\`${tokens.join(" | ")}\`\`\``;
}
