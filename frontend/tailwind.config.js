/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#FCF8EA', 100: '#F7EDCC', 200: '#EEDB9D', 300: '#E4C96D',
          400: '#D7B64F', 500: '#C9A64B', 600: '#A98329', 700: '#85651F',
          800: '#624A1D', 900: '#423317',
        },
        dark: {
          bg: '#F2EEE4',
          card: '#FFFCF5',
          border: '#D8D0C0',
          muted: '#746D62',
        },
        primary: {
          DEFAULT: '#C9A64B',
          hover: '#A98329',
          light: '#E2C875',
        },
        success: {
          DEFAULT: '#22C55E',
          light: '#4ADE80',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#F87171',
        }
      }
    },
  },
  plugins: [],
}

