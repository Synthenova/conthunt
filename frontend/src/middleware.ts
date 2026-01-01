import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
    "/login",
    "/api/csrf",
    "/api/sessionLogin",
    "/api/sessionLogout",
    "/images",
];

export function middleware(req: NextRequest) {
    const { pathname } = req.nextUrl;

    // Allow Next internals + static
    if (
        pathname.startsWith("/_next") ||
        pathname.startsWith("/favicon") ||
        pathname.startsWith("/public")
    ) {
        return NextResponse.next();
    }

    // Allow public paths
    if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(p))) {
        return NextResponse.next();
    }

    // Auth wall
    const session = req.cookies.get("session")?.value;
    if (!session) {
        console.log("Middleware: No session cookie found. Redirecting to /login. Path:", pathname);
        const url = req.nextUrl.clone();
        url.pathname = "/login";
        return NextResponse.redirect(url);
    }

    console.log("Middleware: Session found. Allowing access to:", pathname);
    return NextResponse.next();
}

// Apply to everything (except the exclusions above)
export const config = {
    matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
