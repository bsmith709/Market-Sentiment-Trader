<script lang="ts">
    import StockCard from '$lib/components/StockCard.svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';

    let { data } = $props();
    let stocks = $derived(data.stocks || []);
    let currentDate = $derived(data.currentDate);

    function changeDate(days: number) {
        // 1. Parse the string manually to get Year, Month, Day
        const [y, m, d] = currentDate.split('-').map(Number);
        
        // 2. Create a Date object strictly in UTC (Month is 0-indexed)
        const dateObj = new Date(Date.UTC(y, m - 1, d));
        
        // 3. Add/Subtract days using UTC methods
        dateObj.setUTCDate(dateObj.getUTCDate() + days);
        
        // 4. Format back to YYYY-MM-DD
        const nextDate = dateObj.toISOString().split('T')[0];
        updateDate(nextDate);
    }

    // Update URL which triggers the data loader
    function updateDate(newDate: string) {
        const url = new URL($page.url);
        url.searchParams.set('date', newDate);
        goto(url, { keepFocus: true });
    }
</script>

<div class="max-w-7xl mx-auto px-4 py-4 h-[calc(100vh-80px)] flex flex-col">
    
    <div class="flex flex-col justify-between items-center gap-4 mb-4 flex-shrink-0">
        <div>
            <h1 class="text-2xl font-bold text-neutral-900 tracking-tight">Market Dashboard</h1>
        </div>

        <div class="flex items-center gap-2 bg-white p-1 rounded-lg border border-gray-300 shadow-sm">
            <button onclick={() => changeDate(-1)} class="p-1 hover:bg-gray-100 rounded text-gray-600" title="Previous Day">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
            </button>
            
            <input 
                type="date" 
                value={currentDate} 
                min="2021-01-01" 
                max="2021-12-31"
                onchange={(e) => updateDate(e.currentTarget.value)}
                class="border-0 py-1 px-2 text-gray-900 focus:ring-0 text-sm font-medium cursor-pointer"
            />

            <button onclick={() => changeDate(1)} class="p-1 hover:bg-gray-100 rounded text-gray-600" title="Next Day">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
            </button>
        </div>
    </div>

    <div class="flex-grow overflow-y-auto pr-2 scrollbar-hide pb-10">
        {#if stocks.length === 0}
            <div class="flex flex-col items-center justify-center py-20 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                <div class="bg-gray-200 p-3 rounded-full mb-3">
                    <svg class="w-6 h-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900">Market Closed</h3>
                <p class="text-gray-500 mb-4 text-sm max-w-md text-center">
                    No trading data found for <strong>{currentDate}</strong>. It might be a weekend or market holiday.
                </p>
                <div class="flex gap-2">
                    <button onclick={() => changeDate(-1)} class="text-xs bg-white border border-gray-300 px-3 py-1.5 rounded hover:bg-gray-50 font-medium">
                        &larr; Prev Day
                    </button>
                    <button onclick={() => changeDate(1)} class="text-xs bg-white border border-gray-300 px-3 py-1.5 rounded hover:bg-gray-50 font-medium">
                        Next Day &rarr;
                    </button>
                </div>
            </div>
        {:else}
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each stocks as stock (stock.ticker)}
                    <StockCard {stock} />
                {/each}
            </div>
        {/if}
    </div>
</div>