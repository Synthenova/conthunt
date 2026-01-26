import WhopSDK from "@whop/sdk";

// Initialize the Whop SDK
// The SDK automatically detects the environment (iframe) and handles token retrieval
export const whopsdk = new WhopSDK({
    appID: process.env.NEXT_PUBLIC_WHOP_APP_ID,
});
