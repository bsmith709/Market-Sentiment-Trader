// src/lib/api.ts
import axios, { type InternalAxiosRequestConfig } from 'axios';
import { env } from '$env/dynamic/public';
import { browser } from '$app/environment';

// 1. Create the Axios instance
const api = axios.create({
    // Fallback to localhost if the env var is missing
    baseURL: env.PUBLIC_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

// 2. Add Request Interceptor (Attaches JWT)
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    // CRITICAL: Only access localStorage if we are in the browser!
    // SvelteKit runs this code on the server first, where localStorage doesn't exist.
    if (browser) {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.set('Authorization', `Bearer ${token}`);
        }
    }
    return config;
});

export default api;