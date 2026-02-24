import { useState, useEffect } from 'react';
import {
  Box, Typography, TextField, Button, Paper, Grid, Snackbar, Alert,
  IconButton, CircularProgress, Accordion, AccordionSummary,
  AccordionDetails, Chip, Checkbox, FormControlLabel,
} from '@mui/material';
import {
  Save, ExpandMore, Add, Delete, PersonOutline, SchoolOutlined,
  WorkOutline, CodeOutlined, EmojiEventsOutlined, TuneOutlined,
  UploadFile as UploadFileIcon,
} from '@mui/icons-material';
import { profileAPI } from '../services/api';

// ---- Factories ----
const emptyExperience = () => ({ role: '', company: '', location: '', start_date: '', end_date: '', is_current: false, description: '' });
const emptyProject = () => ({ name: '', tech_stack: [], url: '', description: '' });
const emptyEducation = () => ({ institution: '', location: '', degree: '', start_date: '', end_date: '', is_current: false, details: '' });
const emptyLeadership = () => ({ description: '' });

// ---- Date input row with "Current" checkbox ----
function DateFields({ item, onChange, currentLabel = "Current" }) {
  return (
    <>
      <Grid item xs={12} sm={4}>
        <TextField label="Start Date" size="small" value={item.start_date || ''}
          onChange={e => onChange({ ...item, start_date: e.target.value })}
          placeholder="Sep 2024" />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField label="End Date" size="small" value={item.end_date || ''}
          onChange={e => onChange({ ...item, end_date: e.target.value })}
          placeholder="Dec 2026"
          disabled={item.is_current} 
          sx={{ '& .Mui-disabled': { WebkitTextFillColor: 'rgba(255,255,255,0.3)' } }} />
      </Grid>
      <Grid item xs={12} sm={4} sx={{ display: 'flex', alignItems: 'center' }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={item.is_current || false}
              onChange={e => onChange({ ...item, is_current: e.target.checked, end_date: e.target.checked ? '' : item.end_date })}
              size="small"
              sx={{ color: 'text.disabled', '&.Mui-checked': { color: 'primary.main' } }}
            />
          }
          label={<Typography variant="body2" color="text.secondary">{currentLabel}</Typography>}
        />
      </Grid>
    </>
  );
}

