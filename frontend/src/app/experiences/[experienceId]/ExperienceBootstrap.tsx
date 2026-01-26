"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { signInWithCustomToken } from "firebase/auth";
import { auth } from "@/lib/firebaseClient";
import { GrainGradient } from "@paper-design/shaders-react";
import { Loader2 } from "lucide-react";

export default function ExperienceBootstrap({ experienceId }: { experienceId: string }) {
    const router = useRouter();
    const [status, setStatus] = useState("Initializing Whop session...");

    const initiated = useRef(false);

    useEffect(() => {
        if (initiated.current) return;
        initiated.current = true;

        let mounted = true;

        (async () => {
            try {
                // IMPORTANT: same-origin request so x-whop-user-token is included automatically by the browser context
                const res = await fetch("/api/auth/whop-exchange", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ experienceId }),
                });

                if (!mounted) return;

                if (!res.ok) {
                    console.error("Whop exchange failed", res.status);
                    setStatus("Authentication failed. Please refresh.");
                    // router.replace("/not-authorized"); 
                    return;
                }

                const data = await res.json();

                setStatus("Signing in...");
                await signInWithCustomToken(auth, data.firebase_custom_token);

                // --- NEW: Create Session Cookie for Middleware Access ---
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
            } catch (err) {
                console.error("ExperienceBootstrap error:", err);
                if (mounted) setStatus("Error occurred. Please try again.");
            }
        })();

        return () => {
            mounted = false;
        }
    }, [experienceId, router]);

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
                <Loader2 className="h-8 w-8 animate-spin text-white" />
                <h1 className="text-xl font-medium text-white animate-pulse">{status}</h1>
            </div>
        </div>
    );
}
