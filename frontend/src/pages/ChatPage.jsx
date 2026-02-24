import { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, TextField, IconButton, Paper, Chip, Avatar,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon, DescriptionOutlined, AutoAwesome,
  WorkOutline, SchoolOutlined, TipsAndUpdatesOutlined,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { chatAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const MotionBox = motion.create(Box);
const MotionPaper = motion.create(Paper);

const SUGGESTIONS = [
  { icon: <DescriptionOutlined />, label: 'Resume', text: 'Tailor my resume for a Senior ML Engineer role at Google', color: '#6366f1' },
  { icon: <SchoolOutlined />, label: 'Interview', text: 'Help me prep for a Data Scientist interview at Meta', color: '#22c55e' },
  { icon: <TipsAndUpdatesOutlined />, label: 'Career', text: 'What skills should I highlight for backend engineering roles?', color: '#f59e0b' },
  { icon: <AutoAwesome />, label: 'Profile', text: 'Review my profile and suggest improvements', color: '#ec4899' },
];

const markdownStyles = {
  '& p': { m: 0, mb: 1, lineHeight: 1.7, fontSize: '0.9rem' },
  '& p:last-child': { mb: 0 },
  '& h2': { fontSize: '1.05rem', fontWeight: 700, mt: 2, mb: 0.75, color: 'primary.light' },
  '& h3': { fontSize: '0.95rem', fontWeight: 600, mt: 1.5, mb: 0.5, color: 'text.primary' },
  '& ul, & ol': { pl: 2.5, mb: 1 },
  '& li': { fontSize: '0.9rem', lineHeight: 1.7, mb: 0.3 },
  '& strong': { fontWeight: 600, color: 'text.primary' },
  '& em': { fontStyle: 'italic', color: 'text.secondary' },
  '& code': { bgcolor: 'rgba(99,102,241,0.1)', px: 0.6, py: 0.2, borderRadius: 0.5, fontSize: '0.82rem', fontFamily: 'monospace' },
  '& hr': { border: 'none', borderTop: '1px solid', borderColor: 'divider', my: 2 },
  '& a': { color: 'primary.main', textDecoration: 'underline' },
};

function MessageBubble({ msg, userInitials, index }) {
  const isUser = msg.role === 'user';
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1], delay: 0.05 }}
    >
      <Box sx={{ display: 'flex', gap: 1.5, mb: 3, maxWidth: 800, mx: 'auto', width: '100%', px: 2 }}>
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.1 }}>
          <Avatar
            sx={{
              width: 32, height: 32, fontSize: '0.75rem', fontWeight: 700, mt: 0.5,
              bgcolor: isUser ? 'primary.main' : 'rgba(99,102,241,0.1)',
              color: isUser ? 'white' : 'primary.main',
              border: isUser ? 'none' : '1px solid', borderColor: 'divider',
            }}
          >
            {isUser ? userInitials : 'TS'}
          </Avatar>
        </motion.div>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="caption" fontWeight={600}
            sx={{ color: isUser ? 'primary.main' : 'secondary.main', mb: 0.3, display: 'block', fontSize: '0.78rem' }}>
            {isUser ? 'You' : 'TalentSync AI'}
          </Typography>
          {isUser ? (
            <Typography variant="body2" sx={{ lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{msg.content}</Typography>
          ) : (
            <Box sx={markdownStyles}><ReactMarkdown>{msg.content}</ReactMarkdown></Box>
          )}
          {msg.attachments?.map((att, i) => (
            att.type === 'latex' && att.content ? (
              <MotionPaper
                key={i} variant="outlined"
                whileHover={{ scale: 1.02, borderColor: '#6366f1' }}
                whileTap={{ scale: 0.98 }}
                sx={{
                  mt: 1.5, p: 1.5, display: 'inline-flex', alignItems: 'center', gap: 1,
                  cursor: 'pointer', borderRadius: 2, transition: 'all 0.15s',
                }}
                onClick={() => {
                  const blob = new Blob([att.content], { type: 'application/x-latex' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a'); a.href = url; a.download = att.filename || 'resume.tex'; a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                <Box sx={{ width: 36, height: 36, borderRadius: 1.5, bgcolor: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <DescriptionOutlined sx={{ fontSize: 18, color: 'primary.main' }} />
                </Box>
                <Box>
                  <Typography variant="body2" fontWeight={600} fontSize="0.83rem">{att.filename || 'resume.tex'}</Typography>
                  <Typography variant="caption" color="text.disabled">Click to download LaTeX</Typography>
                </Box>
              </MotionPaper>
            ) : null
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
      <Box sx={{ display: 'flex', gap: 1.5, mb: 3, maxWidth: 800, mx: 'auto', width: '100%', px: 2 }}>
        <Avatar sx={{ width: 32, height: 32, fontSize: '0.75rem', mt: 0.5, bgcolor: 'rgba(99,102,241,0.1)', color: 'primary.main', border: '1px solid', borderColor: 'divider' }}>TS</Avatar>
        <Box sx={{ pt: 1.5, px: 1.5, pb: 1, bgcolor: 'rgba(99,102,241,0.04)', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 0.6 }}>
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ y: [0, -6, 0], opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
                style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#6366f1' }}
              />
            ))}
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}

export default function ChatPage({ threadId, initialMessages = [], onNewThreadCreated }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState(initialMessages);
  const [currentThreadId, setCurrentThreadId] = useState(threadId);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const userInitials = (user?.username || 'U')[0].toUpperCase();

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages((p) => [...p, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const { data } = await chatAPI.send(msg, currentThreadId);
      setMessages((p) => [...p, { role: 'assistant', content: data.response, attachments: data.attachments }]);
      if (data.thread_id && data.thread_id !== currentThreadId) {
        setCurrentThreadId(data.thread_id);
        if (onNewThreadCreated) onNewThreadCreated(data.thread_id);
      }
    } catch {
      setMessages((p) => [...p, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };
  const isEmpty = messages.length === 0;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Box sx={{ flex: 1, overflowY: 'auto', py: 2 }}>
        {isEmpty ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', px: 3 }}>
            {/* Animated logo */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, type: 'spring', stiffness: 200 }}
            >
              <Box sx={{
                width: 64, height: 64, borderRadius: 3, mb: 2.5,
                background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 8px 30px rgba(99,102,241,0.3)',
              }}>
                <Typography sx={{ color: 'white', fontSize: 22, fontWeight: 800 }}>TS</Typography>
              </Box>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.5 }}>
              <Typography variant="h4" fontWeight={800} sx={{ mb: 0.5 }}>
                How can I help you today?
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500 }}>
                I'm your AI career assistant. Tailor resumes, prep for interviews, and get career guidance.
              </Typography>
            </motion.div>

            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1.5, maxWidth: 580, width: '100%' }}>
              {SUGGESTIONS.map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.1, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  whileTap={{ scale: 0.97 }}
                >
                  <Paper
                    variant="outlined" onClick={() => send(s.text)}
                    sx={{
                      p: 2.5, cursor: 'pointer', borderRadius: 3, textAlign: 'left',
                      transition: 'border-color 0.2s, background 0.2s',
                      '&:hover': { borderColor: s.color, bgcolor: `${s.color}08` },
                    }}
                  >
                    <Chip
                      icon={s.icon} label={s.label} size="small"
                      sx={{
                        mb: 1.2, bgcolor: `${s.color}15`, color: s.color, fontWeight: 600,
                        fontSize: '0.72rem', '& .MuiChip-icon': { color: s.color, fontSize: 16 },
                      }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>{s.text}</Typography>
                  </Paper>
                </motion.div>
              ))}
            </Box>
          </Box>
        ) : (
          <>
            <AnimatePresence>
              {messages.map((m, i) => <MessageBubble key={i} msg={m} userInitials={userInitials} index={i} />)}
            </AnimatePresence>
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </>
        )}
      </Box>

      {/* Input area */}
      <Box sx={{ px: 2, pb: 2, pt: 1, flexShrink: 0 }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, duration: 0.5 }}>
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <Paper variant="outlined" sx={{
              display: 'flex', alignItems: 'flex-end', gap: 0.5, borderRadius: 3, p: '8px 8px 8px 16px', borderColor: 'divider',
              transition: 'all 0.2s',
              '&:focus-within': { borderColor: 'primary.main', boxShadow: '0 0 0 3px rgba(99,102,241,0.12)' },
            }}>
              <TextField inputRef={inputRef} multiline maxRows={5}
                placeholder="Ask about resume tailoring, interview prep, or career advice..."
                value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
                variant="standard" fullWidth InputProps={{ disableUnderline: true }}
                sx={{ '& .MuiInputBase-root': { fontSize: '0.9rem', py: 0.5 } }} />
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.9 }}>
                <IconButton onClick={() => send()} disabled={!input.trim() || loading}
                  sx={{
                    bgcolor: input.trim() ? 'primary.main' : 'transparent', color: input.trim() ? 'white' : 'text.disabled',
                    borderRadius: 2, width: 38, height: 38,
                    background: input.trim() ? 'linear-gradient(135deg, #6366f1, #818cf8)' : 'transparent',
                    boxShadow: input.trim() ? '0 2px 10px rgba(99,102,241,0.3)' : 'none',
                    '&:hover': { background: 'linear-gradient(135deg, #818cf8, #a5b4fc)' },
                    '&.Mui-disabled': { bgcolor: 'transparent', background: 'transparent', boxShadow: 'none' },
                  }}>
                  {loading ? <CircularProgress size={18} color="inherit" /> : <SendIcon sx={{ fontSize: 18 }} />}
                </IconButton>
              </motion.div>
            </Paper>
            <Typography variant="caption" color="text.disabled" sx={{ display: 'block', textAlign: 'center', mt: 0.75 }}>
              TalentSync AI can make mistakes. Please verify important information.
            </Typography>
          </Box>
        </motion.div>
      </Box>
    </Box>
  );
}
