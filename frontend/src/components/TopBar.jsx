import { useState } from 'react';
import {
  AppBar, Toolbar, Typography, IconButton, Avatar, Menu, MenuItem,
  ListItemIcon, ListItemText, Divider, Box, useMediaQuery, useTheme,
} from '@mui/material';
import {
  PersonOutline, SettingsOutlined, Logout, Menu as MenuIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { SIDEBAR_WIDTH } from './Sidebar';

export default function TopBar({ title, onNavigate, onMobileMenuToggle }) {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const initials = (user?.username || '?')[0].toUpperCase();

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        width: isMobile ? '100%' : `calc(100% - ${SIDEBAR_WIDTH}px)`,
        ml: isMobile ? 0 : `${SIDEBAR_WIDTH}px`,
        bgcolor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ minHeight: '52px !important', px: 2.5 }}>
        {/* Hamburger on mobile */}
        {isMobile && (
          <IconButton edge="start" onClick={onMobileMenuToggle} sx={{ mr: 1, color: 'text.primary' }}>
            <MenuIcon />
          </IconButton>
        )}

        <Typography variant="subtitle2" color="text.secondary" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>

        <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small">
          <Avatar
            sx={{
              width: 32, height: 32, bgcolor: 'primary.main',
              fontSize: '0.85rem', fontWeight: 600,
            }}
          >
            {initials}
          </Avatar>
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          slotProps={{
            paper: {
              sx: {
                width: 220, mt: 1, bgcolor: 'background.paper',
                border: '1px solid', borderColor: 'divider', borderRadius: 2,
              },
            },
          }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" fontWeight={600}>{user?.username}</Typography>
            <Typography variant="caption" color="text.disabled">{user?.email}</Typography>
          </Box>
          <Divider sx={{ my: 0.5 }} />
          <MenuItem onClick={() => { setAnchorEl(null); onNavigate('profile'); }}>
            <ListItemIcon><PersonOutline fontSize="small" /></ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: '0.87rem' }}>Profile</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => { setAnchorEl(null); onNavigate('settings'); }}>
            <ListItemIcon><SettingsOutlined fontSize="small" /></ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: '0.87rem' }}>Settings</ListItemText>
          </MenuItem>
          <Divider sx={{ my: 0.5 }} />
          <MenuItem onClick={() => { setAnchorEl(null); logout(); }} sx={{ color: 'error.main' }}>
            <ListItemIcon><Logout fontSize="small" sx={{ color: 'error.main' }} /></ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: '0.87rem' }}>Log out</ListItemText>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
