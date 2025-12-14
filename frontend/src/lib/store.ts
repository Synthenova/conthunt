import { create } from 'zustand';

interface SearchInputs {
    instagram_reels: boolean;
    tiktok_keyword: boolean;
    tiktok_top: boolean;
    youtube: boolean;
    pinterest: boolean;
}

// ... existing code ...
interface SearchState {
    query: string;
    limit: number;
    platformInputs: SearchInputs;

    // keys: platform name (e.g. 'tiktok_top'). values: object with filterKey: value
    filters: Record<string, Record<string, string>>;
    // keys: platform name. values: sort key
    sortBy: Record<string, string>;

    setQuery: (q: string) => void;
    setLimit: (n: number) => void;
    togglePlatform: (key: keyof SearchInputs) => void;
    setAllPlatforms: (enabled: boolean) => void;

    setFilter: (platform: string, key: string, value: string) => void;
    setSort: (platform: string, sortKey: string) => void;
}

export const useSearchStore = create<SearchState>((set) => ({
    query: '',
    limit: 5,
    platformInputs: {
        instagram_reels: true,
        tiktok_keyword: true,
        tiktok_top: false,
        youtube: true,
        pinterest: true,
    },
    filters: {},
    sortBy: {},

    setQuery: (query) => set({ query }),
    setLimit: (limit) => set({ limit }),
    togglePlatform: (key) => set((state) => ({
        platformInputs: {
            ...state.platformInputs,
            [key]: !state.platformInputs[key]
        }
    })),
    setAllPlatforms: (enabled) => set({
        platformInputs: {
            instagram_reels: enabled,
            tiktok_keyword: enabled,
            tiktok_top: enabled,
            youtube: enabled,
            pinterest: enabled,
        }
    }),
    setFilter: (platform, key, value) => set((state) => ({
        filters: {
            ...state.filters,
            [platform]: {
                ...(state.filters[platform] || {}),
                [key]: value
            }
        }
    })),
    setSort: (platform, sortKey) => set((state) => ({
        sortBy: {
            ...state.sortBy,
            [platform]: sortKey
        }
    }))
}));
