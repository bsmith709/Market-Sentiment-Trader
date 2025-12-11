<script lang="ts">
    import api from '$lib/api';
    import { login } from '$lib/stores/auth';
    import Button from '$lib/components/Button.svelte';

    // 1. Define Props (Replace createEventDispatcher)
    let { onclose } = $props<{ onclose: () => void }>();

    // 2. Convert State to Runes ($state)
    let isRegistering = $state(false);
    let isLoading = $state(false);
    let errorMessage = $state("");
    let username = $state("");
    let password = $state("");

    // 3. Handle Submit (Standard HTML Event)
    async function handleSubmit(e: Event) {
        e.preventDefault(); // Prevent page reload manually
        
        isLoading = true;
        errorMessage = "";

        try {
            if (isRegistering) {
                // Register
                await api.post('/register', { username, password });
                // Then Login
                await performLogin();
            } else {
                // Login Only
                await performLogin();
            }
        } catch (err: any) {
            if (err.response && err.response.data && err.response.data.detail) {
                errorMessage = err.response.data.detail;
            } else {
                errorMessage = "An unexpected error occurred.";
            }
        } finally {
            isLoading = false;
        }
    }

    async function performLogin() {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await api.post('/token', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        login(res.data.access_token, username);
        
        // 4. Call the Callback Prop
        onclose(); 

        username = "";
        password = "";
    }

    function toggleMode() {
        isRegistering = !isRegistering;
        errorMessage = "";
    }
</script>

<div id="login-dropdown" class="absolute left-0 mt-6 w-12 bg-white border border-gray-200 rounded-lg shadow-xl p-5 z-50">
    <h3 class="text-lg font-bold text-gray-800 mb-1">
        {isRegistering ? 'Create Account' : 'Welcome Back'}
    </h3>
    <p class="text-xs text-gray-500 mb-4">
        {isRegistering ? 'Join to create strategies.' : 'Sign in to access your strategies.'}
    </p>
    
    {#if errorMessage}
        <div class="p-2 mb-3 bg-red-50 border border-red-100 rounded text-xs text-red-600 font-medium">
            {errorMessage}
        </div>
    {/if}

    <form onsubmit={handleSubmit} class="space-y-3">
        <div>
            <label for="username" class="sr-only">Username</label>
            <input 
                id="username"
                type="text" 
                bind:value={username} 
                placeholder="Username" 
                required
                class="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-main-500 focus:ring-main-500"
            />
        </div>
        
        <div>
            <label for="password" class="sr-only">Password</label>
            <input 
                id="password"
                type="password" 
                bind:value={password} 
                placeholder="Password" 
                required
                class="block w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-main-500 focus:ring-main-500"
            />
        </div>
        <Button type="submit" variant="secondary" size="custom" class="w-full bg-blue-600 text-white py-1.5 rounded-md text-sm font-medium hover:bg-blue-700 transition">
            {isLoading ? 'Processing...' : (isRegistering ? 'Sign Up' : 'Sign In')}
        </Button>
    </form>
    
    <div class="mt-4 pt-3 border-t border-gray-100 text-center">
        <button 
            type="button"
            onclick={toggleMode} 
            class="text-xs text-gray-500 hover:text-main-600 underline decoration-gray-300 hover:decoration-main-600"
        >
            {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Register'}
        </button>
    </div>
</div>