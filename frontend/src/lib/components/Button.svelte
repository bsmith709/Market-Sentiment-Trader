<script lang="ts">
  /**
   * A modern, reusable button component for Svelte 5, styled with Tailwind CSS.
   * It supports different visual variants, sizes, and standard button attributes.
   */

  // Define the types for the component's props for strong type safety.
  type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'custom' | string;
  type Size = 'sm' | 'md' | 'lg' | 'icon' | 'custom' | string;
  type ButtonType = 'button' | 'submit' | 'reset';

  // Use Svelte 5's $props() rune for declaring component properties.
  const {
    variant = 'custom' as Variant,
    size = 'custom' as Size,
    type = 'button' as ButtonType,
    disabled = false,
    class: extraClasses = '', // Rename `class` prop to avoid conflict with the HTML attribute
    children = null, // For button content
    ...restProps // Capture any other properties (like onclick, id, etc.)
  } = $props<{
    variant?: Variant;
    size?: Size;
    type?: ButtonType;
    disabled?: boolean;
    class?: string;
    children?: Svelte5.Snippet; // For button content
    [key: string]: any; // Allow any other attributes
  }>();

  // --- Class Definitions ---

  // Base classes applied to all buttons for a consistent foundation.
  const baseClasses = `
    inline-flex items-center justify-center gap-1 whitespace-nowrap rounded-md font-medium
    transform transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
    disabled:pointer-events-none disabled:opacity-50 hover:scale-102 active:scale-95
  `;

  // Classes for different visual styles (variants).
  const variantClasses: Record<Variant, string> = {
    primary: 'text-neutral-100 bg-gradient-main bg-[length:100%_300%] bg-no-repeat bg-center active:bg-bottom hover:bg-top',
    secondary: 'text-neutral-100 bg-gradient-secondary bg-[length:100%_300%] bg-no-repeat bg-center active:bg-bottom hover:bg-top',
    outline: 'border border-neutral-400 text-neutral-400 bg-transparent hover:bg-neutral-400 hover:border-neutral-400 hover:text-neutral-900 active:bg-neutral-500 active:border-neutral-500 active:text-neutral-900',
    ghost: 'text-neutral-400 hover:bg-neutral-700 hover:text-neutral-100 active:bg-neutral-800 active:text-neutral-500',
    link: 'text-neutral-100 underline-offset-4 hover:text-main-300 hover:underline gap-0',
    custom: '', // No predefined classes; user must provide their own via `class` prop
  };

  // Classes for different button sizes.
  const sizeClasses: Record<Size, string> = {
    sm: 'h-6 rounded-md px-3 text-xs',
    md: 'h-7 rounded-md px-4 text-base gap-2',
    lg: 'h-8 rounded-md px-5 text-lg gap-3',
    icon: 'h-5 w-5 p-1',
    custom: '', // No predefined classes; user must provide their own via `class` prop
  };

  // Reactive statement to compute the final class string.
  // It combines base, variant, size, and any extra classes passed to the component.
  let finalClasses = $derived([
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    extraClasses
  ].filter(Boolean).join(' '));

</script>

<!--
  The button element itself.
  - `type` and `disabled` attributes are bound to their respective props.
  - `class` is set to our computed `finalClasses`.
  - `{...restProps}` spreads any additional attributes or event handlers (e.g., onclick) onto the element.
-->
<button
  {type}
  class={finalClasses}
  {disabled}
  {...restProps}
>
  {@render children?.()}
</button>