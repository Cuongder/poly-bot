/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                bgMain: '#0d1117',
                bgCard: '#161b22',
                borderC: '#30363d',
                textPrimary: '#c9d1d9',
                textSecondary: '#8b949e',
                success: '#3fb950',
                danger: '#f85149',
                accent: '#58a6ff',
                warning: '#d29922'
            },
            fontFamily: {
                mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
            }
        },
    },
    plugins: [],
}
