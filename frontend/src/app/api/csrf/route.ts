import { NextResponse } from "next/server";
import { cookies } from "next/headers";

function randomToken() {
    return crypto.randomUUID();
}

export async function GET() {
    const token = randomToken();
    const cookieStore = await cookies();

    cookieStore.set("csrfToken", token, {
        httpOnly: false,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: 60 * 10, // 10 mins
    });

    return NextResponse.json({ csrfToken: token });
}
