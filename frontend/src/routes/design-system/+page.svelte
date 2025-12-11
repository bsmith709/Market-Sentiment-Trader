<script lang="ts">
  // An array of Tailwind CSS background color classes.
  // Using the full class name ensures Tailwind's JIT compiler will include them in the final CSS.
  import Button from '$lib/components/Button.svelte';
  import Icon from '$lib/components/Icon.svelte';
  import Card from '$lib/components/Card.svelte';

  const palettes = [
    {
      name: 'Main Colors',
      colors: [
        { name: 'Main-100', class: 'bg-main-100' },
        { name: 'Main-200', class: 'bg-main-200' },
        { name: 'Main-300', class: 'bg-main-300' },
        { name: 'Main-400', class: 'bg-main-400' },
        { name: 'Main-500', class: 'bg-main-500' },
        { name: 'Main-600', class: 'bg-main-600' },
        { name: 'Main-700', class: 'bg-main-700' },
        { name: 'Main-800', class: 'bg-main-800' },
        { name: 'Main-900', class: 'bg-main-900' }
      ]
    },
    {
      name: 'Secondary Colors',
      colors: [
        { name: 'Secondary-100', class: 'bg-secondary-100' },
        { name: 'Secondary-200', class: 'bg-secondary-200' },
        { name: 'Secondary-300', class: 'bg-secondary-300' },
        { name: 'Secondary-400', class: 'bg-secondary-400' },
        { name: 'Secondary-500', class: 'bg-secondary-500' },
        { name: 'Secondary-600', class: 'bg-secondary-600' },
        { name: 'Secondary-700', class: 'bg-secondary-700' },
        { name: 'Secondary-800', class: 'bg-secondary-800' },
        { name: 'Secondary-900', class: 'bg-secondary-900' }
      ]
    },
    {
      name: 'Neutral Colors',
      colors: [
        { name: 'Neutral-100', class: 'bg-neutral-100' },
        { name: 'Neutral-200', class: 'bg-neutral-200' },
        { name: 'Neutral-300', class: 'bg-neutral-300' },
        { name: 'Neutral-400', class: 'bg-neutral-400' },
        { name: 'Neutral-500', class: 'bg-neutral-500' },
        { name: 'Neutral-600', class: 'bg-neutral-600' },
        { name: 'Neutral-700', class: 'bg-neutral-700' },
        { name: 'Neutral-800', class: 'bg-neutral-800' },
        { name: 'Neutral-900', class: 'bg-neutral-900' }
      ]
    },
    {
      name: 'Semantic Success',
      colors: [
        { name: 'Success-100', class: 'bg-semantic-green-100' },
        { name: 'Success-200', class: 'bg-semantic-green-200' },
        { name: 'Success-300', class: 'bg-semantic-green-300' },
        { name: 'Success-400', class: 'bg-semantic-green-400' },
        { name: 'Success-500', class: 'bg-semantic-green-500' },
        { name: 'Success-600', class: 'bg-semantic-green-600' },
        { name: 'Success-700', class: 'bg-semantic-green-700' },
        { name: 'Success-800', class: 'bg-semantic-green-800' },
        { name: 'Success-900', class: 'bg-semantic-green-900' },
      ]
    },
    {
      name: 'Semantic Warning',
      colors: [
        { name: 'Warning-100', class: 'bg-semantic-yellow-100' },
        { name: 'Warning-200', class: 'bg-semantic-yellow-200' },
        { name: 'Warning-300', class: 'bg-semantic-yellow-300' },
        { name: 'Warning-400', class: 'bg-semantic-yellow-400' },
        { name: 'Warning-500', class: 'bg-semantic-yellow-500' },
        { name: 'Warning-600', class: 'bg-semantic-yellow-600' },
        { name: 'Warning-700', class: 'bg-semantic-yellow-700' },
        { name: 'Warning-800', class: 'bg-semantic-yellow-800' },
        { name: 'Warning-900', class: 'bg-semantic-yellow-900' },
      ]
    },
    {
      name: 'Semantic Error',
      colors: [
        { name: 'Error-100', class: 'bg-semantic-red-100' },
        { name: 'Error-200', class: 'bg-semantic-red-200' },
        { name: 'Error-300', class: 'bg-semantic-red-300' },
        { name: 'Error-400', class: 'bg-semantic-red-400' },
        { name: 'Error-500', class: 'bg-semantic-red-500' },
        { name: 'Error-600', class: 'bg-semantic-red-600' },
        { name: 'Error-700', class: 'bg-semantic-red-700' },
        { name: 'Error-800', class: 'bg-semantic-red-800' },
        { name: 'Error-900', class: 'bg-semantic-red-900' }
      ]
    },
  ];

  const fontScale = [
    { name: 'XS', class: 'text-xs' },
    { name: 'SM', class: 'text-sm' },
    { name: 'Base', class: 'text-base' },
    { name: 'LG', class: 'text-lg' },
    { name: 'XL', class: 'text-xl' },
    { name: '2XL', class: 'text-2xl' },
    { name: '3XL', class: 'text-3xl' },
    { name: '4XL', class: 'text-4xl' },
    { name: '5XL', class: 'text-5xl' },
    { name: '6XL', class: 'text-6xl' },
    { name: '7XL', class: 'text-7xl' }
  ];

  const fontStyles = [
    { name: 'Extra Light', class: 'font-extralight' },
    { name: 'Light', class: 'font-light' },
    { name: 'Normal', class: 'font-normal' },
    { name: 'Medium', class: 'font-medium' },
    { name: 'Semi Bold', class: 'font-semibold' },
    { name: 'Bold', class: 'font-bold' },
    { name: 'Extra Bold', class: 'font-extrabold' },
  ];

  const lineHeights = [
    { name: 'Tight', class: 'leading-tight' },
    { name: 'Snug', class: 'leading-snug' },
    { name: 'Normal', class: 'leading-normal' },
    { name: 'Relaxed', class: 'leading-relaxed' },
    { name: 'Loose', class: 'leading-loose' }
  ];

  const letterSpacing = [
    { name: 'Tight', class: 'tracking-tighter' },
    { name: 'Normal', class: 'tracking-normal' },
    { name: 'Wide', class: 'tracking-wide' },
    { name: 'Wider', class: 'tracking-wider' },
    { name: 'Widest', class: 'tracking-widest' }
  ];

  const spacingScale = [
    { name: 'px', class: 'w-px' },
    { name: '1', class: 'w-1' },
    { name: '2', class: 'w-2' },
    { name: '3', class: 'w-3' },
    { name: '4', class: 'w-4' },
    { name: '5', class: 'w-5' },
    { name: '6', class: 'w-6' },
    { name: '7', class: 'w-7' },
    { name: '8', class: 'w-8' },
    { name: '9', class: 'w-9' },
    { name: '10', class: 'w-10' },
    { name: '11', class: 'w-11' },
    { name: '12', class: 'w-12' },
    { name: '13', class: 'w-13' },
    { name: '14', class: 'w-14' },
    { name: '15', class: 'w-15' },
    { name: '16', class: 'w-16' }
  ];

  const borderWidths = [
    { name: '0px', class: 'border-0' },
    { name: '2px', class: 'border-2' },
    { name: '4px', class: 'border-4' },
    { name: '8px', class: 'border-8' }
  ];

  const gradients = [
    { name: 'Main', class: 'bg-gradient-main' },
    { name: 'Secondary', class: 'bg-gradient-secondary' }
  ];

  const buttons = {
    variant: ['primary', 'secondary', 'outline', 'ghost', 'link'],
    size: ['icon', 'sm', 'md', 'lg']
  }

