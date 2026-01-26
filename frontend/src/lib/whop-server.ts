import "server-only";
import WhopSDK from "@whop/sdk";

export function getWhopSdk() {
    const apiKey = process.env.WHOP_API_KEY;
    if (!apiKey) {
        throw new Error("WHOP_API_KEY is missing");
    }

    return new WhopSDK({
        apiKey,
        appID: process.env.NEXT_PUBLIC_WHOP_APP_ID,
    });
}
