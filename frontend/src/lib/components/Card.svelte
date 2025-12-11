<script lang="ts">
	import Icon from "./Icon.svelte";

    // ... your script block remains the same
    const {
        class: extraClasses = '',
        date = '',
        link = '',
        image = '',
        title = '',
        description = '',
        tags = [] as string[],
        actions = null,
        ...restProps
    } = $props<{
        class?: string;
        date?: string;
        link?: string;
        image?: string;
        title?: string;
        description?: string;
        tags?: string[];
        actions?: Svelte5.Snippet;
        [key: string]: any;
    }>();
</script>

<div class={`@container flex flex-col overflow-visible group ${extraClasses}`} {...restProps}>
    <a href={link}>
        <div class="border-t-2 border-transparent flex-grow @lg:rounded-xl @lg:hover:bg-neutral-800 @lg:hover:border-neutral-700 @lg:hover:shadow-lg @lg:p-4 transition-all">
            <div class="flex flex-col-reverse @xl:flex-row @xl:items-start">
                {#if image}
                    <img 
                        src={image} 
                        alt={title} 
                        loading="lazy"
                        class="aspect-video w-4/5 max-w-12 rounded-sm border border-2 border-neutral-500 group-hover:border-neutral-400 object-cover @xl:mr-4 @xl:mt-2  @xl:w-[25%]" 
                    />
                {/if}

                <div class="flex flex-col flex-grow">
                    <div class="flex justify-between items-baseline mb-1">
                        {#if title}
                            <h3 class="text-lg @xl:text-xl @4xl:text-2xl font-semibold text-main-200 mr-2 pb-0!">{title}</h3>
                        {/if}
                        <Icon name="arrow-up-right" class="w-4 h-4 text-neutral-300 group-hover:text-main-200 group-hover:-translate-y-1 transition-all w-[5%]" />
                    </div>
                    {#if date}
                        <p class="text-sm text-neutral-400 mb-2 w-full xl:text-base">{date}</p>
                    {/if}

                    {#if description}
                        <p class="text-neutral-200 text-base @xl:text-lg @4xl:text-lg text-neutral-100 mb-2 flex-grow">{description}</p>
                    {/if}
                    {#if tags.length > 0}
                        <div class="flex flex-wrap gap-2 mb-4 @xl:mb-0">
                            {#each tags as tag}
                                <span class="bg-gradient-secondary text-secondary-900 text-sm px-2 py-1 rounded-lg">{tag}</span>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </a>
</div>