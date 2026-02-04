import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Operational State Colors (from Master Dashboard spec)
        'state-idle': '#10b981',      // Green
        'state-planning': '#06b6d4',  // Cyan
        'state-running': '#3b82f6',   // Blue
        'state-waiting': '#f59e0b',   // Amber
        'state-paused': '#8b5cf6',    // Purple
        'state-error': '#ef4444',     // Red
        'state-offline': '#6b7280',   // Gray
        
        // UI Colors
        'bg-primary': '#0a0a0a',
        'bg-secondary': '#1a1a1a',
        'bg-tertiary': '#2a2a2a',
        'bg-card': '#1e1e1e',
        'border-default': '#333',
        'text-primary': '#f5f5f5',
        'text-secondary': '#a0a0a0',
        'accent-primary': '#3b82f6',
        'accent-secondary': '#06b6d4',
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
