"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useUser } from "@/hooks/useUser";
import { identifyPostHog } from "@/lib/telemetry/posthog";
import { trackSessionDurationMs, trackSessionStarted } from "@/lib/telemetry/tracking";
import PostHogPageview from "./PostHogPageview";

function TelemetryBootstrap() {
    const { profile } = useUser();
    const [sessionStartedAt] = useState<number>(() => Date.now());

    // initPostHog is handled by PostHogPageview now

    useEffect(() => {
        trackSessionStarted();

        const reportSessionDuration = () => {
            const durationMs = Date.now() - sessionStartedAt;
            if (durationMs > 0) {
                trackSessionDurationMs(durationMs);
            }
        };

        const handleVisibility = () => {
            if (document.visibilityState === "hidden") {
                reportSessionDuration();
            }
        };

        window.addEventListener("pagehide", reportSessionDuration);
        document.addEventListener("visibilitychange", handleVisibility);

        return () => {
            window.removeEventListener("pagehide", reportSessionDuration);
            document.removeEventListener("visibilitychange", handleVisibility);
            reportSessionDuration();
        };
    }, [sessionStartedAt]);

    useEffect(() => {
        if (!profile?.id) {
            return;
        }

        identifyPostHog(profile.id, {
            plan: profile.role || "free",
            role: profile.role || "free",
        });
    }, [profile?.id, profile?.role]);

    return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60 * 1000,
                refetchOnWindowFocus: false,
            },
        }
    }));

    return (
        <QueryClientProvider client={queryClient}>
            <TelemetryBootstrap />
            <PostHogPageview />
            {children}
        </QueryClientProvider>
    );
}
