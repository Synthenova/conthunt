import { useCallback, useEffect, useRef, useState } from "react";

const MEDIA_BASE_VH = 0.6;
const MEDIA_MIN_HEIGHT_PX = 320;
const MEDIA_MAX_HEIGHT_PX = 560;
const MEDIA_COLLAPSE_THRESHOLD = 1;
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
    const scrollRafRef = useRef<number | null>(null);

    const setHeightFromBase = useCallback((collapsed: boolean) => {
        const baseHeight = baseMediaHeightRef.current;
        if (!baseHeight) return;
        const ratio = collapsed ? MEDIA_COLLAPSE_RATIO : 1;
        setMediaHeight(Math.round(baseHeight * ratio));
    }, []);

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

    useEffect(() => {
        if (!isOpen) return;
        setHeightFromBase(isMediaCollapsed);
    }, [isOpen, isMediaCollapsed, setHeightFromBase]);

    useEffect(() => {
        if (!isOpen || !item) return;
        setIsMediaCollapsed(false);
    }, [isOpen, item]);

    const handleViewportScroll = useCallback(() => {
        if (scrollRafRef.current !== null) return;
        scrollRafRef.current = requestAnimationFrame(() => {
            scrollRafRef.current = null;
            const viewport = viewportRef.current;
            if (!viewport) return;
            const shouldCollapse = viewport.scrollTop > MEDIA_COLLAPSE_THRESHOLD;
            setIsMediaCollapsed((prev) => (prev === shouldCollapse ? prev : shouldCollapse));
        });
    }, []);

    const handleViewportScrollEvent = useCallback(() => {
        handleViewportScroll();
    }, [handleViewportScroll]);

    return {
        viewportRef,
        mediaHeight,
        isMediaCollapsed,
        handleViewportScrollEvent,
    };
}
