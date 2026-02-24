import { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, TextField, IconButton, Paper, Chip, Avatar,
  CircularProgress,
} from '@mui/material';
import {
  Send as SendIcon, DescriptionOutlined, AutoAwesome,
  WorkOutline, SchoolOutlined, TipsAndUpdatesOutlined,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { chatAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const SUGGESTIONS = [
  { icon: <DescriptionOutlined />, label: 'Resume', text: 'Tailor my resume for a Senior ML Engineer role at Google' },
  { icon: <SchoolOutlined />, label: 'Interview', text: 'Help me prep for a Data Scientist interview at Meta' },
  { icon: <TipsAndUpdatesOutlined />, label: 'Career', text: 'What skills should I highlight for backend engineering roles?' },
  { icon: <AutoAwesome />, label: 'Profile', text: 'Review my profile and suggest improvements' },
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

function MessageBubble({ msg, userInitials }) {
  const isUser = msg.role === 'user';
  return (
    <Box sx={{ display: 'flex', gap: 1.5, mb: 3, maxWidth: 800, mx: 'auto', width: '100%', px: 2 }}>
      <Avatar
        sx={{
          width: 30, height: 30, fontSize: '0.75rem', fontWeight: 600, mt: 0.5,
          bgcolor: isUser ? 'primary.main' : 'background.paper',
          color: isUser ? 'white' : 'primary.main',
          border: isUser ? 'none' : '1px solid', borderColor: 'divider',
        }}
      >
        {isUser ? userInitials : 'JA'}
      </Avatar>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="caption" fontWeight={600}
          sx={{ color: isUser ? 'primary.main' : 'secondary.main', mb: 0.3, display: 'block' }}
        >
          {isUser ? 'You' : 'Job Assistant'}
        </Typography>

        {isUser ? (
          <Typography variant="body2" sx={{ lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
            {msg.content}
          </Typography>
        ) : (
          <Box sx={markdownStyles}>
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </Box>
        )}

        {msg.attachments?.map((att, i) => (
          att.type === 'latex' && att.content ? (
            <Paper
              key={i} variant="outlined"
              sx={{
                mt: 1.5, p: 1.5, display: 'inline-flex', alignItems: 'center', gap: 1,
                cursor: 'pointer', borderRadius: 2,
                '&:hover': { borderColor: 'primary.main', bgcolor: 'rgba(99,102,241,0.04)' },
              }}
              onClick={() => {
                const blob = new Blob([att.content], { type: 'application/x-latex' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = att.filename || 'resume.tex'; a.click();
                URL.revokeObjectURL(url);
              }}
            >
              <DescriptionOutlined sx={{ fontSize: 20, color: 'primary.main' }} />
              <Box>
                <Typography variant="body2" fontWeight={600} fontSize="0.83rem">{att.filename || 'resume.tex'}</Typography>
                <Typography variant="caption" color="text.disabled">Click to download</Typography>
              </Box>
            </Paper>
          ) : null
        ))}
      </Box>
    </Box>
  );
}

function TypingIndicator() {
  return (
    <Box sx={{ display: 'flex', gap: 1.5, mb: 3, maxWidth: 800, mx: 'auto', width: '100%', px: 2 }}>
      <Avatar sx={{ width: 30, height: 30, fontSize: '0.75rem', mt: 0.5, bgcolor: 'background.paper', color: 'primary.main', border: '1px solid', borderColor: 'divider' }}>JA</Avatar>
      <Box sx={{ pt: 1 }}>
        <Box sx={{ display: 'flex', gap: 0.6 }}>
          {[0, 1, 2].map((i) => (
            <Box key={i} sx={{
              width: 7, height: 7, borderRadius: '50%', bgcolor: 'text.disabled',
              animation: 'pulse 1.4s infinite', animationDelay: `${i * 0.2}s`,
              '@keyframes pulse': { '0%,60%,100%': { transform: 'translateY(0)', opacity: 0.4 }, '30%': { transform: 'translateY(-6px)', opacity: 1 } },
            }} />
          ))}
        </Box>
      </Box>
    </Box>
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages((p) => [...p, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const { data } = await chatAPI.send(msg, currentThreadId);
      setMessages((p) => [...p, {
        role: 'assistant', content: data.response, attachments: data.attachments,
      }]);

      // If this was the first message, backend created a new thread
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const isEmpty = messages.length === 0;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Box sx={{ flex: 1, overflowY: 'auto', py: 2 }}>
        {isEmpty ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', px: 3 }}>
            <Box sx={{ width: 56, height: 56, borderRadius: 3, bgcolor: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
              <WorkOutline sx={{ color: 'white', fontSize: 28 }} />
            </Box>
            <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5 }}>How can I help you today?</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4, maxWidth: 480 }}>
              I'm your AI-powered job assistant. I can tailor your resume, prep you for interviews, and help navigate your career journey.
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1.5, maxWidth: 560, width: '100%' }}>
              {SUGGESTIONS.map((s, i) => (
                <Paper key={i} variant="outlined" onClick={() => send(s.text)}
                  sx={{ p: 2, cursor: 'pointer', borderRadius: 2.5, textAlign: 'left', transition: 'all 0.15s',
                    '&:hover': { borderColor: 'primary.main', bgcolor: 'rgba(99,102,241,0.04)', transform: 'translateY(-2px)' } }}>
                  <Chip icon={s.icon} label={s.label} size="small"
                    sx={{ mb: 1, bgcolor: 'rgba(99,102,241,0.1)', color: 'primary.light', fontWeight: 600, fontSize: '0.72rem', '& .MuiChip-icon': { color: 'primary.light', fontSize: 16 } }} />
                  <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5 }}>{s.text}</Typography>
                </Paper>
              ))}
            </Box>
          </Box>
        ) : (
          <>
            {messages.map((m, i) => <MessageBubble key={i} msg={m} userInitials={userInitials} />)}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </>
        )}
      </Box>

      <Box sx={{ px: 2, pb: 2, pt: 1, flexShrink: 0 }}>
        <Box sx={{ maxWidth: 800, mx: 'auto' }}>
          <Paper variant="outlined" sx={{
            display: 'flex', alignItems: 'flex-end', gap: 0.5, borderRadius: 3, p: '6px 6px 6px 16px', borderColor: 'divider',
            '&:focus-within': { borderColor: 'primary.main', boxShadow: '0 0 0 3px rgba(99,102,241,0.12)' },
          }}>
            <TextField inputRef={inputRef} multiline maxRows={5}
              placeholder="Ask about resume tailoring, interview prep, or career advice..."
              value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
              variant="standard" fullWidth InputProps={{ disableUnderline: true }}
              sx={{ '& .MuiInputBase-root': { fontSize: '0.9rem', py: 0.5 } }} />
            <IconButton onClick={() => send()} disabled={!input.trim() || loading}
              sx={{ bgcolor: input.trim() ? 'primary.main' : 'transparent', color: input.trim() ? 'white' : 'text.disabled',
                borderRadius: 2, width: 36, height: 36, '&:hover': { bgcolor: 'primary.light' }, '&.Mui-disabled': { bgcolor: 'transparent' } }}>
              {loading ? <CircularProgress size={18} color="inherit" /> : <SendIcon sx={{ fontSize: 18 }} />}
            </IconButton>
          </Paper>
          <Typography variant="caption" color="text.disabled" sx={{ display: 'block', textAlign: 'center', mt: 0.75 }}>
            Job Assistant can make mistakes. Please verify important information.
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}
