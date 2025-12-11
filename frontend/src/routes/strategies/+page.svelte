<script lang="ts">
    import StrategyCard from '$lib/components/StrategyCard.svelte';
    import Button from '$lib/components/Button.svelte';
    import CreateStrategyModal from '$lib/components/CreateStrategyModal.svelte';
    import api from '$lib/api';
    import { goto } from '$app/navigation';

    // 1. Get Data from the Loader (+page.ts)
    let { data } = $props();
    
    // Create a local state copy so we can remove items instantly on delete
    let strategies = $state(data.strategies || []);

    let showCreateModal = $state(false); // <--- Modal State

    // --- ACTIONS ---

    async function handleDelete(id: number) {
        if (!confirm("Are you sure you want to delete this strategy?")) return;

        try {
            // 1. Call API
            await api.delete(`/strategies/${id}`);
            
            // 2. Update UI instantly (remove from list)
            strategies = strategies.filter((s: any) => s.strategy_id !== id);
        } catch (err) {
            alert("Failed to delete strategy.");
            console.error(err);
        }
    }

    async function handleBacktest(id: number) {
        try {
            // 1. Trigger the job
            const res = await api.post(`/backtest/${id}`);
            
            alert(`Backtest started! Job ID: ${res.data.job_id}`);
            // Optional: Redirect to a "Results" or "Jobs" page?
            // goto('/leaderboard'); 
        } catch (err) {
            alert("Failed to start backtest.");
            console.error(err);
        }
    }

    function handleStrategyCreated(newStrategy: any) {
        // Add to the top of the list
        strategies = [newStrategy, ...strategies];
    }
</script>

<div class="max-w-7xl mx-auto px-4 py-4">
    
    <div class="flex justify-between items-center gap-2 mb-2">
        <div>
            <h1 class="text-2xl font-bold text-gray-900">My Strategies</h1>
            <p class="text-gray-500 text-sm mt-1">Manage and test your automated trading rules.</p>
        </div>
        
        <Button 
            variant="primary" size="sm"
            onclick={() => showCreateModal = true}
        >
            + Create Strategy
        </Button>
        
    </div>

    {#if showCreateModal}
        <CreateStrategyModal 
            onclose={() => showCreateModal = false} 
            oncreated={handleStrategyCreated} 
        />
    {/if}

    {#if strategies.length === 0}
        <div class="text-center py-20 bg-white rounded-lg border border-dashed border-gray-300">
            <div class="text-gray-400 mb-4">
                <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
            </div>
            <h3 class="text-lg font-medium text-gray-900">No Strategies Yet</h3>
            <p class="text-gray-500 mb-6">Create your first algorithm to start backtesting.</p>
            <Button variant="secondary" onclick={() => goto('/strategies/create')}>
                Create Strategy
            </Button>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each strategies as strategy (strategy.strategy_id)}
                <StrategyCard 
                    {strategy} 
                    ondelete={handleDelete} 
                    onbacktest={handleBacktest} 
                />
            {/each}
        </div>
    {/if}
</div>