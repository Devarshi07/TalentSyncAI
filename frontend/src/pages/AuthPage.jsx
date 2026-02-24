import { useState } from 'react';
import {
  Box, Paper, Typography, TextField, Button, Divider, Alert, Link,
  InputAdornment, IconButton, CircularProgress,
} from '@mui/material';
import { Visibility, VisibilityOff, Google as GoogleIcon } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const MotionPaper = motion.create(Paper);
const MotionBox = motion.create(Box);

export default function AuthPage() {
  const { login, signup, googleLogin } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '' });

  const handleChange = (e) => { setForm((p) => ({ ...p, [e.target.name]: e.target.value })); setError(''); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) await login(form.username, form.password);
      else await signup(form.username, form.email, form.password);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.errors?.map((e) => e.msg).join(', ') || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const toggle = () => { setIsLogin((p) => !p); setError(''); };

  return (
    <Box
      sx={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        bgcolor: 'background.default', position: 'relative', overflow: 'hidden', p: 2,
      }}
    >
      {/* Animated background orbs */}
      <motion.div
        animate={{ x: [0, 30, -20, 0], y: [0, -40, 20, 0], scale: [1, 1.1, 0.95, 1] }}
        transition={{ duration: 15, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute', top: '-20%', left: '-10%',
          width: 600, height: 600, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
          filter: 'blur(40px)', pointerEvents: 'none',
        }}
      />
      <motion.div
        animate={{ x: [0, -25, 15, 0], y: [0, 30, -25, 0], scale: [1, 0.95, 1.05, 1] }}
        transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut', delay: 3 }}
        style={{
          position: 'absolute', bottom: '-15%', right: '-5%',
          width: 500, height: 500, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(34,197,94,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)', pointerEvents: 'none',
        }}
      />

      <MotionPaper
        elevation={0}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        sx={{
          width: 440, p: 4, border: '1px solid', borderColor: 'divider',
          borderRadius: 4, position: 'relative', zIndex: 1,
          backdropFilter: 'blur(20px)', bgcolor: 'rgba(17,17,24,0.85)',
        }}
      >
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2, mb: 0.5 }}>
            <Box
              sx={{
                width: 40, height: 40, borderRadius: 2.5,
                background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 4px 15px rgba(99,102,241,0.3)',
              }}
            >
              <Typography sx={{ color: 'white', fontSize: 16, fontWeight: 800 }}>TS</Typography>
            </Box>
            <Typography variant="h6" fontWeight={700}>TalentSync AI</Typography>
          </Box>
        </motion.div>

        <AnimatePresence mode="wait">
          <motion.div
            key={isLogin ? 'login' : 'signup'}
            initial={{ opacity: 0, x: isLogin ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: isLogin ? 20 : -20 }}
            transition={{ duration: 0.3 }}
          >
            <Typography variant="h5" sx={{ mt: 2.5, mb: 0.3, fontWeight: 700 }}>
              {isLogin ? 'Welcome back' : 'Create your account'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {isLogin ? 'Sign in to continue your career journey' : 'Start your AI-powered career assistant'}
            </Typography>

            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
                  <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>
                </motion.div>
              )}
            </AnimatePresence>

            <Box component="form" onSubmit={handleSubmit}>
              <TextField label="Username" name="username" value={form.username} onChange={handleChange} sx={{ mb: 2 }} autoFocus autoComplete="username" />
              {!isLogin && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} transition={{ duration: 0.2 }}>
                  <TextField label="Email" name="email" type="email" value={form.email} onChange={handleChange} sx={{ mb: 2 }} autoComplete="email" />
                </motion.div>
              )}
              <TextField
                label="Password" name="password" value={form.password} onChange={handleChange} sx={{ mb: 2.5 }}
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
                type="submit" variant="contained" fullWidth size="large" disabled={loading}
                sx={{
                  mb: 2, py: 1.3,
                  background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                  boxShadow: '0 4px 15px rgba(99,102,241,0.25)',
                  '&:hover': { boxShadow: '0 6px 20px rgba(99,102,241,0.4)', transform: 'translateY(-1px)' },
                  transition: 'all 0.2s ease',
                }}
              >
                {loading ? <CircularProgress size={22} color="inherit" /> : isLogin ? 'Sign In' : 'Create Account'}
              </Button>
            </Box>

            <Divider sx={{ my: 2, fontSize: '0.8rem', color: 'text.disabled' }}>or continue with</Divider>

            <Button
              variant="outlined" fullWidth size="large" onClick={googleLogin} startIcon={<GoogleIcon />}
              sx={{
                mb: 3, py: 1.2, borderColor: '#333', color: 'text.primary',
                '&:hover': { borderColor: '#555', bgcolor: 'rgba(255,255,255,0.03)', transform: 'translateY(-1px)' },
                transition: 'all 0.2s ease',
              }}
            >
              Google
            </Button>

            <Typography variant="body2" textAlign="center" color="text.secondary">
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <Link component="button" variant="body2" onClick={toggle}
                sx={{ color: 'primary.main', fontWeight: 600, verticalAlign: 'baseline', '&:hover': { color: 'primary.light' } }}>
                {isLogin ? 'Create one' : 'Sign in'}
              </Link>
            </Typography>
          </motion.div>
        </AnimatePresence>
      </MotionPaper>
    </Box>
  );
}
