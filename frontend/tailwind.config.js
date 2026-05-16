/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx,mdx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Cairo', 'Tajawal', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50:  '#FFF8E7',
          100: '#FDECC1',
          200: '#F9D789',
          300: '#F2BC4B',
          400: '#E8A21F',
          500: '#C68512',
          600: '#9A6710',
          700: '#704A0E',
          800: '#4A300B',
          900: '#2A1B07',
        },
        bg: {
          base:   '#0B0F19',
          panel:  '#121826',
          card:   '#161D2E',
          border: '#232C44',
        },
      },
      boxShadow: {
        soft: '0 4px 20px -2px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
};
