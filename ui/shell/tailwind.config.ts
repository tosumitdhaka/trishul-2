import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Trishul design tokens
        brand: {
          50:  '#f0f4ff',
          100: '#e0e9ff',
          500: '#3b5bdb',
          600: '#2f4ac7',
          700: '#2540b0',
          900: '#1a2d80',
        },
        severity: {
          critical: '#e03131',
          major:    '#f76707',
          minor:    '#f59f00',
          warning:  '#74c0fc',
          cleared:  '#2f9e44',
          info:     '#6c757d',
        },
        surface: {
          50:  '#f8f9fa',
          100: '#f1f3f5',
          200: '#e9ecef',
          800: '#1c1c2e',
          900: '#12121f',
          950: '#0a0a14',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config;
