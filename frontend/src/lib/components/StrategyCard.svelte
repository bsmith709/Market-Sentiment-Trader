<script lang="ts">
    import Button from '$lib/components/Button.svelte';
    import Icon from '$lib/components/Icon.svelte'; // Ensure you have this imported

    // Props
    let { strategy, ondelete, onbacktest } = $props<{ 
        strategy: any, 
        ondelete: (id: number) => void, 
        onbacktest: (id: number) => void 
    }>();

    // State for the accordion
    let isExpanded = $state(false);

    function toggleExpand() {
        isExpanded = !isExpanded;
    }

    // Helper: Format Percentages (0.1 -> "10%")
    function formatPct(val: number | undefined | null) {
        if (val === undefined || val === null) return '-';
        return `${(val * 100).toFixed(0)}%`;
    }

    // Helper: Badge Color
    function getTypeColor(type: string) {
        return type === 'momentum' 
            ? 'bg-blue-50 text-blue-700 border-blue-100'
            : 'bg-purple-50 text-purple-700 border-purple-100';
    }
</script>

<div class="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 flex flex-col overflow-hidden">
    
    <div class="p-5">
        <div class="flex justify-between items-start gap-4">
            
            <div class="flex-grow min-w-0"> <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-lg font-bold text-gray-900 leading-tight truncate">
                        {strategy.name}
                    </h3>
                    <span class="text-xs font-mono text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded border border-gray-100 shrink-0">
                        #{strategy.strategy_id}
                    </span>
                </div>
                
                {#if strategy.description}
                    <p class="text-sm text-gray-500 leading-relaxed line-clamp-2" title={strategy.description}>
                        {strategy.description}
                    </p>
                {:else}
                    <p class="text-xs text-gray-400 italic">No description provided.</p>
                {/if}
            </div>

            <button 
                onclick={toggleExpand}
                class="text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-full hover:bg-blue-50 shrink-0"
                aria-label={isExpanded ? "Collapse" : "Expand"}
            >
                <div class="transition-transform duration-200" class:rotate-180={isExpanded}>
                    <Icon name="chevron-down" class="w-5 h-5" /> 
                </div>
            </button>
        </div>

        <div class="mt-5 flex gap-3">
            <Button 
                variant="primary" 
                size="sm" 
                class="flex-1 text-xs py-2 shadow-sm" 
                onclick={(e: Event) => { e.stopPropagation(); onbacktest(strategy.strategy_id); }}
            >
                Run Backtest
            </Button>
            
            <Button 
                variant="outline" 
                size="sm" 
                class="px-4 text-xs border-gray-200 text-red-600 hover:bg-red-50 hover:border-red-200 hover:text-red-700" 
                onclick={(e: Event) => { e.stopPropagation(); ondelete(strategy.strategy_id); }}
            >
                Delete
            </Button>
        </div>
    </div>

    {#if isExpanded}
        <div class="border-t border-gray-100 bg-gray-50/50 p-4 space-y-3">
            <h4 class="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 ml-1">
                Strategy Rules ({strategy.rules.length})
            </h4>
            
            {#each strategy.rules as rule}
                <div class="bg-white border border-gray-200 rounded-lg p-3 shadow-sm">
                    <div class="flex justify-between items-center mb-3 pb-2 border-b border-gray-50">
                        <div class="flex items-center gap-2">
                            <span class="font-bold text-gray-900 bg-gray-100 px-2 py-0.5 rounded text-sm">
                                {rule.ticker}
                            </span>
                            <span class={`text-[10px] font-bold px-2 py-0.5 text-xs ${getTypeColor(rule.type)}`}>
                                {rule.type.toUpperCase().replace('_', ' ')}
                            </span>
                        </div>
                        <span class="text-xs text-gray-500">
                            Max Alloc: <span class="font-mono text-gray-900 font-medium">{formatPct(rule.max_allocation_pct)}</span>
                        </span>
                    </div>

                    <div class="grid grid-cols-2 gap-4 text-xs">
                        
                        <div>
                            <div class="font-semibold text-gray-400 uppercase text-[10px] mb-1.5">Entry Signals</div>
                            <div class="space-y-1.5 pl-1">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">News</span>
                                    <span class="font-mono font-medium text-gray-900">{formatPct(rule.news_buy_threshold)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Reddit</span>
                                    <span class="font-mono font-medium text-gray-900">{formatPct(rule.reddit_buy_threshold)}</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <div class="font-semibold text-gray-400 uppercase text-[10px] mb-1.5">Exit Signals</div>
                            <div class="space-y-1.5 pl-1">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">News</span>
                                    <span class="font-mono font-medium text-gray-900">{formatPct(rule.news_sell_threshold)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">Reddit</span>
                                    <span class="font-mono font-medium text-gray-900">{formatPct(rule.reddit_sell_threshold)}</span>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>