/** @type {import('tailwindcss').Config} */
export const content = [
  "./product_evaluator/ui/templates/**/*.html",
  "./product_evaluator/static/js/**/*.js"
];
export const theme = {
  extend: {
    colors: {
      'primary': {
        50: '#eef2ff',
        100: '#e0e7ff',
        200: '#c7d2fe',
        300: '#a5b4fc',
        400: '#818cf8',
        500: '#6366f1',
        600: '#4f46e5',
        700: '#4338ca',
        800: '#3730a3',
        900: '#312e81'
      },
      'secondary': {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a'
      },
      'success': {
        50: '#ecfdf5',
        100: '#d1fae5',
        200: '#a7f3d0',
        300: '#6ee7b7',
        400: '#34d399',
        500: '#10b981',
        600: '#059669',
        700: '#047857',
        800: '#065f46',
        900: '#064e3b'
      },
      'warning': {
        50: '#fffbeb',
        100: '#fef3c7',
        200: '#fde68a',
        300: '#fcd34d',
        400: '#fbbf24',
        500: '#f59e0b',
        600: '#d97706',
        700: '#b45309',
        800: '#92400e',
        900: '#78350f'
      },
      'error': {
        50: '#fef2f2',
        100: '#fee2e2',
        200: '#fecaca',
        300: '#fca5a5',
        400: '#f87171',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
        800: '#991b1b',
        900: '#7f1d1d'
      }
    },
    fontFamily: {
      'sans': ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      'display': ['Poppins', 'ui-sans-serif', 'system-ui'],
      'mono': ['Fira Code', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace']
    },
    spacing: {
      '18': '4.5rem',
      '72': '18rem',
      '84': '21rem',
      '96': '24rem',
    },
    boxShadow: {
      'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      'card-hover': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
    },
    typography: (theme) => ({
      DEFAULT: {
        css: {
          color: theme('colors.secondary.700'),
          a: {
            color: theme('colors.primary.600'),
            '&:hover': {
              color: theme('colors.primary.800'),
            },
          },
          h1: {
            color: theme('colors.primary.800'),
          },
          h2: {
            color: theme('colors.primary.700'),
          },
          h3: {
            color: theme('colors.primary.600'),
          },
          h4: {
            color: theme('colors.secondary.800'),
          },
          'code::before': {
            content: '""',
          },
          'code::after': {
            content: '""',
          },
        },
      },
    }),
  },
};
export const plugins = [
  require('@tailwindcss/typography'),
  require('@tailwindcss/forms'),
];