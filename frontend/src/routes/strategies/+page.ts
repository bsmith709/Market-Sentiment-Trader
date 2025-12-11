// src/routes/strategies/+page.ts
import api from '$lib/api';
import { redirect } from '@sveltejs/kit';

// CRITICAL: Disable SSR so this runs only in the browser (where localStorage exists)
export const ssr = false;

export const load = async () => {
    try {
        const res = await api.get('/strategies');
        return {
            strategies: res.data
        };
    } catch (err: any) {
        // If 401 Unauthorized, kick them to login
        if (err.response?.status === 401) {
            throw redirect(302, '/?login=true'); 
        }
        // Otherwise return empty list (or handle error UI)
        return {
            strategies: []
        };
    }
};