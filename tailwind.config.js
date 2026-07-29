/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Arial', 'sans-serif'],
      },
      colors: {
        /* BADC Brand Green Palette */
        'primary': '#059669',             /* Emerald 600 - Primary Brand */
        'primary-container': '#10b981',   /* Emerald 500 - Secondary Green */
        'primary-hover': '#047857',       /* Emerald 700 - Hover State */
        'primary-fixed': '#d1fae5',       /* Emerald 100 - Light Accent */
        'primary-fixed-dim': '#a7f3d0',   /* Emerald 200 */
        'on-primary': '#ffffff',          /* White text on primary */
        'on-primary-container': '#064e3b',/* Emerald 900 - Dark text on light green */

        /* Neutral Surface & Background Colors */
        'background': '#f8fafc',          /* Slate 50 */
        'surface': '#ffffff',             /* Pure White */
        'surface-container': '#f1f5f9',   /* Slate 100 */
        'surface-container-high': '#e2e8f0',/* Slate 200 */
        
        /* Typography & Borders */
        'on-surface': '#0f172a',          /* Slate 900 */
        'on-surface-variant': '#64748b',  /* Slate 500 */
        'outline': '#94a3b8',             /* Slate 400 */
        'outline-variant': '#e2e8f0',     /* Slate 200 */

        /* Alerts & System States */
        'error': '#ef4444',               /* Red 500 */
        'error-container': '#fef2f2',     /* Red 50 */
        'on-error': '#ffffff',
        'on-error-container': '#991b1b',  /* Red 800 */
      },
      borderRadius: { 
        card: '16px' 
      }
    },
  },
  plugins: [],
}