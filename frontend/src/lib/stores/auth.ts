import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Initialize from localStorage if available (persists login on refresh)
const storedToken = browser ? localStorage.getItem('access_token') : null;
const storedUser = browser ? localStorage.getItem('username') : null;

export const auth = writable({
    token: storedToken,
    username: storedUser,
    isAuthenticated: !!storedToken
});

// Helper to log in
export function login(token: string, username: string) {
    if (browser) {
        localStorage.setItem('access_token', token);
        localStorage.setItem('username', username);
    }
    auth.set({ token, username, isAuthenticated: true });
}

// Helper to log out
export function logout() {
    if (browser) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
    }
    auth.set({ token: null, username: null, isAuthenticated: false });
}