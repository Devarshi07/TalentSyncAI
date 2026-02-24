import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#6366f1', light: '#818cf8', dark: '#4f46e5' },
    secondary: { main: '#22c55e', light: '#4ade80', dark: '#16a34a' },
    background: {
      default: '#09090f',
      paper: '#111118',
    },
    divider: '#1e1e2e',
    text: {
      primary: '#f0f0f5',
      secondary: '#9394a5',
      disabled: '#5d5e72',
    },
    error: { main: '#ef4444' },
    warning: { main: '#f59e0b' },
    success: { main: '#22c55e' },
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 500 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { backgroundColor: '#09090f' },
        '*::-webkit-scrollbar': { width: '6px' },
        '*::-webkit-scrollbar-thumb': {
          backgroundColor: '#2a2a3d',
          borderRadius: '3px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 10, padding: '10px 20px', fontSize: '0.9rem' },
        containedPrimary: {
          '&:hover': { backgroundColor: '#818cf8', transform: 'translateY(-1px)' },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', fullWidth: true, size: 'small' },
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            backgroundColor: '#0d0d14',
            '& fieldset': { borderColor: '#2a2a3d' },
            '&:hover fieldset': { borderColor: '#4a4a6a' },
            '&.Mui-focused fieldset': { borderColor: '#6366f1' },
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none', borderColor: '#1e1e2e' },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { backgroundColor: '#111118', borderRight: '1px solid #1e1e2e' },
      },
    },
  },
});

export default theme;
