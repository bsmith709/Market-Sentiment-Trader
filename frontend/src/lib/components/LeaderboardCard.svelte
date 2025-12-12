<script lang="ts">
    // Props
    let { entry, rank } = $props<{ entry: any, rank: number }>();

    // Helper: Format Percentages
    function formatPct(val: number) {
        return val.toFixed(2) + '%';
    }

    // Helper: Get Rank Styles
    function getRankTheme(r: number) {
        if (r === 1) return { bg: 'bg-gradient-to-r from-yellow-50 to-yellow-100/50', border: 'border-yellow-200', text: 'text-yellow-700', icon: 'text-yellow-500' }; // Gold
        if (r === 2) return { bg: 'bg-gradient-to-r from-gray-50 to-gray-100/50', border: 'border-gray-200', text: 'text-gray-700', icon: 'text-gray-400' };     // Silver
        if (r === 3) return { bg: 'bg-gradient-to-r from-orange-50 to-orange-100/50', border: 'border-orange-200', text: 'text-orange-700', icon: 'text-orange-500' }; // Bronze
        return { bg: 'bg-white', border: 'border-gray-100', text: 'text-gray-500', icon: 'text-gray-300' };                                // Standard
    }

    const theme = getRankTheme(rank);
</script>

<div class={`relative border rounded-xl shadow-sm p-4 flex items-center justify-between transition-all duration-200 hover:shadow-md ${theme.bg} ${theme.border}`}>
    
    <div class="flex items-center gap-4">
        
        <div class="flex-shrink-0 flex items-center justify-center relative">
            {#if rank <= 3}
                <svg class={`w-7 h-7 ${theme.icon} fill-current`} viewBox="0 0 24 24">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                </svg>
                <span class="absolute inset-0 flex items-center justify-center font-black text-sm text-white pt-1">{rank}</span>
            {:else}
                <span class={`text-xl font-black ${theme.text} opacity-60`}>#{rank}</span>
            {/if}
        </div>

        <div class="flex flex-col">
            <h3 class="text-lg font-bold text-gray-900 leading-tight truncate">
                {entry.strategy_name}
            </h3>
            <div class="text-xs text-gray-500 mt-1 flex items-center flex-wrap gap-1">
                <span>by</span>
                <span class="font-medium text-gray-700 bg-gray-200/80 px-1.5 py-0.5 rounded text-[10px]">
                    @{entry.username}
                </span>
                <span class="text-gray-300">•</span>
                <span>{new Date(entry.rank_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
            </div>
        </div>
    </div>

    <div class="text-right pl-4 flex-shrink-0">
        <div class="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-0.5">Total Return</div>
        <div class={`text-2xl font-mono font-bold ${entry.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {entry.total_return_pct > 0 ? '+' : ''}{formatPct(entry.total_return_pct)}
        </div>
    </div>
</div>