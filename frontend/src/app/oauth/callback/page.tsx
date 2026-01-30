"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { signInWithCustomToken } from "firebase/auth";
import { auth } from "@/lib/firebaseClient";
import { GrainGradient } from "@paper-design/shaders-react";
import { Loader2 } from "lucide-react";
import { handleWhopCallback } from "@/lib/whop-oauth";

export default function OAuthCallbackPage() {
    const router = useRouter();
    const [status, setStatus] = useState("Processing OAuth callback...");
    const [error, setError] = useState("");
    const initiated = useRef(false);

    useEffect(() => {
        if (initiated.current) return;
        initiated.current = true;

        let mounted = true;

        (async () => {
            try {
                // Extract params from URL IMMEDIATELY before HMR can cause issues
                const urlParams = new URLSearchParams(window.location.search);
                const code = urlParams.get("code");
                const state = urlParams.get("state");
                const error = urlParams.get("error");

                // Check for OAuth errors from Whop
                if (error) {
                    const errorDesc = urlParams.get("error_description") || "";
                    throw new Error(`OAuth error: ${error} - ${errorDesc}`);
                }

                if (!code || !state) {
                    throw new Error("No authorization code in URL - OAuth flow may have failed or was already processed");
                }

                // IMMEDIATELY clear the URL to prevent HMR from reprocessing
                window.history.replaceState({}, "", "/oauth/callback");

                const clientId = process.env.NEXT_PUBLIC_WHOP_APP_ID;
                if (!clientId) {
                    throw new Error("Whop App ID not configured");
                }

                const redirectUri = `${window.location.origin}/oauth/callback`;

                console.log("[OAuth] Starting callback handling", { clientId, redirectUri, code: code.substring(0, 10) + "..." });

                // Exchange code for tokens (URL already cleared, safe from HMR)
                setStatus("Exchanging authorization code...");
                const tokens = await handleWhopCallback(clientId, redirectUri, code, state);

                if (!mounted) return;

                // Send access token to backend
                setStatus("Authenticating with backend...");
                const res = await fetch("/v1/auth/whop-exchange/oauth", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ access_token: tokens.access_token }),
                });

                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(err.detail || `Backend auth failed: ${res.status}`);
                }

                const data = await res.json();

                // Sign in with Firebase custom token
                setStatus("Signing in...");
                await signInWithCustomToken(auth, data.firebase_custom_token);

                // Get ID token for session
                setStatus("Finalizing session...");
                const getIdTokenWithRetry = async () => {
                    for (let attempt = 0; attempt < 3; attempt += 1) {
                        const user = auth.currentUser;
                        if (user) {
                            const token = await user.getIdToken(true);
                            if (token) return token;
                        }
                        await new Promise((resolve) => setTimeout(resolve, 200 * (attempt + 1)));
                    }
                    return null;
                };

                const idToken = await getIdTokenWithRetry();
                if (!idToken) {
                    throw new Error("Missing ID token after sign-in");
                }

                // Get CSRF Token
                const csrfReq = await fetch("/api/csrf");
                const { csrfToken } = await csrfReq.json();

                // Exchange for Session Cookie
                const sessionRes = await fetch("/api/sessionLogin", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRF-Token": csrfToken,
                    },
                    body: JSON.stringify({ idToken }),
                });

                if (!sessionRes.ok) {
                    throw new Error("Session creation failed");
                }

                router.replace("/app");
            } catch (err: any) {
                console.error("OAuth callback error:", err);
                if (mounted) {
                    setError(err.message || "Authentication failed");
                    setStatus("");
                }
            }
        })();

        return () => {
            mounted = false;
        };
    }, [router]);

    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black">
            <GrainGradient
                style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
                colors={["#7300ff", "#eba8ff", "#00bfff", "#2b00ff"]}
                colorBack="#000000"
                softness={0.67}
                intensity={0.26}
                noise={0.24}
                shape="corners"
                speed={1}
                rotation={128}
                offsetX={0.22}
                offsetY={-0.04}
            />
            <div className="relative z-10 flex flex-col items-center gap-4">
                {error ? (
                    <>
                        <div className="p-4 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl text-center max-w-md">
                            {error}
                        </div>
                        <button
                            onClick={() => router.push("/login")}
                            className="text-white/70 hover:text-white text-sm"
                        >
                            Return to login
                        </button>
                    </>
                ) : (
                    <>
                        <Loader2 className="h-8 w-8 animate-spin text-white" />
                        <h1 className="text-xl font-medium text-white animate-pulse">{status}</h1>
                    </>
                )}
            </div>
        </div>
    );
}
