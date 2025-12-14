import { create } from 'zustand';

interface SearchInputs {
    instagram_reels: boolean;
    tiktok_keyword: boolean;
    tiktok_top: boolean;
    youtube: boolean;
    pinterest: boolean;
}

interface SearchState {
    query: string;
    limit: number;
    platformInputs: SearchInputs;

    // keys: platform name (e.g. 'tiktok_top'). values: object with filterKey: value
    filters: Record<string, Record<string, string>>;
    // keys: platform name. values: sort key
    sortBy: Record<string, string>;

    // Selection state for adding to boards
    selectedItems: string[];
    toggleItemSelection: (id: string) => void;
    clearSelection: () => void;
    selectAll: (ids: string[]) => void;
    isItemSelected: (id: string) => boolean;

    setQuery: (q: string) => void;
    setLimit: (n: number) => void;
    togglePlatform: (key: keyof SearchInputs) => void;
    setAllPlatforms: (enabled: boolean) => void;

    setFilter: (platform: string, key: string, value: string) => void;
    setSort: (platform: string, sortKey: string) => void;
}

export const useSearchStore = create<SearchState>((set, get) => ({
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

    // Selection state
    selectedItems: [],
    toggleItemSelection: (id) => set((state) => ({
        selectedItems: state.selectedItems.includes(id)
            ? state.selectedItems.filter(i => i !== id)
            : [...state.selectedItems, id]
    })),
    clearSelection: () => set({ selectedItems: [] }),
    selectAll: (ids) => set({ selectedItems: ids }),
    isItemSelected: (id) => get().selectedItems.includes(id),

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
