/**
 * Whop OAuth PKCE Utilities
 * Based on Whop OAuth documentation
 */

const STORAGE_KEY = "whop_oauth_pkce";

interface PKCEParams {
    codeVerifier: string;
    state: string;
    nonce: string;
}

export interface WhopTokens {
    access_token: string;
    refresh_token: string;
    id_token?: string;
    token_type: string;
    expires_in: number;
    obtained_at: number;
}

function base64url(bytes: Uint8Array): string {
    return btoa(String.fromCharCode(...bytes))
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

function randomString(len: number): string {
    return base64url(crypto.getRandomValues(new Uint8Array(len)));
}

async function sha256(str: string): Promise<string> {
    const hash = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(str)
    );
    return base64url(new Uint8Array(hash));
}

/**
 * Start Whop OAuth flow by redirecting to Whop authorization page
 */
export async function startWhopOAuth(
    clientId: string,
    redirectUri: string,
    scope = "openid profile email"
): Promise<void> {
    const pkce: PKCEParams = {
        codeVerifier: randomString(32),
        state: randomString(16),
        nonce: randomString(16),
    };

    const codeChallenge = await sha256(pkce.codeVerifier);

    // Store PKCE params for callback verification (include challenge for debug)
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...pkce, codeChallenge }));
    console.log("[OAuth] Stored PKCE params:", {
        verifier: pkce.codeVerifier.substring(0, 10) + "...",
        challenge: codeChallenge.substring(0, 10) + "...",
        verifierLength: pkce.codeVerifier.length,
    });

    // codeChallenge already computed above

    const params = new URLSearchParams({
        response_type: "code",
        client_id: clientId,
        redirect_uri: redirectUri,
        scope,
        state: pkce.state,
        nonce: pkce.nonce,
        code_challenge: codeChallenge,
        code_challenge_method: "S256",
    });

    window.location.href = `https://api.whop.com/oauth/authorize?${params.toString()}`;
}

/**
 * Handle Whop OAuth callback - exchange code for tokens
 * IMPORTANT: Call this with code/state extracted from URL, then caller should clear URL before HMR
 */
export async function handleWhopCallback(
    clientId: string,
    redirectUri: string,
    code: string,
    state: string
): Promise<WhopTokens> {
    // Retrieve and verify PKCE params
    const storedStr = sessionStorage.getItem(STORAGE_KEY);
    console.log("[OAuth] Retrieved PKCE from storage:", storedStr ? "found" : "NOT FOUND");

    if (!storedStr) {
        throw new Error("Missing PKCE parameters - OAuth flow may have expired or was already processed");
    }

    // Remove AFTER checking so we don't process twice
    sessionStorage.removeItem(STORAGE_KEY);

    const stored: PKCEParams & { codeChallenge?: string } = JSON.parse(storedStr);

    // Verify the code_verifier hashes to the same code_challenge
    const recomputedChallenge = await sha256(stored.codeVerifier);
    console.log("[OAuth] PKCE verification:", {
        storedChallenge: stored.codeChallenge?.substring(0, 10) + "...",
        recomputedChallenge: recomputedChallenge.substring(0, 10) + "...",
        match: stored.codeChallenge === recomputedChallenge,
    });

    if (state !== stored.state) {
        throw new Error("Invalid state - possible CSRF attack");
    }

    if (!code) {
        throw new Error("Missing authorization code");
    }

    // Exchange code for tokens
    const res = await fetch("https://api.whop.com/oauth/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            grant_type: "authorization_code",
            code,
            redirect_uri: redirectUri,
            client_id: clientId,
            code_verifier: stored.codeVerifier,
        }),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error("[OAuth] Token exchange failed:", {
            status: res.status,
            error: err,
            request: {
                grant_type: "authorization_code",
                code: code?.substring(0, 10) + "...",
                redirect_uri: redirectUri,
                client_id: clientId,
                code_verifier_length: stored.codeVerifier?.length,
            }
        });
        throw new Error(
            `Token exchange failed: ${err.error_description || err.error || res.status}`
        );
    }

    const tokens = await res.json();
    return { ...tokens, obtained_at: Date.now() };
}
