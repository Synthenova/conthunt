import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { adminAuth } from "@/lib/firebaseAdmin";

export async function POST(req: Request) {
    const cookieStore = await cookies();
    const csrfCookie = cookieStore.get("csrfToken")?.value;

    const csrfHeader = req.headers.get("x-csrf-token") || "";
    const { idToken } = await req.json();

    // Minimal CSRF check (double-submit). Firebase recommends CSRF protection.
    if (!csrfCookie || !csrfHeader || csrfCookie !== csrfHeader) {
        console.error("CSRF Failed:", { csrfCookie, csrfHeader });
        return NextResponse.json({ error: "CSRF check failed" }, { status: 401 });
    }

    try {
        // 5 days
        const expiresInMs = 1000 * 60 * 60 * 24 * 5;

        // Optional hardening: only allow session cookie if user signed in recently (auth_time).
        // Firebase docs show checking auth_time before createSessionCookie.
        const decoded = await adminAuth.verifyIdToken(idToken);
        const nowSec = Date.now() / 1000;
        if (nowSec - decoded.auth_time > 5 * 60) {
            console.error("Recent sign-in required:", { nowSec, authTime: decoded.auth_time });
            return NextResponse.json({ error: "Recent sign-in required" }, { status: 401 });
        }

        const sessionCookie = await adminAuth.createSessionCookie(idToken, {
            expiresIn: expiresInMs,
        });

        console.log("Session cookie created successfully, setting cookie...");

        cookieStore.set("session", sessionCookie, {
            httpOnly: true,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
            path: "/",
            maxAge: expiresInMs / 1000,
        });

        // clear csrf token after use
        cookieStore.set("csrfToken", "", { path: "/", maxAge: 0 });

        return NextResponse.json({ status: "ok" });
    } catch (error) {
        console.error("Session login error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}
