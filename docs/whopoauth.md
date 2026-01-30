> ## Documentation Index
> Fetch the complete documentation index at: https://docs.whop.com/llms.txt
> Use this file to discover all available pages before exploring further.

# OAuth

> Use OAuth to let users sign in with Whop on your website

Use OAuth 2.1 + PKCE with OpenID Connect (OIDC) to let users sign in with Whop on your website or app.
You can use the returned access tokens to access data and perform actions on behalf of whop users.

<Info>
  OAuth endpoints live at `https://api.whop.com/oauth/`
</Info>

## Step 1: Get your Client ID and Scopes

<Steps>
  <Step title="Create or select your app">
    Go to the [Developer Dashboard](https://whop.com/dashboard/developer), create a new app or select an existing one.
  </Step>

  <Step title="Add redirect URIs">
    In the OAuth section, add every redirect URI you plan to use (exact match required).
  </Step>

  <Step title="Copy credentials">
    Copy your `client_id` (looks like `app_xxxxx`).
  </Step>

  <Step title="Select your scopes">
    Select your available oauth scopes from the "View available scopes" button and select only the ones you need. Copy them as JSON.
  </Step>
</Steps>

## Step 2: Send users to authorize

In your web or mobile client, use PKCE to securely redirect users to Whop's OAuth flow.

```typescript expandable theme={null}
const STORAGE_KEY = "whop_oauth_pkce";

function base64url(bytes: Uint8Array) {
  return btoa(String.fromCharCode(...bytes)).replace(/[+/=]/g, (c) => ({ "+": "-", "/": "_", "=": "" })[c]!);
}

function randomString(len: number) {
  return base64url(crypto.getRandomValues(new Uint8Array(len)));
}

async function sha256(str: string) {
  return base64url(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str))));
}

async function startWhopOAuth(clientId: string, redirectUri: string, scope = "openid profile email", companyId?: string) {
  const pkce = { codeVerifier: randomString(32), state: randomString(16), nonce: randomString(16) };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(pkce));

  const params = new URLSearchParams({
    response_type: "code", client_id: clientId, redirect_uri: redirectUri, scope, state: pkce.state, nonce: pkce.nonce,
    code_challenge: await sha256(pkce.codeVerifier), code_challenge_method: "S256",
    ...(companyId && { company_id: companyId }),
  });

  window.location.href = `https://api.whop.com/oauth/authorize?${params}`;
}
```

Call `startWhopOAuth` to redirect the user:

```typescript  theme={null}
await startWhopOAuth(
  "app_xxxxxxxxx", 
  "https://yourapp.com/oauth/callback",
  "openid profile email", // optionally specify more custom scopes here
  "biz_xxxxx", // optionally specify a scoped company id here
);
```

If the user is not logged in, Whop will prompt for login, then show the consent screen.
If the user has already approved your application for the requested scopes,
they will be automatically redirected back without needing to confirm twice.

<Note>
  If you provide `companyId`, tokens are company-scoped for a specific user, meaning you
  will only have access to resources that that particular user can control on the specified Whop company.
</Note>

## Step 3: Handle the callback and exchange the code

Whop redirects back to your `redirect_uri` with `code` and `state`. Use this function to verify the state, exchange the code for tokens, and retrieve credentials:

```typescript expandable theme={null}
const STORAGE_KEY = "whop_oauth_pkce";

interface WhopTokens {
  access_token: string;
  refresh_token: string;
  id_token?: string; // only present if "openid" scope was requested
  token_type: string;
  expires_in: number;
  obtained_at: number; // we add this client-side for refresh logic
}

async function handleWhopCallback(clientId: string, redirectUri: string): Promise<WhopTokens> {
  const params = new URLSearchParams(window.location.search);
  const [code, returnedState, error] = [params.get("code"), params.get("state"), params.get("error")];
  if (error) throw new Error(`OAuth error: ${error} - ${params.get("error_description") || ""}`);

  const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "null");
  sessionStorage.removeItem(STORAGE_KEY);
  if (!stored || returnedState !== stored.state) throw new Error("Invalid state - possible CSRF");

  const res = await fetch("https://api.whop.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code", code, redirect_uri: redirectUri,
      client_id: clientId, code_verifier: stored.codeVerifier,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`Token exchange failed: ${err.error_description || res.status}`);
  }
  
  const tokens = await res.json();
  return { ...tokens, obtained_at: Date.now() };
}

function storeTokens(tokens: WhopTokens) {
  document.cookie = `whop_tokens=${encodeURIComponent(JSON.stringify(tokens))}; path=/; max-age=${60 * 60 * 24 * 30}; secure; samesite=strict`;
}

