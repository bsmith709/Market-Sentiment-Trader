<script lang="ts">
    let { stock } = $props<{ stock: any }>();

    // Use $derived so these update when 'stock' changes
    let change = $derived(stock.daily_close - stock.daily_open);
    let changePct = $derived((change / stock.daily_open) * 100);
    let isPositive = $derived(change >= 0);

    // Helper: Sentiment Color Logic
    function getSentimentColor(score: number) {
        if (score > 0.6) return 'text-green-600'; 
        if (score >= 0.4) return 'text-yellow-600'; 
        return 'text-red-600';
    }

    function fmtSent(val: number) {
        return (val * 100).toFixed(0) + '%';
    }
</script>

<div class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 p-4 flex flex-col gap-3">
    
    <div class="flex items-center justify-between">
        
        <div class="flex flex-col min-w-[120px]">
            <h3 class="text-xl font-black text-gray-900 leading-none tracking-tight">{stock.ticker}</h3>
            <span class="text-xs text-gray-500 font-medium truncate max-w-[140px] mt-1">{stock.company_name}</span>
        </div>

        <div class="flex items-center gap-6 text-sm font-bold">
            <div class="flex flex-col items-center">
                <span class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Reddit</span>
                <span class={getSentimentColor(stock.reddit_hype_score)}>
                    {fmtSent(stock.reddit_hype_score)}
                </span>
            </div>
            <div class="flex flex-col items-center">
                <span class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">News</span>
                <span class={getSentimentColor(stock.news_hype_score)}>
                    {fmtSent(stock.news_hype_score)}
                </span>
            </div>
        </div>

        <div class="text-right min-w-[100px]">
            <div class="text-lg font-bold text-gray-900 leading-none">${stock.daily_close.toFixed(2)}</div>
            <div class={`text-xs font-bold mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                {isPositive ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)
            </div>
        </div>
    </div>

    <div class="h-px bg-gray-100 w-full"></div>

    <div class="flex items-center justify-between text-[10px]">
        <span class="inline-flex items-center px-2 py-0.5 rounded font-medium bg-gray-100 text-gray-600 uppercase tracking-wide">
            {stock.sector}
        </span>
        <span class="text-gray-400 font-mono">
            Vol: {(stock.daily_volume / 1000000).toFixed(1)}M
        </span>
    </div>
</div>