</script>

<main class="min-h-screen w-full max-w-7xl mx-auto p-4 sm:p-5 lg:p-6">

  <!-- Main header -->
  <header class="text-center">
    <h1 class="text-2xl sm:text-5xl lg:text-6xl xl:text-7xl font-extrabold text-gradient-main tracking-wide mb-6 sm:mt-6 sm:mb-8">
      Portfolio Design System
    </h1>
  </header>

  <!-- Color Palettes Section -->
  <section class="mb-6 sm:mb-10">
    <!-- Section header -->
    <h2 class="text-xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-center text-gradient-secondary mb-4">Color Palettes</h2>

    <!-- Color Palettes -->
     {#each palettes as palette}
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">{palette.name}</h3>
      <div class="grid grid-cols-5 sm:grid-cols-9 gap-3 sm:gap-4 mb-4">
        {#each palette.colors as color}
            <button class="relative group" aria-label={color.name} tabindex="0">

              <span class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 whitespace-nowrap bg-neutral-900 text-neutral-100 text-xs sm:text-sm md:text-base font-semibold px-2 py-1 rounded-md opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity duration-300 ease-in-out pointer-events-none">
                {color.name}
              </span>

              <!-- The main color splotch -->
              <div 
                class="aspect-square shadow-lg rounded-xl transition-all duration-300 ease-in-out group-hover:scale-110 group-hover:shadow-xl group-focus:scale-110 group-focus:shadow-xl {color.class}"
              ></div>
              
              <!-- A subtle border effect on hover/focus -->
              <div class="absolute rounded-xl inset-0 border-4 border-transparent group-hover:border-white/50 group-focus:border-white/50 transition-all duration-300"></div>
            </button>
        {/each}
      </div>
    {/each}
  </section>


  <!-- Typography Section -->
  <section class="mb-6 sm:mb-10">

    <!-- Section header -->
    <h2 class="text-xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-center text-gradient-secondary mb-4"> Typography</h2>

    <!-- Font Scale -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Font Scale</h3>
      <div class="space-y-6 text-center">
        {#each fontScale as font}
          <div class="{font.class}">
            <p class="font-semibold">{font.name} - The quick brown fox jumps over the lazy dog.</p>
          </div>
        {/each}
      </div>
    </div>

    <!-- Font Weights -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Font Weights</h3>
      <div class="space-y-6 text-center">
        {#each fontStyles as style}
          <div class="grid grid-cols-2 gap-7 {style.class}">
              <p>{style.name} - The quick brown fox jumps over the lazy dog.</p> <p class="italic">{style.name} Italic - The quick brown fox jumps over the lazy dog.</p>
          </div>
        {/each}
      </div>
    </div>

    <!-- Line Heights -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Line Heights</h3>
      <div class="grid grid-cols-2 gap-4 text-center items-start">
        {#each lineHeights as line}
          <div>
              <p class="font-extrabold text-gradient-secondary">{line.name}</p> <p class="{line.class}">The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog. The quick brown fox jumps over the lazy dog.</p>
          </div>
        {/each}
      </div>
    </div>

    <!-- Letter Spacing -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Letter Spacing</h3>
      <div class="grid grid-cols-2 gap-4 text-center">
        {#each letterSpacing as letter}
          <div class="{letter.class}">
              <p class="font-extrabold text-gradient-secondary">{letter.name}</p> <p>The quick brown fox jumps over the lazy dog.</p>
          </div>
        {/each}
      </div>
    </div>
  </section> 

  <section class="mb-6 sm:mb-10">
    <h2 class="text-xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-center text-gradient-secondary mb-4">Spacing and Borders</h2>

    <!-- Spacing Scale -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Spacing Scale</h3>
      <div class="overflow-x-auto overflow-y-hidden grid grid-cols-[auto_1fr] gap-6">
        {#each spacingScale as space}
          <p class="font-semibold">{space.name}: </p>
          <div class="bg-neutral-500 h-5 {space.class}"></div>
        {/each}
      </div>
    </div>

    <!-- Border Widths -->
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Border Widths</h3>
      <div class="grid grid-cols-4 gap-6 sm:gap-7 lg:gap-8">
        {#each borderWidths as border}
          <div class="text-center">
            <p class="font-semibold mb-2">{border.name}</p>
            <div class="bg-neutral-700 border-neutral-500 w-full aspect-square border {border.class}"></div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <section class="mb-6 sm:mb-10">

    <!-- Section header -->
    <h2 class="text-xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-center text-gradient-secondary mb-4">Gradients</h2>

    <!-- Gradients -->
    <div class="mb-7">
      <div class="grid grid-cols-2 gap-6 sm:gap-7 lg:gap-8">
        {#each gradients as gradient}
          <div class="text-center">
            <p class="font-semibold text-gradient-secondary mb-4">{gradient.name}</p>
            <div class="h-10 {gradient.class} rounded-lg"></div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <section class="mb-6 sm:mb-10">
    <h2 class="text-xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold text-center text-gradient-secondary mb-4">Components</h2>

    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Buttons</h3>
      <div class="grid grid-cols-[auto_1fr] gap-6 items-center">
        {#each buttons.size as size}
        <p class="font-semibold text-gradient-secondary">{size}:</p>
        <div class="flex flex-wrap items-center gap-4">
            {#each buttons.variant as variant}
              {#if size === 'icon'}
                <Button {variant} {size}><div class="w-full h-full shrink-0"><Icon name="arrow-right" /></div></Button>
              {:else}
                {#if size === 'sm'}
                  <Button {variant} {size}><span>{variant.charAt(0).toUpperCase() + variant.slice(1)} Button</span><Icon name="arrow-right" class="h-3 w-3"></Icon></Button>
                {:else if size === 'md'}
                  <Button {variant} {size}><span>{variant.charAt(0).toUpperCase() + variant.slice(1)} Button</span><Icon name="arrow-right" class="h-4 w-4"></Icon></Button>
                {:else if size === 'lg'}
                  <Button {variant} {size}><span>{variant.charAt(0).toUpperCase() + variant.slice(1)} Button</span><Icon name="arrow-right" class="h-5 w-5"></Icon></Button>
                {/if}

              {/if}
            {/each}
        </div>
        {/each}
      </div> 
    </div>
  
    <div class="mb-7">
      <h3 class="text-lg sm:text-xl lg:text-2xl xl:text-3xl font-semibold text-secondary-300 mb-4">Cards</h3>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Card 
          date="Date — Date"
          title="Card Title" 
          description="This is a description for the card component. It provides additional context about the card's content." 
          tags={['Tag1', 'Tag2', 'Tag3']}
        >
          {#snippet actions()}
            <Button 
              variant="link" 
              class="text-sm @md:text-base @xl:text-lg @4xl:text-xl"
            >
              Learn More
              <Icon name="link" class="h-3 w-3 sm:h-4 sm:w-4" />
            </Button>
          {/snippet}
        </Card>

        <Card 
          title="Card Title" 
          description="This is a description for the card component. It provides additional context about the card's content." 
          tags={['Tag1', 'Tag2', 'Tag3']}
        >
          {#snippet actions()}
            <Button 
              variant="link" 
              class="text-sm @md:text-base @xl:text-lg @4xl:text-xl"
            >
              Learn More
              <Icon name="link" class="h-3 w-3 sm:h-4 sm:w-4" />
            </Button>
          {/snippet}
        </Card>
      </div>
      <Card 
        title="Card Title" 
        description="This is a description for the card component. It provides additional context about the card's content." 
        tags={['Tag1', 'Tag2', 'Tag3']}
      >
        {#snippet actions()}
          <Button 
            variant="link" 
            class="text-sm @md:text-base @xl:text-lg @4xl:text-xl"
          >
            Learn More
            <Icon name="link" class="h-3 w-3 sm:h-4 sm:w-4" />
          </Button>
        {/snippet}
      </Card>
    </div>
  </section>
</main>