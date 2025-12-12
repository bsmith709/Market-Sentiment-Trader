<script lang="ts">
    import LeaderboardCard from '$lib/components/LeaderboardCard.svelte';
    import Button from '$lib/components/Button.svelte';
    import { invalidateAll } from '$app/navigation';

    let { data } = $props();

    // 1. Use $derived so it updates automatically when data refreshes
    // 2. Add '|| []' to prevent "undefined" crashes (The White Screen Fix)
    let entries = $derived(data.entries || []);
    
    let isRefreshing = $state(false);

    async function refresh() {
        isRefreshing = true;
        await invalidateAll(); // This re-runs the load function
        isRefreshing = false;
    }
</script>

<div class="max-w-4xl mx-auto px-4 py-4 h-[calc(100vh-80px)] flex flex-col">
    
    <div class="flex justify-between items-center gap-2 mb-2">
        <div>
            <h1 class="text-2xl font-bold text-neutral-900">Top Strategies</h1>
            <p class="text-gray-500 text-sm mt-1">Community rankings based on total return percentage.</p>
        </div>
        
        <Button variant="primary" size="sm" onclick={refresh} disabled={isRefreshing}>
            {isRefreshing ? 'Refreshing...' : 'Refresh Rankings'}
        </Button>
    </div>

    <div class="flex-grow overflow-y-auto scrollbar-hide pb-10">
        {#if entries.length === 0}
            <div class="text-center py-20 bg-white rounded-xl border border-dashed border-gray-300">
                <div class="mx-auto h-12 w-12 text-gray-300 mb-3">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-12 h-12">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">No Ranked Strategies Yet</h3>
                <p class="text-gray-500 mb-4 text-sm">Run a backtest to see if you can make the leaderboard!</p>
                <a href="/strategies" class="text-blue-600 hover:underline text-sm font-medium">Create Strategy &rarr;</a>
            </div>
        {:else}
            <div class="space-y-4">
                {#each entries as entry, i (entry.username + entry.strategy_name + '-' + i)}
                    <LeaderboardCard {entry} rank={i + 1} />
                {/each}
            </div>
        {/if}
    </div>
</div>