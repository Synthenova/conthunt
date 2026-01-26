import { NextResponse } from "next/server";
import { cookies } from "next/headers";

function randomToken() {
    return crypto.randomUUID();
}

export async function GET(req: Request) {
    const token = randomToken();
    const cookieStore = await cookies();

    // Auto-detect based on protocol (Ngrok/Prod=HTTPS->None, Localhost=HTTP->Lax)
    const isSecure = req.url.startsWith("https") || req.headers.get("x-forwarded-proto") === "https";

    cookieStore.set("csrfToken", token, {
        httpOnly: false,
        sameSite: isSecure ? "none" : "lax",
        secure: isSecure,
        path: "/",
        maxAge: 60 * 10, // 10 mins
    });

    return NextResponse.json({ csrfToken: token });
}
