/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  theme: {
    extend: {
      colors: {
        barclays: {
          navy: '#00395D',
          blue: '#00AEEF',
          gold: '#C8A951',
          teal: '#006272',
          lightblue: '#E8F4FD',
        },
        user: {
          bg: '#FAFBFC',
          surface: '#FFFFFF',
          border: '#E2E8F0',
          text: '#1A202C',
          muted: '#64748B',
          accent: '#00395D',
          highlight: '#00AEEF',
        },
        admin: {
          bg: '#0A0F1A',
          surface: '#111827',
          surface2: '#1A2235',
          border: '#1E2D45',
          text: '#F1F5F9',
          muted: '#64748B',
          accent: '#00AEEF',
          gold: '#C8A951',
        },
        risk: {
          low: '#10B981',
          medium: '#F59E0B',
          high: '#F97316',
          very_high: '#EF4444',
          low_bg: '#D1FAE5',
          medium_bg: '#FEF3C7',
          high_bg: '#FFEDD5',
          vh_bg: '#FEE2E2',
        },
        decision: {
          approve: '#10B981',
          hold: '#F59E0B',
          reject: '#EF4444',
          pending: '#6366F1',
        },
      },
      fontFamily: {
        display: ['Clash Display', 'DM Serif Display', 'serif'],
        body: ['Instrument Sans', 'Plus Jakarta Sans', 'sans-serif'],
        data: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      fontSize: {
        score: ['72px', { lineHeight: '1', letterSpacing: '-0.04em', fontWeight: '700' }],
        hero: ['48px', { lineHeight: '1.1', letterSpacing: '-0.03em', fontWeight: '600' }],
        card: ['20px', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
      },
      boxShadow: {
        'card-user': '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,57,93,0.08)',
        'card-admin': '0 0 0 1px rgba(30,45,69,0.8), 0 4px 24px rgba(0,0,0,0.4)',
        'score-glow': '0 0 40px rgba(0,174,239,0.3)',
        approve: '0 4px 20px rgba(16,185,129,0.4)',
        reject: '0 4px 20px rgba(239,68,68,0.4)',
      },
      borderRadius: {
        card: '16px',
        pill: '9999px',
        input: '10px',
      },
      animation: {
        'score-fill': 'scoreFill 1.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'fade-in': 'fadeIn 0.3s ease forwards',
        'pulse-dot': 'pulseDot 2s ease infinite',
        shimmer: 'shimmer 1.5s infinite',
      },
      keyframes: {
        scoreFill: {
          '0%': { strokeDashoffset: '440' },
          '100%': { strokeDashoffset: 'var(--score-offset)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(16px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(1.3)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      transitionTimingFunction: {
        spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
        smooth: 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
};
