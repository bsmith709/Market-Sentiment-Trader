import api from '$lib/api';
import { redirect } from '@sveltejs/kit';

export const ssr = false;

export const load = async () => {
    try {
        const res = await api.get('/backtest/jobs');
        // Sort by newest first
        const sortedJobs = res.data.sort((a: any, b: any) => 
            new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
        );
        
        return {
            jobs: sortedJobs
        };
    } catch (err: any) {
        if (err.response?.status === 401) {
            throw redirect(302, '/?login=true');
        }
        return {
            jobs: []
        };
    }
};