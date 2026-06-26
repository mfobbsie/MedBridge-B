import { useMutation } from "@tanstack/react-query";
import { useAuth } from "../context/AuthContext";
import type { LoginRequest, AuthResponse } from "../types/auth";

export interface ApiCall<T = unknown> {
    url: string;
    method: 'POST' | 'GET' | 'DELETE' | 'PATCH' | "HEAD";
    body: T
}




export const apiCall = async ({ url, method, body }: ApiCall) => {
    try {

        const options: RequestInit = {
            method: method,
            headers: { "Content-Type": "application/json" },
        };

        if (body && method !== "GET" && method !== "HEAD") {
            options.body = JSON.stringify(body);
        }
        const response = await fetch(url, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || "Error with response");
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



async function loginUser(credentials: LoginRequest): Promise<AuthResponse> {

    return apiCall({
        url: "http://localhost:8000/auth/login",
        method: "POST",
        body: credentials
    })
}

export function useLogin() {
    const { login } = useAuth();

    return useMutation({
        mutationFn: (credentials: LoginRequest) => loginUser(credentials),


        onSuccess: (response: AuthResponse) => {
            if (response.access_token) {
                login(response.access_token, response.email)
            }
        },

        onError: (error: Error) => {
            console.error("Mutation error interceptor:", error.message)
        }

    })
}