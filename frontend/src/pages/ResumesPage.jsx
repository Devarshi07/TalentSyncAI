import { useState } from 'react';
import {
  Box, Typography, Paper, Button, TextField, Chip, Divider,
  List, ListItem, ListItemIcon, ListItemText, IconButton, CircularProgress,
} from '@mui/material';
import {
  DescriptionOutlined, Download, Delete, Add, AutoAwesome,
} from '@mui/icons-material';
import { chatAPI } from '../services/api';

export default function ResumesPage() {
  const [resumes, setResumes] = useState([]);
  const [jobDesc, setJobDesc] = useState('');
  const [generating, setGenerating] = useState(false);

  const generateResume = async () => {
    if (!jobDesc.trim()) return;
    setGenerating(true);
    try {
      const { data } = await chatAPI.send(
        `Tailor my resume for this role: ${jobDesc}`,
        { job_description: jobDesc }
      );
      if (data.attachments?.length) {
        const att = data.attachments[0];
        setResumes((prev) => [{
          id: Date.now(),
          title: jobDesc.slice(0, 60) + (jobDesc.length > 60 ? '...' : ''),
          date: new Date().toLocaleDateString(),
          content: att.content,
          filename: att.filename || 'resume.tex',
        }, ...prev]);
        setJobDesc('');
      }
    } catch {
      // handled by chat
    } finally {
      setGenerating(false);
    }
  };

  const downloadResume = (resume) => {
    const blob = new Blob([resume.content], { type: 'application/x-latex' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = resume.filename; a.click();
    URL.revokeObjectURL(url);
  };

  const removeResume = (id) => {
    setResumes((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <Box sx={{ maxWidth: 860, mx: 'auto', px: 3, py: 3, height: '100%', overflowY: 'auto' }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5 }}>Resumes</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
        Generate tailored resumes for specific job descriptions using AI.
      </Typography>

      {/* Generator */}
      <Paper variant="outlined" sx={{ p: 3, borderRadius: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <AutoAwesome sx={{ color: 'primary.main', fontSize: 20 }} />
          <Typography variant="subtitle1" fontWeight={600}>Generate Tailored Resume</Typography>
        </Box>
        <TextField
          multiline minRows={3} maxRows={8}
          placeholder="Paste a job description or describe the role you're targeting...&#10;&#10;Example: Senior ML Engineer at Google — working on recommendation systems, requires 5+ years experience with TensorFlow, PyTorch..."
          value={jobDesc} onChange={(e) => setJobDesc(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained" startIcon={generating ? <CircularProgress size={16} color="inherit" /> : <AutoAwesome />}
          onClick={generateResume}
          disabled={!jobDesc.trim() || generating}
          sx={{ borderRadius: 2 }}
        >
          {generating ? 'Generating...' : 'Generate Resume'}
        </Button>
      </Paper>

      {/* Resume list */}
      {resumes.length > 0 && (
        <>
          <Typography variant="overline" fontWeight={700} color="text.secondary"
            sx={{ letterSpacing: '0.06em', mb: 1.5, display: 'block' }}
          >
            Generated Resumes ({resumes.length})
          </Typography>
          <List disablePadding>
            {resumes.map((r) => (
              <Paper
                key={r.id} variant="outlined"
                sx={{ mb: 1.5, borderRadius: 2, overflow: 'hidden' }}
              >
                <ListItem
                  secondaryAction={
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <IconButton size="small" onClick={() => downloadResume(r)}
                        sx={{ color: 'primary.main' }}>
                        <Download fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => removeResume(r.id)}
                        sx={{ color: 'text.disabled', '&:hover': { color: 'error.main' } }}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    <DescriptionOutlined sx={{ color: 'primary.main' }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={r.title}
                    secondary={r.date}
                    primaryTypographyProps={{ fontSize: '0.88rem', fontWeight: 500, noWrap: true }}
                    secondaryTypographyProps={{ fontSize: '0.75rem' }}
                  />
                </ListItem>
              </Paper>
            ))}
          </List>
        </>
      )}

      {resumes.length === 0 && (
        <Paper
          variant="outlined"
          sx={{
            p: 5, textAlign: 'center', borderRadius: 3, borderStyle: 'dashed',
          }}
        >
          <DescriptionOutlined sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            No resumes generated yet. Paste a job description above to get started.
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
