<script lang="ts">
    import BacktestCard from '$lib/components/BacktestCard.svelte';
    import Button from '$lib/components/Button.svelte';
    import api from '$lib/api';
    import { onMount } from 'svelte';

    let { data } = $props();
    let jobs = $state(data.jobs || []);
    let isRefreshing = $state(false);

    // Manual Refresh Function
    async function refreshJobs() {
        isRefreshing = true;
        try {
            const res = await api.get('/backtest/jobs');
            jobs = res.data.sort((a: any, b: any) => 
                new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
            );
        } catch (err) {
            console.error("Failed to refresh jobs", err);
        } finally {
            isRefreshing = false;
        }
    }
</script>

<div class="max-w-7xl mx-auto px-4 py-4">
    
    <div class="flex justify-between items-center mb-4">
        <div>
            <h1 class="text-2xl font-bold text-neutral-900">Backtest Results</h1>
            <p class="text-gray-500 text-sm mt-1">History of your strategy simulations.</p>
        </div>
        
        <Button variant="primary" size="sm" onclick={refreshJobs} disabled={isRefreshing}>
            {#if isRefreshing}
                Refreshing...
            {:else}
                Refresh Status
            {/if}
        </Button>
    </div>

    {#if jobs.length === 0}
        <div class="text-center py-20 bg-white rounded-lg border border-dashed border-gray-300">
            <h3 class="text-lg font-medium text-gray-900">No Backtests Found</h3>
            <p class="text-gray-500 mb-4">Run a backtest from your Strategies page to see results here.</p>
            <a href="/strategies" class="text-blue-600 hover:underline text-sm font-medium">Go to Strategies &rarr;</a>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {#each jobs as job (job.job_id)}
                <BacktestCard {job} />
            {/each}
        </div>
    {/if}
</div>