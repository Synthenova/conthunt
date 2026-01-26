"use client";

import { useEffect, useState } from "react";
import firebase, { auth } from "@/lib/firebaseClient";
import { BACKEND_URL } from "@/lib/api";
import { GrainGradient } from "@paper-design/shaders-react";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
    const [isLoggingIn, setIsLoggingIn] = useState(false);
    const [loading, setLoading] = useState(false);
    const [emailLoading, setEmailLoading] = useState(false);
    const [resetLoading, setResetLoading] = useState(false);
    const [error, setError] = useState("");
    const [info, setInfo] = useState("");
    const [showEmailForm, setShowEmailForm] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleGoogleLogin = async () => {
        try {
            setLoading(true);
            setError("");
            const provider = new firebase.auth.GoogleAuthProvider();
            await auth.signInWithPopup(provider);
        } catch (e: any) {
            console.error("Google login error", e);
            setError(e.message);
            setLoading(false);
        }
    };

    const handleEmailSignIn = async () => {
        try {
            setEmailLoading(true);
            setError("");
            setInfo("");
            if (!email || !password) {
                setError("Please enter email and password.");
                return;
            }
            await auth.signInWithEmailAndPassword(email, password);
        } catch (e: any) {
            console.error("Email sign-in error", e);
            setError(e.message);
        } finally {
            setEmailLoading(false);
        }
    };

    const handleEmailSignUp = async () => {
        try {
            setEmailLoading(true);
            setError("");
            setInfo("");
            if (!email || !password) {
                setError("Please enter email and password.");
                return;
            }
            const credential = await auth.createUserWithEmailAndPassword(email, password);
            const user = credential.user;
            if (user) {
                await user.sendEmailVerification({
                    url: `${window.location.origin}/login`,
                });
            }
            setInfo("Verification email sent. Please verify and then sign in.");
            await auth.signOut();
        } catch (e: any) {
            console.error("Email sign-up error", e);
            setError(e.message);
        } finally {
            setEmailLoading(false);
        }
    };

    const handlePasswordReset = async () => {
        try {
            setResetLoading(true);
            setError("");
            setInfo("");
            if (!email) {
                setError("Enter your email to reset your password.");
                return;
            }
            await auth.sendPasswordResetEmail(email, {
                url: `${window.location.origin}/login`,
            });
            setInfo("Password reset email sent.");
        } catch (e: any) {
            console.error("Password reset error", e);
            setError(e.message);
        } finally {
            setResetLoading(false);
        }
    };

    useEffect(() => {
        let cancelled = false;

        // Listen for auth state changes (handles popup, redirect, and existing sessions)
        const unsubscribe = auth.onAuthStateChanged(async (user) => {
            if (cancelled) return;
            if (user) {
                const hasPasswordProvider = user.providerData.some(
                    (provider) => provider?.providerId === "password",
                );
                if (hasPasswordProvider && !user.emailVerified) {
                    setInfo("Please verify your email to continue.");
                    await auth.signOut();
                    setIsLoggingIn(false);
                    return;
                }
                setIsLoggingIn(true);
                console.log("AuthStateChanged: User detected. Getting ID Token...");

                try {
                    let idToken = await user.getIdToken();

                    // 1. Sync with backend (creates user in DB, sets custom claims)
                    const backendUrl = BACKEND_URL;
                    console.log("Syncing with backend...");
                    const syncResp = await fetch(`${backendUrl}/v1/auth/sync`, {
                        method: "POST",
                        headers: {
                            "Authorization": `Bearer ${idToken}`,
                            "Content-Type": "application/json",
                        },
                    });

                    if (!syncResp.ok) {
                        const err = await syncResp.json();
                        console.error("Backend sync failed:", err);
                        alert("Failed to sync with backend. Please try again.");
                        setIsLoggingIn(false);
                        return;
                    }

                    const syncData = await syncResp.json();
                    console.log("Backend sync success:", syncData);

                    // 2. If claims were set, refresh the token to get new claims
                    if (syncData.needs_token_refresh) {
                        console.log("Refreshing token to get new claims...");
                        idToken = await user.getIdToken(true);
                    }

                    // 3. Get CSRF token for session login
                    const csrfReq = await fetch("/api/csrf");
                    const { csrfToken } = await csrfReq.json();

                    // 4. Create session cookie (Next.js API route)
                    console.log("Sending ID Token to /api/sessionLogin...");
                    const resp = await fetch("/api/sessionLogin", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRF-Token": csrfToken,
                        },
                        body: JSON.stringify({ idToken }),
                    });

                    console.log("Session login response:", resp.status);

                    if (resp.ok) {
                        console.log("Session login success. Redirecting to /app");
                        window.location.href = "/app";
                        return;
                    } else {
                        const err = await resp.json();
                        console.error("Session login failed:", err);

                        if (err.error === "Recent sign-in required") {
                            console.log("Session too old, singing out to force refresh...");
                            await auth.signOut();
                            setIsLoggingIn(false);
                            return;
                        }

                        alert("Session login failed. Please try again.");
                        setIsLoggingIn(false);
                    }
                } catch (e) {
                    console.error("Error during session exchange:", e);
                    setIsLoggingIn(false);
                }
            } else {
                setIsLoggingIn(false);
            }
        });

        return () => {
            cancelled = true;
            unsubscribe();
        };
    }, []);

    if (isLoggingIn) {
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
                <h1 className="relative z-10 text-xl font-bold text-white animate-pulse">Logging you in...</h1>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 flex items-center bg-black">
            {/* GrainGradient Background */}
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

            {/* Login Content */}
            <div className="relative z-10 flex flex-col items-center gap-6 ml-[8%] md:ml-[12%] w-full max-w-sm">
                {/* Heading */}
                <h1 className="text-xl md:text-2xl tracking-[0.25em] text-white font-light whitespace-nowrap">
                    LOG IN TO <span className="font-bold">CONTHUNT</span>
                </h1>

                {/* Error Message */}
                {error && (
                    <div className="w-full p-3 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl text-center">
                        {error}
                    </div>
                )}

                {info && (
                    <div className="w-full p-3 text-sm text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-center">
                        {info}
                    </div>
                )}

                {/* {!showEmailForm ? (
                    <button
                        type="button"
                        onClick={() => setShowEmailForm(true)}
                        className="glass-button w-fit py-4 px-12 text-base font-medium text-white/90 tracking-wide mt-2 hover:text-white transition-colors"
                    >
                        sign in with email
                    </button>
                ) : (
                    <div className="w-full flex flex-col gap-4 animate-in">
                        <input
                            type="email"
                            autoComplete="email"
                            placeholder="Email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            className="w-full rounded-full bg-white/5 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                        />
                        <input
                            type="password"
                            autoComplete="current-password"
                            placeholder="Password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="w-full rounded-full bg-white/5 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                        />
                        <div className="flex w-full items-center gap-3">
                            <button
                                type="button"
                                onClick={handleEmailSignIn}
                                disabled={emailLoading}
                                className="glass-button flex-1 py-3 text-sm font-medium text-white/90 tracking-wide hover:text-white transition-colors disabled:opacity-60"
                            >
                                {emailLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "sign in"}
                            </button>
                            <button
                                type="button"
                                onClick={handleEmailSignUp}
                                disabled={emailLoading}
                                className="glass-button-white flex-1 py-3 text-sm font-medium tracking-wide disabled:opacity-60"
                            >
                                {emailLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "sign up"}
                            </button>
                        </div>
                        <button
                            type="button"
                            onClick={handlePasswordReset}
                            disabled={resetLoading}
                            className="text-xs text-white/60 hover:text-white transition-colors"
                        >
                            {resetLoading ? "sending reset email..." : "forgot password?"}
                        </button>
                    </div>
                )} */}

                {/* Google Sign-in Button */}
                <button
                    type="button"
                    onClick={handleGoogleLogin}
                    disabled={loading}
                    className="glass-button w-fit py-4 px-12 text-base font-medium text-white/90 tracking-wide mt-2 hover:text-white transition-colors"
                >
                    {loading ? (
                        <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                    ) : (
                        <div className="flex items-center gap-3">
                            <span>sign in with</span>
                            <svg className="h-5 w-5" viewBox="0 0 24 24">
                                <path
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    fill="currentColor"
                                />
                                <path
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    fill="currentColor"
                                />
                                <path
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z"
                                    fill="currentColor"
                                />
                                <path
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 2.09 3.99 4.56 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    fill="currentColor"
                                />
                            </svg>
                        </div>
                    )}
                </button>
            </div>
        </div>
    );
}
