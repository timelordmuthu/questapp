import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Magical Dark Theme
        void:    { DEFAULT: '#0a0a0f', 50: '#16161f', 100: '#1a1a26', 200: '#22222e' },
        arcane:  { DEFAULT: '#6b3fa0', light: '#8b5fbe', dark: '#4a2870', glow: '#a855f7' },
        gold:    { DEFAULT: '#d4a017', light: '#f0bc35', dark: '#9c750f', glow: '#fbbf24' },
        ember:   { DEFAULT: '#e05c2e', light: '#f0734a', dark: '#b04420' },
        rune:    { DEFAULT: '#3b82f6', glow: '#60a5fa' },
        mist:    { DEFAULT: '#94a3b8', dark: '#64748b', light: '#cbd5e1' },
        surface: { DEFAULT: '#12121a', raised: '#1a1a26', border: '#2a2a3e' },
      },
      fontFamily: {
        display: ['"Cinzel"', 'Georgia', 'serif'],
        body:    ['"Inter"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        arcane: '0 0 20px rgba(107, 63, 160, 0.4)',
        gold:   '0 0 20px rgba(212, 160, 23, 0.4)',
        rune:   '0 0 15px rgba(59, 130, 246, 0.3)',
        inner:  'inset 0 1px 0 rgba(255,255,255,0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow':       'glow 2s ease-in-out infinite alternate',
        'float':      'float 6s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%':   { boxShadow: '0 0 5px rgba(107,63,160,0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(107,63,160,0.6)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
