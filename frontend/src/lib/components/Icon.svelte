<script lang="ts">
    type IconName = 'arrow-down-tray' | 'arrow-right' | 'arrow-left' | 'github' | 'link' | 'handshake' | 'arrow-up-right' | 'chevron-down' | 'linkedin' | null;

    const {
        name = null as IconName,
        class: extraClasses = '', // Rename `class` prop to avoid conflict with the HTML attribute
        ...restProps // Capture any other properties (like onclick, id, etc.)
    } = $props<{
        name?: IconName;
        class?: string;
        [key: string]: any; // Allow any other attributes
    }>();

    type IconDefinition = {
        paths: string;
        viewBox?: string;
        fill?: string;
        stroke?: string;
        strokeWidth?: string;
    };

    const icons = new Map<IconName, IconDefinition>([
        [
            'arrow-down-tray',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />',
            }
        ],
        [
            'arrow-right',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />',
            }
        ],
        [
            'arrow-left',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />'
            }
        ],
        [
            'github',
            {
                paths: '<path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>',
                fill: 'currentColor', // Override fill
                stroke: 'none',       // Override stroke
            }
        ],
        [
            'link',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />',
                strokeWidth: '1.5',
            }
        ],
        [
            'handshake',
            {
                paths: '<g transform="translate(0 225) scale(0.1 -0.1)"><path fill-rule="evenodd" d="M0 2250 H2250 V0 H0 Z M870 1791 c0 -4 -52 -300 -115 -656 -63 -357 -115 -656 -115 -667 0 -16 10 -18 124 -18 110 0 125 2 130 18 2 9 17 89 31 177 15 88 32 168 39 177 6 9 66 62 134 117 85 71 122 96 122 84 0 -16 -80 -470 -96 -546 l-6 -27 130 0 130 0 12 68 c6 37 59 340 119 675 l107 607 -127 0 -128 0 -10 -52 c-6 -29 -27 -145 -47 -258 -19 -112 -37 -206 -38 -208 -13 -13 -261 -210 -263 -209 -2 2 111 643 123 700 l6 27 -131 0 c-72 0 -131 -4 -131 -9z"/></g>',
                viewBox: '0 0 225 225',
                fill: 'currentColor',
                stroke: 'none'
            }
        ],
        [
            'arrow-up-right',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 19.5 15-15m0 0H8.25m11.25 0v11.25" />',
            }
        ],
        [
            'chevron-down',
            {
                paths: '<path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />',
            }
        ],
        [
            'linkedin',
            {
                paths: '<path fill-rule="evenodd" d="M20.3292112,2 C21.2519624,2 22,2.74752185 22,3.67078882 L22,20.3292112 C22,21.2519624 21.2524781,22 20.3292112,22 L3.67078882,22 C2.74803764,22 2,21.2524781 2,20.3292112 L2,3.67078882 C2,2.74803764 2.74752185,2 3.67078882,2 L20.3292112,2 Z M15.51875,9.5 C14.0993287,9.5 13.128125,10.127356 12.6956992,10.8562567 L12.625,10.9858333 L12.625,9.625 L9.91666667,9.625 L9.91666667,19.2083333 L12.8333333,19.2083333 L12.8333333,14.56625 C12.8333333,13.0104167 13.40625,12.0208333 14.7833333,12.0208333 C15.7330797,12.0208333 16.1315784,12.8606664 16.1644352,14.3580086 L16.1666667,14.56625 L16.1666667,19.2083333 L19.0833333,19.2083333 L19.0833333,13.9154167 C19.0833333,11.0575 18.3995833,9.5 15.51875,9.5 Z M7.83333333,9.5 L4.91666667,9.5 L4.91666667,19.0833333 L7.83333333,19.0833333 L7.83333333,9.5 Z M6.375,4.5 C5.33958333,4.5 4.5,5.33958333 4.5,6.375 C4.5,7.41041667 5.33958333,8.25 6.375,8.25 C7.41041667,8.25 8.25,7.41041667 8.25,6.375 C8.25,5.33958333 7.41041667,4.5 6.375,4.5 Z"/>',
                fill: 'currentColor',
                stroke: 'none',
                viewBox: "2 2 20 20",
            }
        ]
    ]);

    // Reactive statement to get the correct SVG path data.
    const icon = $derived(icons.get(name) ?? '');
</script>

{#if icon}
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox={icon.viewBox ?? '0 0 24 24'}
    fill={icon.fill ?? 'none'}
    stroke={icon.stroke ?? 'currentColor'}
    stroke-width={icon.strokeWidth ?? '2'}
    stroke-linecap="round"
    stroke-linejoin="round"
    class={extraClasses}
  >
    {@html icon.paths}
  </svg>
{/if}