function getTokens(): WhopTokens | null {
  const match = document.cookie.match(/whop_tokens=([^;]+)/);
  return match ? JSON.parse(decodeURIComponent(match[1])) : null;
}

function clearTokens() {
  document.cookie = "whop_tokens=; path=/; max-age=0";
}
```

On your callback page:

```typescript  theme={null}
const tokens = await handleWhopCallback(
  "app_xxxxxxxxx",
  "https://yourapp.com/oauth/callback"
);
storeTokens(tokens);
```

## Step 4: Use the tokens

Initialize the Whop SDK with the user's access token:

```typescript  theme={null}
import Whop from "@whop/sdk";

const tokens = getTokens();

const client = new Whop({
  apiKey: tokens.access_token,
});
```

View our [API Reference](/api-reference) to see all available endpoints.

## Step 5: Refresh tokens

Access tokens expire after 1 hour. Use the refresh token to get new credentials:

```typescript expandable theme={null}
async function refreshTokens(clientId: string, companyId?: string): Promise<WhopTokens> {
  const tokens = getTokens();
  if (!tokens?.refresh_token) throw new Error("No refresh token available");

  const res = await fetch("https://api.whop.com/oauth/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "refresh_token",
      refresh_token: tokens.refresh_token,
      client_id: clientId,
      ...(companyId && { company_id: companyId }),
    }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    if (res.status === 401 || error.error === "invalid_grant") {
      clearTokens();
      throw new Error("Session expired - please log in again");
    }
    throw new Error(`Token refresh failed: ${error.error_description || res.status}`);
  }

  const newTokens = await res.json();
  const stored = { ...newTokens, obtained_at: Date.now() };
  storeTokens(stored);
  return stored;
}

async function getValidAccessToken(clientId: string): Promise<string> {
  const tokens = getTokens();
  if (!tokens) throw new Error("Not logged in");

  const expiresAt = tokens.obtained_at + tokens.expires_in * 1000;
  const needsRefresh = Date.now() > expiresAt - 5 * 60 * 1000; // 5 min buffer
  
  if (needsRefresh) {
    const refreshed = await refreshTokens(clientId);
    return refreshed.access_token;
  }

  return tokens.access_token;
}
```

Usage:

```typescript  theme={null}
const accessToken = await getValidAccessToken("app_xxxxxxxxx");
```

<Note>
  Refresh tokens rotate on each use. Always store the new tokens returned from the refresh endpoint.
  If you provided `company_id` during authorization, you must provide the same `company_id` when refreshing.
</Note>

## Step 6: Userinfo and revoke

### Get user info

Fetch the authenticated user's profile using the userinfo endpoint:

```typescript  theme={null}
interface WhopUserInfo {
  sub: string;                 // user tag (e.g. "user_xxxxx")
  name?: string;               // requires "profile" scope
  preferred_username?: string; // requires "profile" scope
  picture?: string;            // requires "profile" scope
  email?: string;              // requires "email" scope
  email_verified?: boolean;    // requires "email" scope
}

async function getUserInfo(accessToken: string): Promise<WhopUserInfo> {
  const res = await fetch("https://api.whop.com/oauth/userinfo", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(`Failed to fetch user info: ${res.status}`);
  return res.json();
}
```

<Note>
  The fields returned depend on the scopes granted. `openid` is required, `profile` adds name/username/picture, `email` adds email fields.
</Note>

### Revoke tokens on logout

When a user logs out, revoke their refresh token. Access tokens expire after 1 hour and cannot be server-revoked.

```typescript  theme={null}
async function logout(clientId: string) {
  const tokens = getTokens();
  if (tokens?.refresh_token) {
    await fetch("https://api.whop.com/oauth/revoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: tokens.refresh_token, client_id: clientId }),
    });
  }
  clearTokens();
}
```

<Warning>
  Always revoke tokens when users log out. This invalidates the refresh token immediately, preventing unauthorized access even if the token was compromised.
</Warning>

## Error handling

OAuth errors follow the standard format:

```json  theme={null}
{
  "error": "invalid_grant",
  "error_description": "Authorization code has expired"
}
```

Common error codes:

* `invalid_request` - Missing or invalid parameter
* `invalid_grant` - Code/token expired or revoked
* `invalid_client` - Unknown client\_id
* `insufficient_scope` - Token doesn't have required scope
* `rate_limit_exceeded` - Too many requests (check `Retry-After` header)
