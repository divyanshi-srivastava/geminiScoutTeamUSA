/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a1128',
          800: '#0f1b3d',
          700: '#162552',
          600: '#1d2f67',
        },
        gold: {
          500: '#c5a44e',
          400: '#d4b95e',
          300: '#e3ce6f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
