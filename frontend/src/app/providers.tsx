"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useUser } from "@/hooks/useUser";
import { identifyPostHog } from "@/lib/telemetry/posthog";
import PostHogPageview from "./PostHogPageview";

function TelemetryBootstrap() {
    const { profile } = useUser();

    // initPostHog is handled by PostHogPageview now

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
