<script lang="ts">
    import Icon from '$lib/components/Icon.svelte';

    // Props
    let { job } = $props<{ job: any }>();

    // Helper: Format Dates
    function formatDate(dateStr: string) {
        return new Date(dateStr).toLocaleString('en-US', {
            month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
        });
    }

    // Helper: Format Percentages
    function formatPct(val: number) {
        return val.toFixed(2) + '%';
    }

    // Helper: Color logic for returns
    function getReturnColor(val: number) {
        if (val > 0) return 'text-green-600';
        if (val < 0) return 'text-red-600';
        return 'text-gray-600';
    }
</script>

<div class="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-5 flex flex-col h-full">
    
    <div class="flex justify-between items-start mb-4">
        <div>
            <h3 class="text-sm font-bold text-gray-900">
                Backtest #{job.job_id}
            </h3>
            <span class="text-xs text-gray-400">
                {formatDate(job.submitted_at)}
            </span>
        </div>
        
        {#if job.status === 'completed'}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                Completed
            </span>
        {:else if job.status === 'failed'}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                Failed
            </span>
        {:else}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 animate-pulse">
                Running...
            </span>
        {/if}
    </div>

    <div class="flex-grow flex items-center">
        {#if job.status === 'completed' && job.result}
            <div class="w-full grid grid-cols-3 gap-2 text-center">
                
                <div class="p-2 bg-gray-50 rounded-lg">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Return</div>
                    <div class={`text-sm font-mono font-bold ${getReturnColor(job.result.total_return_pct)}`}>
                        {job.result.total_return_pct > 0 ? '+' : ''}{formatPct(job.result.total_return_pct)}
                    </div>
                </div>

                <div class="p-2 bg-gray-50 rounded-lg">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Win Rate</div>
                    <div class="text-sm font-mono font-bold text-gray-800">
                        {formatPct(job.result.win_rate)}
                    </div>
                </div>

                <div class="p-2 bg-gray-50 rounded-lg">
                    <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-1">Max DD</div>
                    <div class="text-sm font-mono font-bold text-red-500">
                        {formatPct(job.result.max_drawdown_pct)}
                    </div>
                </div>

            </div>
        {:else if job.status === 'failed'}
            <div class="w-full text-center py-4 text-sm text-red-500 bg-red-50 rounded-lg border border-red-100">
                Execution Error
            </div>
        {:else}
            <div class="w-full py-4 flex flex-col items-center justify-center text-gray-400 space-y-2">
                <svg class="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-xs">Processing Market Data...</span>
            </div>
        {/if}
    </div>

    {#if job.status === 'completed' && job.result}
        <div class="mt-4 pt-3 border-t border-gray-100 flex justify-between text-xs text-gray-500">
            <span>Trades Executed:</span>
            <span class="font-mono font-medium text-gray-900">{job.result.trades.length}</span>
        </div>
    {/if}
</div>