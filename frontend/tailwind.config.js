module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#6c63ff', dark: '#5a52e0' },
        accent: { DEFAULT: '#00d4aa' },
        bg: { primary: '#0a0a0f', secondary: '#111118', card: '#16161f' },
        border: { DEFAULT: '#2a2a3a' },
      },
      fontFamily: {
        sans: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
