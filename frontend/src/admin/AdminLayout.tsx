import React from 'react';
import {
  AppBar, Avatar, Box, Chip, Divider, Drawer, IconButton, List, ListItemButton, ListItemIcon,
  ListItemText, Toolbar, Tooltip, Typography,
} from '@mui/material';
import {
  Business as ClientsIcon, Event as DeadlineIcon, Forum as TaskIcon, Group as StaffIcon,
  Inventory2 as PackageIcon, History as AuditIcon, Settings as SettingsIcon, SwapHoriz as SwapIcon,
  Logout as LogoutIcon, PersonAdd as NewIcon,
  Gavel as TermsIcon,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { STAFF_ROLES } from './api';
import { useAdmin } from './AdminContext';

const SIDEBAR = 220;
const BAR = 52;

const ITEMS = [
  { text: 'Kunder', icon: <ClientsIcon fontSize="small" />, path: '/admin/clients' },
  { text: 'Opret kunde', icon: <NewIcon fontSize="small" />, path: '/admin/clients/new' },
  { text: 'Fristkalender', icon: <DeadlineIcon fontSize="small" />, path: '/admin/deadlines' },
  { text: 'Opgaver og forespørgsler', icon: <TaskIcon fontSize="small" />, path: '/admin/tasks' },
  { text: 'Medarbejdere', icon: <StaffIcon fontSize="small" />, path: '/admin/staff' },
  { text: 'Pakker', icon: <PackageIcon fontSize="small" />, path: '/admin/packages' },
  { text: 'Betingelser', icon: <TermsIcon fontSize="small" />, path: '/admin/terms' },
  { text: 'Audit-log', icon: <AuditIcon fontSize="small" />, path: '/admin/audit-log' },
  { text: 'Revisorhuset', icon: <SettingsIcon fontSize="small" />, path: '/admin/settings' },
];

const AdminLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { firm, role } = useAdmin();
  const color = firm?.primary_color || '#0B3D5C';

  const active = (path: string) =>
    path === '/admin/clients'
      ? location.pathname === path || (location.pathname.startsWith('/admin/clients/') && !location.pathname.endsWith('/new'))
      : location.pathname.startsWith(path);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: color }}>
        <Toolbar variant="dense" sx={{ minHeight: BAR, height: BAR }}>
          {firm?.logo && (
            <Box component="img" src={firm.logo} alt="" sx={{ height: 30, maxWidth: 140, objectFit: 'contain', mr: 1.5 }} />
          )}
          <Typography variant="h6" noWrap sx={{ fontSize: 16, fontWeight: 700 }}>
            {firm?.name || 'Ajan Partners'}
          </Typography>
          <Chip size="small" label="Admin-portal" sx={{ ml: 1.5, bgcolor: 'rgba(255,255,255,0.18)', color: '#fff' }} />
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Tooltip title="Arbejd i en kunde">
              <IconButton color="inherit" size="small" onClick={() => navigate('/admin/select-client')}>
                <SwapIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Box sx={{ textAlign: 'right' }}>
              <Typography sx={{ fontSize: 12, lineHeight: 1.2 }}>
                {user?.first_name} {user?.last_name}
              </Typography>
              <Typography sx={{ fontSize: 11, opacity: 0.8, lineHeight: 1.2 }}>{STAFF_ROLES[role] || role}</Typography>
            </Box>
            <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 28, height: 28, fontSize: 12 }}>
              {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
            </Avatar>
            <Tooltip title="Log ud">
              <IconButton color="inherit" size="small" onClick={() => { logout(); navigate('/login'); }}>
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer variant="permanent" sx={{
        width: SIDEBAR, flexShrink: 0,
        '& .MuiDrawer-paper': { width: SIDEBAR, boxSizing: 'border-box', mt: `${BAR}px`, height: `calc(100% - ${BAR}px)`, bgcolor: '#fafafa' },
      }}>
        <List dense sx={{ pt: 1 }}>
          {ITEMS.map((item) => {
            const on = active(item.path);
            return (
              <ListItemButton key={item.path} onClick={() => navigate(item.path)} sx={{
                mx: 1, borderRadius: 1, mb: 0.3,
                bgcolor: on ? color : 'transparent', color: on ? '#fff' : 'text.primary',
                '&:hover': { bgcolor: on ? color : 'action.hover' },
                '& .MuiListItemIcon-root': { color: on ? '#fff' : 'text.secondary', minWidth: 30 },
              }}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} primaryTypographyProps={{ fontSize: 12.5 }} />
              </ListItemButton>
            );
          })}
        </List>
        <Divider />
        <List dense>
          <ListItemButton onClick={() => navigate('/admin/select-client')} sx={{
            mx: 1, borderRadius: 1,
            ...(active('/admin/select-client') ? { bgcolor: color, color: '#fff', '&:hover': { bgcolor: color } } : {}),
            '& .MuiListItemIcon-root': { color: active('/admin/select-client') ? '#fff' : 'text.secondary', minWidth: 30 },
          }}>
            <ListItemIcon><SwapIcon fontSize="small" /></ListItemIcon>
            <ListItemText primary="Arbejd i en kunde" primaryTypographyProps={{ fontSize: 12.5 }} />
          </ListItemButton>
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: `${BAR}px`, bgcolor: 'background.default', minWidth: 0 }}>
        {children}
      </Box>
    </Box>
  );
};

export default AdminLayout;
