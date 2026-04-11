import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { auth } from "@/lib/firebaseClient";

const LOADING_MESSAGES = [
    "Watching your video with AI eyes...",
    "Extracting the good stuff...",
    "Finding the hooks and CTAs...",
    "Scanning for on-screen text...",
    "Analyzing engagement patterns...",
    "Decoding viral potential...",
    "Almost there, thinking hard...",
    "Crunching the content...",
    "AI brain at work...",
    "Uncovering hidden gems...",
];
const ANALYSIS_NOT_READY_MESSAGE = "Finalizing search results...";
const ANALYSIS_POLL_INTERVAL_MS = 2500;
const ANALYSIS_MAX_NOT_READY_RETRIES = 20;
const ANALYSIS_NOT_READY_STATUSES = new Set([404, 409, 425]);

interface UseContentAnalysisOptions {
    item: any | null;
    isOpen: boolean;
    analysisDisabled?: boolean;
    onAnalysisComplete?: () => void;
}

export function useContentAnalysis({ item, isOpen, analysisDisabled = false, onAnalysisComplete }: UseContentAnalysisOptions) {
    const [analyzing, setAnalyzing] = useState(false);
    const [polling, setPolling] = useState(false);
    const [checkingExisting, setCheckingExisting] = useState(false);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0]);
    const analysisNotReadyRetries = useRef(0);

    const getMediaAssetId = useCallback(() => {
        if (!item) return null;
        const videoAsset = item.assets?.find((a: any) => a.asset_type === "video");
        return videoAsset?.id || null;
    }, [item]);

    const fetchAnalysis = useCallback(async () => {
        if (!item) return null;

        const user = auth.currentUser;
        if (!user) return null;

        const mediaAssetId = getMediaAssetId();

        if (!mediaAssetId) {
            const isYouTube = item.platform === "youtube" || item.platform === "youtube_search";
            if (isYouTube) {
                throw new Error("YouTube video analysis requires a fresh search. Please search again to enable analysis.");
            }
            throw new Error("No video asset found for this content");
        }

        const token = await user.getIdToken();
        const { BACKEND_URL } = await import("@/lib/api");

        const response = await fetch(`${BACKEND_URL}/v1/video-analysis/${mediaAssetId}`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
        });

        if (ANALYSIS_NOT_READY_STATUSES.has(response.status)) {
            return { status: "not_ready" };
        }

        if (!response.ok) {
            const detail = await response.json().catch(() => null);
            throw new Error(detail?.detail || (response.status === 401 ? "Unauthorized" : "Analysis failed"));
        }

        return await response.json();
    }, [item, getMediaAssetId]);

    const fetchExistingAnalysis = useCallback(async () => {
        const user = auth.currentUser;
        if (!user) return null;

        const mediaAssetId = getMediaAssetId();
        if (!mediaAssetId) return null;

        const token = await user.getIdToken();
        const { BACKEND_URL } = await import("@/lib/api");

        const response = await fetch(`${BACKEND_URL}/v1/video-analysis/${mediaAssetId}`, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });

        if (!response.ok) return null;
        return await response.json();
    }, [getMediaAssetId]);

    useEffect(() => {
        if (!analyzing && !polling) return;

        const interval = setInterval(() => {
            setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]);
        }, 2500);

        return () => clearInterval(interval);
    }, [analyzing, polling]);

    useEffect(() => {
        if (!polling) return;

        const pollInterval = setInterval(async () => {
            try {
                const data = await fetchAnalysis();
                if (!data) return;
                setAnalysisResult(data);

                if (data?.status === "not_ready") {
                    analysisNotReadyRetries.current += 1;
                    if (analysisNotReadyRetries.current >= ANALYSIS_MAX_NOT_READY_RETRIES) {
                        setPolling(false);
                        setError("Search is still saving results. Please try again in a moment.");
                    }
                    return;
                }

                analysisNotReadyRetries.current = 0;
                if (data?.status !== "processing") {
                    setPolling(false);
                    clearInterval(pollInterval);
                    if (data?.status === "completed") {
                        onAnalysisComplete?.();
                    }
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, ANALYSIS_POLL_INTERVAL_MS);

        return () => clearInterval(pollInterval);
    }, [polling, fetchAnalysis, onAnalysisComplete]);

    useEffect(() => {
        if (isOpen && item) {
            setAnalysisResult(null);
            setError(null);
            setAnalyzing(false);
            setPolling(false);
            setCheckingExisting(false);
            analysisNotReadyRetries.current = 0;

            // Auto-fetch existing analysis if user has already accessed it (GET - no credit charge)
            if (!analysisDisabled) {
                setCheckingExisting(true);
                setLoadingMessage("Checking for existing analysis...");
                fetchExistingAnalysis()
                    .then((data) => {
                        if (data && data.status === "completed") {
                            setAnalysisResult(data);
                        }
                    })
                    .catch(() => {
                        // Silently ignore - user can manually trigger if needed
                    })
                    .finally(() => {
                        setCheckingExisting(false);
                    });
            }
        }
    }, [isOpen, item, analysisDisabled, fetchExistingAnalysis]);

    const handleAnalyze = useCallback(async () => {
        if (!item || analyzing || polling || analysisDisabled) return;

        setAnalyzing(true);
        setError(null);
        setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)]);
        analysisNotReadyRetries.current = 0;

        try {
            const data = await fetchAnalysis();
            setAnalysisResult(data);

            if (data?.status === "not_ready") {
                setLoadingMessage(ANALYSIS_NOT_READY_MESSAGE);
            }

            if (data?.status === "processing" || data?.status === "not_ready") {
                setPolling(true);
            }
        } catch (err) {
            setError("Failed to analyze video. Please try again.");
            console.error(err);
        } finally {
            setAnalyzing(false);
        }
    }, [analysisDisabled, analyzing, fetchAnalysis, item, polling]);

    return useMemo(
        () => ({
            analysisResult,
            analyzing: analyzing || checkingExisting,
            polling,
            error,
            loadingMessage,
            handleAnalyze,
        }),
        [analysisResult, analyzing, checkingExisting, polling, error, loadingMessage, handleAnalyze]
    );
}

export { ANALYSIS_NOT_READY_MESSAGE };
