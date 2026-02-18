"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, Suspense } from "react";
import { capturePostHog } from "@/lib/telemetry/posthog";

function PostHogPageviewInner() {
    const pathname = usePathname();
    const searchParams = useSearchParams();

    useEffect(() => {
        if (pathname) {
            let url = window.origin + pathname;
            if (searchParams.toString()) {
                url = url + `?${searchParams.toString()}`;
            }
            capturePostHog("$pageview", {
                $current_url: url,
                $pathname: pathname,
            });
        }
    }, [pathname, searchParams]);

    return null;
}

export default function PostHogPageview() {
    return (
        <Suspense fallback={null}>
            <PostHogPageviewInner />
        </Suspense>
    );
}
