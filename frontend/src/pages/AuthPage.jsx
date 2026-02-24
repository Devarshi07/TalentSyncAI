import { useState } from 'react';
import {
  Box, Paper, Typography, TextField, Button, Divider, Alert, Link,
  InputAdornment, IconButton, CircularProgress,
} from '@mui/material';
import {
  Visibility, VisibilityOff, Google as GoogleIcon,
  WorkOutline,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
  const { login, signup, googleLogin } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPwd, setShowPwd] = useState(false);

  const [form, setForm] = useState({ username: '', email: '', password: '' });

  const handleChange = (e) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) {
        await login(form.username, form.password);
      } else {
        await signup(form.username, form.email, form.password);
      }
    } catch (err) {
      const msg = err.response?.data?.detail
        || err.response?.data?.errors?.map((e) => e.msg).join(', ')
        || 'Something went wrong';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggle = () => {
    setIsLogin((p) => !p);
    setError('');
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        background: 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.12), transparent), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(99,102,241,0.04), transparent)',
        p: 2,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: 440, p: 4, border: '1px solid', borderColor: 'divider',
          borderRadius: 3,
        }}
      >
        {/* Logo */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
          <Box
            sx={{
              width: 38, height: 38, borderRadius: 2, bgcolor: 'primary.main',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <WorkOutline sx={{ color: 'white', fontSize: 22 }} />
          </Box>
          <Typography variant="h6" fontWeight={700}>Job Assistant</Typography>
        </Box>

        <Typography variant="h5" sx={{ mt: 2.5, mb: 0.3 }}>
          {isLogin ? 'Welcome back' : 'Create your account'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {isLogin
            ? 'Sign in to continue your job search journey'
            : 'Start your AI-powered career assistant'}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            label="Username" name="username" value={form.username}
            onChange={handleChange} sx={{ mb: 2 }} autoFocus autoComplete="username"
          />
          {!isLogin && (
            <TextField
              label="Email" name="email" type="email" value={form.email}
              onChange={handleChange} sx={{ mb: 2 }} autoComplete="email"
            />
          )}
          <TextField
            label="Password" name="password" value={form.password}
            onChange={handleChange} sx={{ mb: 2.5 }}
            type={showPwd ? 'text' : 'password'}
            autoComplete={isLogin ? 'current-password' : 'new-password'}
            placeholder={isLogin ? '' : 'Min 8 chars, 1 letter, 1 number'}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPwd((p) => !p)} edge="end" size="small">
                    {showPwd ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit" variant="contained" fullWidth size="large"
            disabled={loading}
            sx={{ mb: 2, py: 1.3 }}
          >
            {loading ? (
              <CircularProgress size={22} color="inherit" />
            ) : isLogin ? 'Sign In' : 'Create Account'}
          </Button>
        </Box>

        <Divider sx={{ my: 2, fontSize: '0.8rem', color: 'text.disabled' }}>
          or continue with
        </Divider>

        <Button
          variant="outlined" fullWidth size="large" onClick={googleLogin}
          startIcon={<GoogleIcon />}
          sx={{
            mb: 3, py: 1.2, borderColor: '#444',
            color: 'text.primary', '&:hover': { borderColor: '#666', bgcolor: '#1a1a27' },
          }}
        >
          Google
        </Button>

        <Typography variant="body2" textAlign="center" color="text.secondary">
          {isLogin ? "Don't have an account? " : 'Already have an account? '}
          <Link
            component="button" variant="body2" onClick={toggle}
            sx={{ color: 'primary.main', fontWeight: 600, verticalAlign: 'baseline' }}
          >
            {isLogin ? 'Create one' : 'Sign in'}
          </Link>
        </Typography>
      </Paper>
    </Box>
  );
}
