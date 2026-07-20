/**
 * Centralized frontend environment configuration.
 *
 * This is the ONLY module that reads `import.meta.env`. Every other module
 * imports the validated values from here.
 *
 * Validation runs at module load so a missing or malformed configuration
 * fails immediately with an actionable message, instead of silently
 * producing requests such as `/undefined/auth/login`.
 */

const rawApiUrl = import.meta.env.VITE_API_URL;

if (!rawApiUrl) {
    throw new Error(
        "[config] VITE_API_URL is not set. Copy app-frontend/.env.example to " +
        "app-frontend/.env and restart the dev server — Vite only reads .env at startup."
    );
}

if (!/^https?:\/\//.test(rawApiUrl)) {
    throw new Error(
        "[config] VITE_API_URL must be an absolute http(s) URL " +
        `(e.g. http://localhost:8000). Received: "${rawApiUrl}"`
    );
}

/** Backend API origin. Guaranteed non-empty, absolute, and without a trailing slash. */
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, "");
