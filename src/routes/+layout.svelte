<script lang="ts">
	import "./layout.css"
    import { auth, login, logout } from '$lib/stores/auth';
    import api from '$lib/api';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
	import Button from "$lib/components/Button.svelte";

    // UI State
    let showLoginDropdown = false;
    let showMobileNav = false; // State for the hamburger menu

    // Login Form State
    let username = "";
    let password = "";
    let errorMessage = "";

    // Close dropdowns when clicking outside
    onMount(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const dropdown = document.getElementById('login-dropdown');
            const button = document.getElementById('auth-button');

            // If click is not the button, and not inside the dropdown, close it
            if (showLoginDropdown && dropdown && button && 
                !dropdown.contains(event.target as Node) && !button.contains(event.target as Node)) {
                showLoginDropdown = false;
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    });

    // Toggle dropdown
    function toggleDropdown() {
        showLoginDropdown = !showLoginDropdown;
    }

    // Toggle mobile navigation
    function toggleMobileNav() {
        showMobileNav = !showMobileNav;
    }

    // Handle Login
    async function handleLogin() {
        try {
            // Note: Axios uses FormData() for x-www-form-urlencoded
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const res = await api.post('/token', formData);
            
            // Save to store
            login(res.data.access_token, username);
            
            // Reset UI
            showLoginDropdown = false;
            errorMessage = "";
            password = "";
        } catch (err) {
            errorMessage = "Invalid credentials";
        }
    }

    function handleLogout() {
        logout();
        showLoginDropdown = false;
        showMobileNav = false; // Close menu on logout
        goto('/'); 
    }
</script>

<div class="min-h-screen bg-gray-50 flex flex-col">
    <header class="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
        
        <div class="max-w-4xl mx-auto px-4 h-14 flex justify-between items-center">
            
            <div class="relative w-1/3 flex justify-start">
                {#if $auth.isAuthenticated}
                    <div class="text-sm text-gray-700 truncate max-w-[100px]">
                        Hi, {$auth.username}
                    </div>
                {:else}
					<Button variant="primary" size="sm">Login/Register</Button>
                {/if}

                {#if showLoginDropdown}
                    <div id="login-dropdown" class="absolute left-0 mt-8 w-64 bg-white border border-gray-200 rounded-lg shadow-xl p-4 z-50">
                        <h3 class="text-sm font-bold text-gray-700 mb-3">Welcome Back</h3>
                        
                        {#if errorMessage}
                            <div class="text-xs text-red-600 mb-2">{errorMessage}</div>
                        {/if}

                        <form on:submit|preventDefault={handleLogin} class="space-y-3">
                            <input type="text" bind:value={username} placeholder="Username" required
                                class="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            />
                            <input type="password" bind:value={password} placeholder="Password" required
                                class="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                            />
                            <button type="submit" class="w-full bg-blue-600 text-white py-1.5 rounded-md text-sm font-medium hover:bg-blue-700 transition">
                                Sign In
                            </button>
                        </form>
                        
                        <div class="mt-3 pt-2 border-t border-gray-100 text-center">
                            <a href="/register" on:click={() => showLoginDropdown = false} class="text-xs text-gray-500 hover:text-blue-600">Need an account? Register</a>
                        </div>
                    </div>
                {/if}
            </div>
            
            <div class="w-1/3 flex justify-center">
                <a href="/" class="text-xl font-bold text-blue-600 tracking-tight">
                    Sentiment<span class="text-gray-900">Trader</span>
                </a>
            </div>

            <div class="w-1/3 flex justify-end">
                <button on:click={toggleMobileNav} class="p-1 text-gray-600 hover:text-blue-600 focus:outline-none">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                    </svg>
                </button>
            </div>
        </div>
    </header>

    <div 
        class="fixed inset-y-0 right-0 w-64 bg-white shadow-2xl z-40 transform transition-transform duration-300"
        class:translate-x-full={!showMobileNav}
        class:translate-x-0={showMobileNav}
    >
        <div class="p-6">
            <h3 class="text-lg font-bold text-gray-800 mb-6">Navigation</h3>
            <nav class="space-y-4">
                <a 
                    href="/" 
                    on:click={toggleMobileNav} 
                    class="block text-gray-600 hover:text-blue-600 font-medium text-base"
                >
                    Stocks
                </a>
                <a 
                    href="/leaderboard" 
                    on:click={toggleMobileNav} 
                    class="block text-gray-600 hover:text-blue-600 font-medium text-base"
                >
                    Leaderboard
                </a>
                {#if $auth.isAuthenticated}
                    <a 
                        href="/strategies" 
                        on:click={toggleMobileNav} 
                        class="block text-gray-600 hover:text-blue-600 font-medium text-base"
                    >
                        Strategies
                    </a>
                    <button on:click={handleLogout} class="block w-full text-left text-red-500 hover:text-red-700 font-medium text-base mt-6 pt-4 border-t border-gray-100">
                        Logout
                    </button>
                {/if}
            </nav>
        </div>
    </div>
    
    {#if showMobileNav}
        <div on:click={toggleMobileNav} class="fixed inset-0 bg-black opacity-30 z-30"></div>
    {/if}

    <main class="flex-grow">
        <slot />
    </main>
</div>