// ---- Section accordion wrapper ----
function SectionAccordion({ icon, title, count, defaultExpanded, children }) {
  return (
    <Accordion
      defaultExpanded={defaultExpanded}
      sx={{
        bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider',
        borderRadius: '12px !important', mb: 2, '&::before': { display: 'none' },
        '&.Mui-expanded': { mb: 2 },
      }}
    >
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {icon}
          <Typography fontWeight={600} fontSize="0.95rem">{title}</Typography>
          {count > 0 && (
            <Chip label={count} size="small" sx={{ height: 20, fontSize: '0.7rem', bgcolor: 'rgba(99,102,241,0.1)', color: 'primary.light' }} />
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>{children}</AccordionDetails>
    </Accordion>
  );
}

// ---- Main ----
export default function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [toast, setToast] = useState({ open: false, msg: '', severity: 'success' });

  useEffect(() => {
    profileAPI.get()
      .then(({ data }) => setProfile(data))
      .catch(() => setProfile({
        personal: {}, education: [], experience: [], projects: [],
        skills: { technical: [], soft: [] }, skills_categories: [],
        leadership: [], preferences: { target_roles: [], industries: [] },
      }))
      .finally(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await profileAPI.update(profile);
      setToast({ open: true, msg: 'Profile saved!', severity: 'success' });
    } catch {
      setToast({ open: true, msg: 'Failed to save', severity: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleImportResume = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ''; // reset input
    setImporting(true);
    try {
      const { data } = await profileAPI.importResume(file);
      if (data.profile) {
        setProfile(data.profile);
        setToast({ open: true, msg: 'Resume imported! Review your profile below.', severity: 'success' });
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to import resume';
      setToast({ open: true, msg, severity: 'error' });
    } finally {
      setImporting(false);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', pt: 10 }}><CircularProgress /></Box>;

  const p = profile?.personal || {};
  const pr = profile?.preferences || {};

  const updatePersonal = (f, v) => setProfile(prev => ({ ...prev, personal: { ...prev.personal, [f]: v } }));
  const addItem = (key, factory) => setProfile(prev => ({ ...prev, [key]: [...(prev[key] || []), factory()] }));
  const removeItem = (key, i) => setProfile(prev => ({ ...prev, [key]: prev[key].filter((_, j) => j !== i) }));
  const updateItem = (key, i, updated) => setProfile(prev => {
    const arr = [...prev[key]]; arr[i] = { ...arr[i], ...updated }; return { ...prev, [key]: arr };
  });
  const updateItemField = (key, i, field, val) => updateItem(key, i, { [field]: val });

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', px: 3, py: 3, height: '100%', overflowY: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Your Profile</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.3 }}>
            Fill in your details or import from a PDF resume. The AI will tailor bullet points from your descriptions.
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexShrink: 0 }}>
          <Button
            variant="outlined" component="label" disabled={importing}
            startIcon={importing ? <CircularProgress size={16} color="inherit" /> : <UploadFileIcon />}
            sx={{ borderColor: 'divider', color: 'text.primary', '&:hover': { borderColor: 'primary.main' } }}
          >
            {importing ? 'Importing...' : 'Import PDF'}
            <input type="file" hidden accept=".pdf" onChange={handleImportResume} />
          </Button>
          <Button variant="contained" startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <Save />} onClick={save} disabled={saving}>
            Save
          </Button>
        </Box>
      </Box>

      {/* ===== Personal ===== */}
      <SectionAccordion icon={<PersonOutline sx={{ color: 'primary.main' }} />} title="Personal Information" count={0} defaultExpanded>
        <Grid container spacing={2}>
          {[['Full Name', 'name'], ['Email', 'email'], ['Phone', 'phone'], ['Location', 'location'], ['LinkedIn', 'linkedin'], ['GitHub', 'github']].map(([label, field]) => (
            <Grid item xs={12} sm={6} key={field}>
              <TextField label={label} value={p[field] || ''} onChange={e => updatePersonal(field, e.target.value)} />
            </Grid>
          ))}
        </Grid>
      </SectionAccordion>

      {/* ===== Education ===== */}
      <SectionAccordion icon={<SchoolOutlined sx={{ color: 'primary.main' }} />} title="Education" count={profile.education?.length || 0}>
        {(profile.education || []).map((edu, i) => (
          <Paper key={i} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
              <Typography variant="subtitle2" color="text.secondary">{edu.institution || `Education #${i + 1}`}</Typography>
              <IconButton size="small" onClick={() => removeItem('education', i)} sx={{ color: 'error.main' }}><Delete fontSize="small" /></IconButton>
            </Box>
            <Grid container spacing={1.5}>
              <Grid item xs={12} sm={6}>
                <TextField label="Institution" size="small" value={edu.institution || ''} onChange={e => updateItemField('education', i, 'institution', e.target.value)} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Location" size="small" value={edu.location || ''} onChange={e => updateItemField('education', i, 'location', e.target.value)} />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Degree" size="small" value={edu.degree || ''} onChange={e => updateItemField('education', i, 'degree', e.target.value)} placeholder="Master of Science in Data Analytics Engineering" />
              </Grid>
              <DateFields item={edu} onChange={updated => updateItem('education', i, updated)} currentLabel="Currently studying" />
              <Grid item xs={12}>
                <TextField label="Details (coursework, GPA, honors)" size="small" multiline value={edu.details || ''} onChange={e => updateItemField('education', i, 'details', e.target.value)} />
              </Grid>
            </Grid>
          </Paper>
        ))}
        <Button startIcon={<Add />} onClick={() => addItem('education', emptyEducation)} size="small">Add Education</Button>
      </SectionAccordion>

      {/* ===== Experience ===== */}
      <SectionAccordion icon={<WorkOutline sx={{ color: 'primary.main' }} />} title="Experience" count={profile.experience?.length || 0}>
        {(profile.experience || []).map((exp, i) => (
          <Paper key={i} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
              <Typography variant="subtitle2" color="text.secondary">{exp.role ? `${exp.role} @ ${exp.company}` : `Experience #${i + 1}`}</Typography>
              <IconButton size="small" onClick={() => removeItem('experience', i)} sx={{ color: 'error.main' }}><Delete fontSize="small" /></IconButton>
            </Box>
            <Grid container spacing={1.5}>
              <Grid item xs={12} sm={6}>
                <TextField label="Role / Title" size="small" value={exp.role || ''} onChange={e => updateItemField('experience', i, 'role', e.target.value)} placeholder="Software Engineer Intern" />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="Company" size="small" value={exp.company || ''} onChange={e => updateItemField('experience', i, 'company', e.target.value)} />
              </Grid>
              <Grid item xs={12} sm={12}>
                <TextField label="Location" size="small" value={exp.location || ''} onChange={e => updateItemField('experience', i, 'location', e.target.value)} placeholder="Boston, MA" />
              </Grid>
              <DateFields item={exp} onChange={updated => updateItem('experience', i, updated)} currentLabel="Currently working here" />
              <Grid item xs={12}>
                <TextField
                  label="Description" size="small" multiline minRows={3}
                  value={exp.description || ''}
                  onChange={e => updateItemField('experience', i, 'description', e.target.value)}
                  placeholder="Describe what you did in this role. Include key accomplishments, technologies used, and impact. The AI will convert this into tailored bullet points when generating your resume."
                  helperText="Write freely — the AI will create tailored bullet points from this when you generate a resume."
                />
              </Grid>
            </Grid>
          </Paper>
        ))}
        <Button startIcon={<Add />} onClick={() => addItem('experience', emptyExperience)} size="small">Add Experience</Button>
      </SectionAccordion>

      {/* ===== Projects ===== */}
      <SectionAccordion icon={<CodeOutlined sx={{ color: 'primary.main' }} />} title="Projects" count={profile.projects?.length || 0}>
        {(profile.projects || []).map((proj, i) => (
          <Paper key={i} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
              <Typography variant="subtitle2" color="text.secondary">{proj.name || `Project #${i + 1}`}</Typography>
              <IconButton size="small" onClick={() => removeItem('projects', i)} sx={{ color: 'error.main' }}><Delete fontSize="small" /></IconButton>
            </Box>
            <Grid container spacing={1.5}>
              <Grid item xs={12} sm={6}>
                <TextField label="Project Name" size="small" value={proj.name || ''} onChange={e => updateItemField('projects', i, 'name', e.target.value)} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField label="URL" size="small" value={proj.url || ''} onChange={e => updateItemField('projects', i, 'url', e.target.value)} placeholder="github.com/user/repo" />
              </Grid>
              <Grid item xs={12}>
                <TextField label="Tech Stack (comma-separated)" size="small" value={(proj.tech_stack || []).join(', ')}
                  onChange={e => updateItemField('projects', i, 'tech_stack', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  placeholder="React.js, FastAPI, PostgreSQL, LangGraph..." />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Description" size="small" multiline minRows={3}
                  value={proj.description || ''}
                  onChange={e => updateItemField('projects', i, 'description', e.target.value)}
                  placeholder="Describe the project — what it does, your role, key features, and results. The AI will convert this into tailored bullet points."
                  helperText="Write freely — the AI will create tailored bullet points from this when you generate a resume."
                />
              </Grid>
            </Grid>
          </Paper>
        ))}
        <Button startIcon={<Add />} onClick={() => addItem('projects', emptyProject)} size="small">Add Project</Button>
      </SectionAccordion>

      {/* ===== Skills Categories ===== */}
      <SectionAccordion icon={<TuneOutlined sx={{ color: 'primary.main' }} />} title="Technical Skills" count={profile.skills_categories?.length || 0}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Organize skills by category (e.g. Languages/Database, Libraries/Frameworks, DevOps/Cloud)
        </Typography>
        {(profile.skills_categories || []).map((cat, i) => (
          <Paper key={i} variant="outlined" sx={{ p: 2, mb: 1.5, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
              <TextField label="Category" size="small" sx={{ width: 220, flexShrink: 0 }}
                value={cat.category || ''}
                onChange={e => {
                  const arr = [...(profile.skills_categories || [])]; arr[i] = { ...arr[i], category: e.target.value };
                  setProfile(prev => ({ ...prev, skills_categories: arr }));
                }}
                placeholder="e.g. Languages/Database" />
              <TextField label="Skills (comma-separated)" size="small" fullWidth multiline
                value={(cat.items || []).join(', ')}
                onChange={e => {
                  const arr = [...(profile.skills_categories || [])]; arr[i] = { ...arr[i], items: e.target.value.split(',').map(s => s.trim()).filter(Boolean) };
                  setProfile(prev => ({ ...prev, skills_categories: arr }));
                }}
                placeholder="Python, C++, JavaScript, MySQL..." />
              <IconButton size="small" onClick={() => {
                setProfile(prev => ({ ...prev, skills_categories: prev.skills_categories.filter((_, j) => j !== i) }));
              }} sx={{ color: 'error.main', mt: 0.5 }}><Delete fontSize="small" /></IconButton>
            </Box>
          </Paper>
        ))}
        <Button startIcon={<Add />} size="small" onClick={() => {
          setProfile(prev => ({ ...prev, skills_categories: [...(prev.skills_categories || []), { category: '', items: [] }] }));
        }}>Add Category</Button>
      </SectionAccordion>

      {/* ===== Leadership ===== */}
      <SectionAccordion icon={<EmojiEventsOutlined sx={{ color: 'primary.main' }} />} title="Leadership & Achievements" count={profile.leadership?.length || 0}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Each item becomes a bullet point on your resume. Write complete descriptions.
        </Typography>
        {(profile.leadership || []).map((lead, i) => (
          <Paper key={i} variant="outlined" sx={{ p: 2, mb: 1.5, borderRadius: 2 }}>
            <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
              <TextField
                size="small" fullWidth multiline
                value={lead.description || ''}
                onChange={e => updateItemField('leadership', i, 'description', e.target.value)}
                placeholder="e.g. Ranked top 20/1,000+ teams as Regional Semifinalist in Microsoft Imagine Cup 2023"
              />
              <IconButton size="small" onClick={() => removeItem('leadership', i)}
                sx={{ color: 'error.main', mt: 0.5 }}><Delete fontSize="small" /></IconButton>
            </Box>
          </Paper>
        ))}
        <Button startIcon={<Add />} onClick={() => addItem('leadership', emptyLeadership)} size="small">Add Achievement</Button>
      </SectionAccordion>

      {/* ===== Preferences ===== */}
      <SectionAccordion icon={<TuneOutlined sx={{ color: 'primary.main' }} />} title="Preferences" count={0}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField label="Target Roles (comma-separated)" value={(pr.target_roles || []).join(', ')}
              onChange={e => setProfile(prev => ({ ...prev, preferences: { ...prev.preferences, target_roles: e.target.value.split(',').map(s => s.trim()).filter(Boolean) } }))} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField label="Target Industries (comma-separated)" value={(pr.industries || []).join(', ')}
              onChange={e => setProfile(prev => ({ ...prev, preferences: { ...prev.preferences, industries: e.target.value.split(',').map(s => s.trim()).filter(Boolean) } }))} />
          </Grid>
        </Grid>
      </SectionAccordion>

      <Snackbar open={toast.open} autoHideDuration={3000} onClose={() => setToast(t => ({ ...t, open: false }))} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}>
        <Alert severity={toast.severity} onClose={() => setToast(t => ({ ...t, open: false }))} sx={{ borderRadius: 2 }}>{toast.msg}</Alert>
      </Snackbar>
    </Box>
  );
}
