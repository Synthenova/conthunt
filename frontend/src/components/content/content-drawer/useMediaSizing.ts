import { useCallback, useEffect, useRef, useState } from "react";

const MEDIA_BASE_VH = 0.6;
const MEDIA_MIN_HEIGHT_PX = 320;
const MEDIA_MAX_HEIGHT_PX = 560;
const MEDIA_COLLAPSE_RATIO = 0.5;

interface UseMediaSizingOptions {
    isOpen: boolean;
    item: any | null;
}

export function useMediaSizing({ isOpen, item }: UseMediaSizingOptions) {
    const viewportRef = useRef<HTMLDivElement>(null);
    const [mediaHeight, setMediaHeight] = useState<number | null>(null);
    const [isMediaCollapsed, setIsMediaCollapsed] = useState(false);
    const baseMediaHeightRef = useRef(0);

    const setHeightFromBase = useCallback((collapsed: boolean) => {
        const baseHeight = baseMediaHeightRef.current;
        if (!baseHeight) return;
        const ratio = collapsed ? MEDIA_COLLAPSE_RATIO : 1;
        setMediaHeight(Math.round(baseHeight * ratio));
    }, []);

    // Calculate base height on open and resize
    useEffect(() => {
        if (!isOpen) return;

        const updateBaseHeight = () => {
            const baseHeight = Math.min(
                MEDIA_MAX_HEIGHT_PX,
                Math.max(MEDIA_MIN_HEIGHT_PX, window.innerHeight * MEDIA_BASE_VH)
            );
            baseMediaHeightRef.current = baseHeight;
            setHeightFromBase(isMediaCollapsed);
        };

        updateBaseHeight();
        window.addEventListener("resize", updateBaseHeight);

        return () => {
            window.removeEventListener("resize", updateBaseHeight);
        };
    }, [isOpen, isMediaCollapsed, setHeightFromBase]);

    // Sync height when collapse state changes
    useEffect(() => {
        if (!isOpen) return;
        setHeightFromBase(isMediaCollapsed);
    }, [isOpen, isMediaCollapsed, setHeightFromBase]);

    // Reset collapse state when drawer opens or item changes
    useEffect(() => {
        if (!isOpen || !item) return;
        setIsMediaCollapsed(false);
    }, [isOpen, item]);

    // Wheel handler - called directly from ScrollArea onWheel
    const handleWheel = useCallback((e: React.WheelEvent<HTMLDivElement>) => {
        const scrollTop = viewportRef.current?.scrollTop ?? 0;

        if (e.deltaY > 0) {
            // Scrolling DOWN - collapse
            setIsMediaCollapsed(true);
        } else if (e.deltaY < 0 && scrollTop <= 5) {
            // Scrolling UP and at top - expand
            setIsMediaCollapsed(false);
        }
    }, []);

    // Touch scroll handler
    const handleScroll = useCallback(() => {
        const viewport = viewportRef.current;
        if (!viewport) return;

        if (viewport.scrollTop <= 5) {
            setIsMediaCollapsed(false);
        } else if (viewport.scrollTop > 20) {
            setIsMediaCollapsed(true);
        }
    }, []);

    return {
        viewportRef,
        mediaHeight,
        isMediaCollapsed,
        handleWheel,
        handleScroll,
    };
}
