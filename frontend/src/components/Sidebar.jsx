import { useState } from 'react';
import {
  Box, Drawer, Typography, List, ListItemButton, ListItemIcon,
  ListItemText, Button, Divider, IconButton, TextField, ClickAwayListener,
  useMediaQuery, useTheme,
} from '@mui/material';
import {
  Add as AddIcon, ChatBubbleOutline, PersonOutline,
  DescriptionOutlined, WorkOutline, DeleteOutline, EditOutlined, Check,
  Menu as MenuIcon,
} from '@mui/icons-material';

const SIDEBAR_WIDTH = 260;

export default function Sidebar({ activePage, onNavigate, chatHistory, onNewChat, onSelectChat, onDeleteChat, onRenameChat, activeChatId, mobileOpen, onMobileToggle }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [hoveredId, setHoveredId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const startRename = (e, chat) => {
    e.stopPropagation();
    setEditingId(chat.id);
    setEditTitle(chat.title);
  };

  const confirmRename = () => {
    if (editingId && editTitle.trim() && onRenameChat) {
      onRenameChat(editingId, editTitle.trim());
    }
    setEditingId(null);
  };

  const cancelRename = () => setEditingId(null);

  const handleNav = (page) => {
    onNavigate(page);
    if (isMobile && onMobileToggle) onMobileToggle();
  };

  const handleSelectChat = (id) => {
    onSelectChat(id);
    if (isMobile && onMobileToggle) onMobileToggle();
  };

  const handleNewChat = () => {
    onNewChat();
    if (isMobile && onMobileToggle) onMobileToggle();
  };

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Logo */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 2 }}>
        <Box sx={{ width: 32, height: 32, borderRadius: 1.5, bgcolor: 'primary.main', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <WorkOutline sx={{ color: 'white', fontSize: 18 }} />
        </Box>
        <Typography variant="subtitle1" fontWeight={700}>Job Assistant</Typography>
      </Box>

      {/* New Chat */}
      <Box sx={{ px: 1.5, mb: 1 }}>
        <Button fullWidth variant="outlined" startIcon={<AddIcon />} onClick={handleNewChat}
          sx={{ justifyContent: 'flex-start', borderColor: 'divider', color: 'text.primary', borderRadius: 2, py: 1,
            '&:hover': { borderColor: 'primary.main', bgcolor: 'rgba(99,102,241,0.06)' } }}>
          New Chat
        </Button>
      </Box>

      {/* Chat History */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: 0.75 }}>
        {chatHistory.length > 0 && (
          <>
            <Typography variant="caption" sx={{ px: 1.5, py: 0.75, display: 'block', color: 'text.disabled', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Recent
            </Typography>
            <List dense disablePadding>
              {chatHistory.map((chat) => (
                editingId === chat.id ? (
                  <ClickAwayListener key={chat.id} onClickAway={cancelRename}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mx: 0.5, mb: 0.3, gap: 0.5 }}>
                      <TextField
                        size="small" autoFocus fullWidth
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') confirmRename(); if (e.key === 'Escape') cancelRename(); }}
                        sx={{ '& .MuiOutlinedInput-root': { borderRadius: 1.5, fontSize: '0.82rem', py: 0 }, '& input': { py: '6px' } }}
                      />
                      <IconButton size="small" onClick={confirmRename} sx={{ color: 'primary.main', p: 0.3 }}>
                        <Check sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Box>
                  </ClickAwayListener>
                ) : (
                  <ListItemButton
                    key={chat.id}
                    selected={chat.id === activeChatId}
                    onClick={() => handleSelectChat(chat.id)}
                    onMouseEnter={() => setHoveredId(chat.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    sx={{ borderRadius: 2, mx: 0.5, mb: 0.3, pr: 1, '&.Mui-selected': { bgcolor: 'rgba(99,102,241,0.1)' } }}
                  >
                    <ListItemIcon sx={{ minWidth: 28 }}>
                      <ChatBubbleOutline sx={{ fontSize: 15, color: 'text.disabled' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={chat.title}
                      primaryTypographyProps={{ noWrap: true, fontSize: '0.82rem', color: 'text.secondary' }}
                    />
                    {(hoveredId === chat.id || chat.id === activeChatId) && (
                      <Box sx={{ display: 'flex', gap: 0 }}>
                        {onRenameChat && (
                          <IconButton size="small" onClick={(e) => startRename(e, chat)}
                            sx={{ p: 0.3, color: 'text.disabled', '&:hover': { color: 'primary.main' } }}>
                            <EditOutlined sx={{ fontSize: 14 }} />
                          </IconButton>
                        )}
                        {onDeleteChat && (
                          <IconButton size="small" onClick={(e) => { e.stopPropagation(); onDeleteChat(chat.id); }}
                            sx={{ p: 0.3, color: 'text.disabled', '&:hover': { color: 'error.main' } }}>
                            <DeleteOutline sx={{ fontSize: 14 }} />
                          </IconButton>
                        )}
                      </Box>
                    )}
                  </ListItemButton>
                )
              ))}
            </List>
          </>
        )}
      </Box>

      {/* Bottom Nav */}
      <Divider />
      <List dense sx={{ px: 0.75, py: 0.5 }}>
        <ListItemButton selected={activePage === 'chat'} onClick={() => handleNav('chat')} sx={{ borderRadius: 2, mx: 0.5, mb: 0.3 }}>
          <ListItemIcon sx={{ minWidth: 34 }}><ChatBubbleOutline sx={{ fontSize: 20 }} /></ListItemIcon>
          <ListItemText primary="Chat" primaryTypographyProps={{ fontSize: '0.87rem', fontWeight: 500 }} />
        </ListItemButton>
        <ListItemButton selected={activePage === 'profile'} onClick={() => handleNav('profile')} sx={{ borderRadius: 2, mx: 0.5, mb: 0.3 }}>
          <ListItemIcon sx={{ minWidth: 34 }}><PersonOutline sx={{ fontSize: 20 }} /></ListItemIcon>
          <ListItemText primary="Profile" primaryTypographyProps={{ fontSize: '0.87rem', fontWeight: 500 }} />
        </ListItemButton>
        <ListItemButton selected={activePage === 'resume'} onClick={() => handleNav('resume')} sx={{ borderRadius: 2, mx: 0.5 }}>
          <ListItemIcon sx={{ minWidth: 34 }}><DescriptionOutlined sx={{ fontSize: 20 }} /></ListItemIcon>
          <ListItemText primary="Resumes" primaryTypographyProps={{ fontSize: '0.87rem', fontWeight: 500 }} />
        </ListItemButton>
      </List>
    </Box>
  );

  // Mobile: temporary drawer (overlay)
  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileToggle}
        ModalProps={{ keepMounted: true }} // better mobile perf
        sx={{
          '& .MuiDrawer-paper': { width: SIDEBAR_WIDTH, boxSizing: 'border-box' },
        }}
      >
        {drawerContent}
      </Drawer>
    );
  }

  // Desktop: permanent drawer
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: SIDEBAR_WIDTH, flexShrink: 0,
        '& .MuiDrawer-paper': { width: SIDEBAR_WIDTH, boxSizing: 'border-box' },
      }}
    >
      {drawerContent}
    </Drawer>
  );
}

export { SIDEBAR_WIDTH };
