"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { useSearchStore } from "@/lib/store";

export function NavigationReset() {
    const pathname = usePathname();
    const prevPathnameRef = useRef(pathname);

    useEffect(() => {
        // Only run if the pathname has actually changed, not just on mount
        // Although on mount for a full reload the store is empty anyway.
        // But if we are navigating, we want to clear.

        if (prevPathnameRef.current !== pathname) {
            useSearchStore.getState().setActiveSearchId(null);
            useSearchStore.getState().clearSelection();
            prevPathnameRef.current = pathname;
        }
    }, [pathname]);

    return null;
}
