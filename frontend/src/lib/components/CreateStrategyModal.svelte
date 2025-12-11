<script lang="ts">
    import api from '$lib/api';
    import Button from '$lib/components/Button.svelte';
    import Icon from '$lib/components/Icon.svelte';

    // Props
    let { onclose, oncreated } = $props<{ 
        onclose: () => void, 
        oncreated: (newStrategy: any) => void 
    }>();

    // Strategy State
    let name = $state("");
    let description = $state("");
    
    // Initialize rules with ALL fields
    let rules = $state([
        createDefaultRule()
    ]);

    function createDefaultRule() {
        return {
            ticker: "",
            type: "momentum",
            max_allocation_pct: 1.0, 
            
            // Standard Triggers
            news_buy_threshold: 0.7,
            news_sell_threshold: 0.4,
            reddit_buy_threshold: undefined as number | undefined,
            reddit_sell_threshold: undefined as number | undefined,
            
            // Risk
            stop_loss_pct: 0.1, 
            take_profit_pct: 0.2,
            
            // NEW: Advanced Fields (Risk)
            trailing_stop_pct: undefined as number | undefined,
            cooldown_days: 0,
            
            // NEW: Advanced Fields (Filters)
            min_mentions: 0,
            hype_smoothing_window: 0,
            price_sma_days: undefined as number | undefined,
            news_hype_delta_min: undefined as number | undefined,
            reddit_hype_delta_min: undefined as number | undefined,

            // UI State (Local to this rule)
            showAdvanced: false 
        };
    }

    let isLoading = $state(false);
    let errorMessage = $state("");

    // --- ACTIONS ---

    function addRule() {
        rules.push(createDefaultRule());
    }

    function removeRule(index: number) {
        if (rules.length > 1) {
            rules = rules.filter((_, i) => i !== index);
        }
    }

    function toggleAdvanced(index: number) {
        rules[index].showAdvanced = !rules[index].showAdvanced;
    }

    async function handleSubmit(e: Event) {
        e.preventDefault();
        isLoading = true;
        errorMessage = "";

        try {
            const payload = {
                name,
                description,
                rules: rules.map(r => ({
                    ...r,
                    ticker: r.ticker.toUpperCase(),
                    // Sanitize Optional fields to null if empty/undefined
                    reddit_buy_threshold: r.reddit_buy_threshold || null,
                    reddit_sell_threshold: r.reddit_sell_threshold || null,
                    news_buy_threshold: r.news_buy_threshold || null,
                    news_sell_threshold: r.news_sell_threshold || null,
                    
                    stop_loss_pct: r.stop_loss_pct || null,
                    take_profit_pct: r.take_profit_pct || null,
                    trailing_stop_pct: r.trailing_stop_pct || null,
                    
                    price_sma_days: r.price_sma_days || null,
                    news_hype_delta_min: r.news_hype_delta_min || null,
                    reddit_hype_delta_min: r.reddit_hype_delta_min || null,
                    
                    // Integers can stay 0
                    cooldown_days: r.cooldown_days,
                    min_mentions: r.min_mentions,
                    hype_smoothing_window: r.hype_smoothing_window
                }))
            };

            const res = await api.post('/strategies', payload);
            oncreated(res.data);
            onclose();

        } catch (err: any) {
            console.error(err);
            if (err.response && err.response.data && err.response.data.detail) {
                const d = err.response.data.detail;
                if (Array.isArray(d)) {
                    errorMessage = d.map((e: any) => e.msg).join(", ");
                } else {
                    errorMessage = d;
                }
            } else {
                errorMessage = "Failed to create strategy.";
            }
        } finally {
            isLoading = false;
        }
    }
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" onclick={onclose}></div>

    <div class="relative w-full max-w-3xl max-h-[90vh] flex flex-col bg-white rounded-xl shadow-2xl overflow-hidden">
        
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gray-50/50">
            <h2 class="text-lg font-bold text-gray-900">Create New Strategy</h2>
            <button type="button" onclick={onclose} class="text-gray-400 hover:text-gray-600">
                <Icon name="chevron-down" class="w-5 h-5 rotate-180" />
            </button>
        </div>

        <div class="overflow-y-auto p-6 space-y-6">
            
            {#if errorMessage}
                <div class="p-3 bg-red-50 border border-red-100 rounded-md text-sm text-red-600">
                    {errorMessage}
                </div>
            {/if}

            <form id="strategy-form" onsubmit={handleSubmit} class="space-y-6">
                
                <div class="space-y-4">
                    <div>
                        <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Strategy Name</label>
                        <input type="text" id="name" bind:value={name} required placeholder="e.g. Tesla Momentum Alpha"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 sm:text-sm" />
                    </div>
                    <div>
                        <label for="desc" class="block text-sm font-medium text-gray-700 mb-1">Description <span class="text-gray-400 font-normal">(Optional)</span></label>
                        <textarea id="desc" bind:value={description} rows="2" placeholder="What does this strategy do?"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 sm:text-sm"></textarea>
                    </div>
                </div>

                <div class="border-t border-gray-100 pt-4">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-gray-900 uppercase tracking-wide">Trading Rules</h3>
                        <Button type="button" variant="ghost" size="sm" onclick={addRule} class="text-xs text-main-600 hover:text-main-700 hover:bg-main-50">
                            + Add Ticker
                        </Button>
                    </div>

                    <div class="space-y-6">
                        {#each rules as rule, i}
                            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200 relative">
                                
                                {#if rules.length > 1}
                                    <button type="button" onclick={() => removeRule(i)} 
                                        class="absolute top-2 right-2 text-gray-300 hover:text-red-500 transition-colors z-10">
                                        <Icon name="chevron-down" class="w-4 h-4 rotate-45" /> </button>
                                {/if}

                                <div class="grid grid-cols-1 sm:grid-cols-12 gap-4">
                                    
                                    <div class="sm:col-span-4">
                                        <label class="block text-xs font-medium text-gray-500 mb-1">Ticker</label>
                                        <input type="text" bind:value={rule.ticker} required placeholder="AAPL"
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-sm uppercase" />
                                    </div>
                                    <div class="sm:col-span-4">
                                        <label class="block text-xs font-medium text-gray-500 mb-1">Strategy Type</label>
                                        <select bind:value={rule.type} class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-sm">
                                            <option value="momentum">Momentum (Trend)</option>
                                            <option value="mean_reversion">Mean Reversion (Dip)</option>
                                        </select>
                                    </div>
                                    <div class="sm:col-span-4">
                                        <label class="block text-xs font-medium text-gray-500 mb-1">Max Allocation (0-1)</label>
                                        <input type="number" step="0.01" min="0.01" max="1.0" bind:value={rule.max_allocation_pct} required
                                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-sm" />
                                    </div>

                                    <div class="sm:col-span-6 border-t border-gray-200 pt-3 mt-1">
                                        <span class="block text-xs font-bold text-gray-700 mb-2">News Sentiment</span>
                                        <div class="grid grid-cols-2 gap-2">
                                            <div>
                                                <label class="block text-[10px] text-gray-400">Buy</label>
                                                <input type="number" step="0.01" min="0" max="1" bind:value={rule.news_buy_threshold} placeholder="0.7"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-xs" />
                                            </div>
                                            <div>
                                                <label class="block text-[10px] text-gray-400">Sell</label>
                                                <input type="number" step="0.01" min="0" max="1" bind:value={rule.news_sell_threshold} placeholder="0.4"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-xs" />
                                            </div>
                                        </div>
                                    </div>

                                    <div class="sm:col-span-6 border-t border-gray-200 pt-3 mt-1">
                                        <span class="block text-xs font-bold text-gray-700 mb-2">Reddit Hype</span>
                                        <div class="grid grid-cols-2 gap-2">
                                            <div>
                                                <label class="block text-[10px] text-gray-400">Buy</label>
                                                <input type="number" step="0.01" min="0" max="1" bind:value={rule.reddit_buy_threshold} placeholder="Optional"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-xs" />
                                            </div>
                                            <div>
                                                <label class="block text-[10px] text-gray-400">Sell</label>
                                                <input type="number" step="0.01" min="0" max="1" bind:value={rule.reddit_sell_threshold} placeholder="Optional"
                                                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-main-500 focus:ring-main-500 text-xs" />
                                            </div>
                                        </div>
                                    </div>

                                    <div class="sm:col-span-12 border-t border-gray-200 pt-3 mt-1 flex gap-4">
                                        <div class="w-1/2">
                                            <label class="block text-xs font-medium text-red-600 mb-1">Stop Loss %</label>
                                            <input type="number" step="0.01" min="0" max="1" bind:value={rule.stop_loss_pct} placeholder="0.10"
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-red-500 focus:ring-red-500 text-sm" />
                                        </div>
                                        <div class="w-1/2">
                                            <label class="block text-xs font-medium text-green-600 mb-1">Take Profit %</label>
                                            <input type="number" step="0.01" min="0" max="1" bind:value={rule.take_profit_pct} placeholder="0.20"
                                                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 text-sm" />
                                        </div>
                                    </div>

                                    <div class="sm:col-span-12 pt-2">
                                        <button type="button" onclick={() => toggleAdvanced(i)} class="flex items-center text-xs text-blue-600 hover:text-blue-800 font-medium">
                                            <span class="mr-1">{rule.showAdvanced ? 'Hide' : 'Show'} Advanced Settings</span>
                                            <Icon name="chevron-down" class={`w-3 h-3 transition-transform ${rule.showAdvanced ? 'rotate-180' : ''}`} />
                                        </button>
                                    </div>

                                    {#if rule.showAdvanced}
                                        <div class="sm:col-span-12 grid grid-cols-2 sm:grid-cols-4 gap-4 bg-blue-50/50 p-3 rounded-md border border-blue-100">
                                            
                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">Trailing Stop %</label>
                                                <input type="number" step="0.01" min="0" max="1" bind:value={rule.trailing_stop_pct} placeholder="e.g. 0.05"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>
                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">Cooldown Days</label>
                                                <input type="number" step="1" min="0" bind:value={rule.cooldown_days} placeholder="0"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>

                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">Min Mentions</label>
                                                <input type="number" step="1" min="0" bind:value={rule.min_mentions} placeholder="0"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>
                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">SMA Days (Trend)</label>
                                                <input type="number" step="1" min="2" bind:value={rule.price_sma_days} placeholder="e.g. 50"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>

                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">Smoothing Window</label>
                                                <input type="number" step="1" min="0" bind:value={rule.hype_smoothing_window} placeholder="0"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>
                                            <div class="col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">News Hype Delta</label>
                                                <input type="number" step="0.01" min="0" bind:value={rule.news_hype_delta_min} placeholder="e.g. 0.1"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>
                                            <div class="col-span-2 sm:col-span-1">
                                                <label class="block text-[10px] text-gray-500 font-bold mb-1">Reddit Hype Delta</label>
                                                <input type="number" step="0.01" min="0" bind:value={rule.reddit_hype_delta_min} placeholder="e.g. 0.1"
                                                    class="block w-full rounded border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-xs" />
                                            </div>
                                        </div>
                                    {/if}

                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

            </form>
        </div>

        <div class="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-end gap-3">
            <Button type="button" variant="ghost" onclick={onclose}>Cancel</Button>
            <Button type="submit" form="strategy-form" variant="primary" disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create Strategy'}
            </Button>
        </div>
    </div>
</div>