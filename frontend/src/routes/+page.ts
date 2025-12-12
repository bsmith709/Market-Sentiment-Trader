import api from '$lib/api';
import { redirect } from '@sveltejs/kit';

export const ssr = false;

export const load = async ({ url }) => {
    // 1. Check URL for 'date' param, otherwise default to first trading day of 2021
    const selectedDate = url.searchParams.get('date') || '2021-01-04';

    try {
        const res = await api.get(`/stocks?sim_date=${selectedDate}`);
        
        return {
            stocks: res.data || [],
            currentDate: selectedDate
        };
    } catch (err: any) {
        if (err.response?.status === 401) {
            throw redirect(302, '/?login=true');
        }
        return {
            stocks: [],
            currentDate: selectedDate
        };
    }
};