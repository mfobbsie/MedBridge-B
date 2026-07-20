
export interface apiHelper<T = unknown> {
    url: string;
    method: 'POST' | 'GET' | 'DELETE' | 'PATCH' | "HEAD" | "PUT";
    body?: T,
    tokenOverride?: string;
    params?: Record<string, string | number | boolean | null | undefined>
}

/**
 * Thrown when a request URL is not an absolute http(s) URL.
 *
 * Most often this means VITE_API_URL was missing or malformed, which previously
 * produced silent same-origin requests such as `/undefined/auth/login`.
 */
export class InvalidApiUrlError extends Error {
    constructor(url: string) {
        super(
            `[apiHelper] Invalid request URL: "${url}". Expected an absolute http(s) URL. ` +
            "Check that VITE_API_URL is set correctly — see app-frontend/.env.example."
        );
        this.name = "InvalidApiUrlError";
    }
}

/**
 * Parses an absolute http(s) request URL.
 *
 * Deliberately does NOT resolve relative URLs against `window.location.origin`:
 * that turned a misconfigured base URL into a valid same-origin request which
 * returned the SPA's index.html with a 200 status instead of failing.
 */
const toAbsoluteApiUrl = (url: string): URL => {
    try {
        const parsed = new URL(url);
        if (parsed.protocol === "http:" || parsed.protocol === "https:") {
            return parsed;
        }
    } catch {
        // Falls through to the InvalidApiUrlError below.
    }
    throw new InvalidApiUrlError(url);
};

export const setAuthCookie = (token: string, days: number = 7): void => {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;

    document.cookie = `auth_token=${token}; ${expires}; path=/; SameSite=Strict; Secure`;
};


export const getAuthCookie = (): string | null => {
    const name = "auth_token=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');

    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return null;

}

export const clearAuthCookie = (): void => {
    document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/; SameSite=Strict; Secure";

};




export const apiHelper = async ({ url, method, body, tokenOverride, params }: apiHelper) => {
    try {

        const token = tokenOverride || getAuthCookie();
        const isFormData = body instanceof FormData;
        const headers: Record<string, string> = {}

        if(!isFormData){
            headers["Content-Type"] = "application/json";
        }

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const parsedUrl = toAbsoluteApiUrl(url);
        if(params){
            Object.entries(params).forEach(([key, value]) => {
                if(value !== undefined && value !== null){
                    parsedUrl.searchParams.append(key, String(value));
                }
            })
        }


        const options: RequestInit = {
            method: method,
            headers: headers,
        };

        if (body && method !== "GET" && method !== "HEAD") {
            options.body = isFormData ? body : JSON.stringify(body);
        }
        const response = await fetch(parsedUrl.toString(), options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || "Error with response");
        }

        if (response.status === 204) {
            return null;
        }

        const text = await response.text();
        const data = text ? JSON.parse(text) : null;
        return data;

    } catch (error) {
        console.error("Error:", error)
        throw error;
    }
}



