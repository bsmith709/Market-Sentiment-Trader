import api from '$lib/api';
import { redirect } from '@sveltejs/kit';

export const ssr = false;

export const load = async () => {
    try {
        const res = await api.get('/leaderboard');
        
        // Sort descending by return %
        const sortedEntries = res.data.sort((a: any, b: any) => 
            b.total_return_pct - a.total_return_pct
        );
        
        // IMPORTANT: Return 'entries', not 'jobs'
        return {
            entries: sortedEntries
        };
    } catch (err: any) {
        if (err.response?.status === 401) {
            throw redirect(302, '/?login=true');
        }
        // Return empty array on error to prevent crash
        return {
            entries: [] 
        };
    }
};