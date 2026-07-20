/// <reference types="vite/client" />

interface ImportMetaEnv {
    /**
     * Backend API origin, e.g. `http://localhost:8000`.
     *
     * Typed as possibly undefined because Vite inlines this at build time and
     * omits it entirely when it is not defined. `src/config/env.ts` validates it
     * and re-exports a guaranteed `string` as `API_BASE_URL`.
     */
    readonly VITE_API_URL: string | undefined;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
