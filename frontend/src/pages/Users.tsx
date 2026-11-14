import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, MenuItem, Chip, FormControlLabel, Switch, Alert,
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Key as KeyIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

type Role = 'admin' | 'accountant' | 'viewer';

interface User {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active?: boolean;
  role: Role;
}

const EMPTY_CREATE_FORM = {
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  role: 'viewer' as 'admin' | 'accountant' | 'viewer',
};

const Users: React.FC = () => {
  const { t } = useTranslation();

  const ROLE_CHIP_PROPS: Record<string, { color: 'error' | 'primary' | 'default'; label: string }> = {
    admin: { color: 'error', label: t('users.admin') },
    accountant: { color: 'primary', label: t('users.accountant') },
    viewer: { color: 'default', label: t('users.viewer') },
  };

  const [users, setUsers] = useState<User[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ ...EMPTY_CREATE_FORM });

  // Edit dialog: every field of the account, not only the role.
  const [editOpen, setEditOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({
    username: '', first_name: '', last_name: '', email: '', role: 'viewer' as Role, is_active: true,
  });
  const [editError, setEditError] = useState<string | null>(null);

  // Change password dialog: the admin types it twice, or lets the server
  // pick one and shows it once.
  const [pwOpen, setPwOpen] = useState(false);
  const [pwUser, setPwUser] = useState<User | null>(null);
  const [pw1, setPw1] = useState('');
  const [pw2, setPw2] = useState('');
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwResult, setPwResult] = useState<string | null>(null);

  const fetchUsers = () => {
    api.get('/users').then(res => {
      if (res.data.success) {
        setUsers(res.data.data?.users || res.data.users || []);
      }
    });
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Create user
  const handleCreateOpen = () => {
    setCreateForm({ ...EMPTY_CREATE_FORM });
    setCreateOpen(true);
  };

  const handleCreate = async () => {
    if (!createForm.username || !createForm.password) {
      alert(t('users.usernamePasswordRequired'));
      return;
    }
    try {
      await api.post('/users', createForm);
      setCreateOpen(false);
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.message || t('users.errorCreating'));
    }
  };

  // Edit
  const handleEditOpen = (user: User) => {
    setEditingUser(user);
    setEditForm({
      username: user.username, first_name: user.first_name || '', last_name: user.last_name || '',
      email: user.email || '', role: user.role, is_active: user.is_active !== false,
    });
    setEditError(null);
    setEditOpen(true);
  };

  const handleEditSave = async () => {
    if (!editingUser) return;
    if (!editForm.username.trim()) { setEditError(t('users.usernameRequired')); return; }
    try {
      await api.put(`/users/${editingUser.id}`, editForm);
      setEditOpen(false);
      setEditingUser(null);
      fetchUsers();
    } catch (err: any) {
      setEditError(err.response?.data?.message || t('users.errorUpdating'));
    }
  };

  // Change password
  const handlePwOpen = (user: User) => {
    setPwUser(user); setPw1(''); setPw2(''); setPwError(null); setPwResult(null);
    setPwOpen(true);
  };

  const handlePwSave = async (generate: boolean) => {
    if (!pwUser) return;
    if (!generate) {
      if (pw1.length < 8) { setPwError(t('users.passwordTooShort')); return; }
      if (pw1 !== pw2) { setPwError(t('users.passwordMismatch')); return; }
    }
    try {
      const res = await api.post(`/users/${pwUser.id}/reset-password`, generate ? {} : { password: pw1 });
      setPwError(null);
      if (generate) setPwResult(res.data?.data?.password || '');
      else { setPwOpen(false); setPwUser(null); }
    } catch (err: any) {
      setPwError(err.response?.data?.message || t('users.errorPassword'));
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>{t('users.title')}</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreateOpen} sx={{ bgcolor: '#2e7d32' }}>
          {t('users.addUser')}
        </Button>
      </Box>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
              <TableCell sx={{ fontWeight: 600 }}>{t('users.username')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('users.firstName')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('users.lastName')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('common.email')}</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>{t('users.role')}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map(user => {
              const roleProps = ROLE_CHIP_PROPS[user.role] || { color: 'default' as const, label: user.role };
              return (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>{user.username}</Typography>
                  </TableCell>
                  <TableCell>{user.first_name}</TableCell>
                  <TableCell>{user.last_name}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Chip
                      label={roleProps.label}
                      size="small"
                      color={roleProps.color}
                      sx={{ height: 22, fontSize: '11px' }}
                    />
                    {user.is_active === false && (
                      <Chip label={t('users.inactive')} size="small" sx={{ height: 22, fontSize: '11px', ml: 0.5 }} />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => handleEditOpen(user)} title={t('users.editUser')}>
                      <EditIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                    <IconButton size="small" onClick={() => handlePwOpen(user)} title={t('users.changePassword')}>
                      <KeyIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </TableCell>
                </TableRow>
              );
            })}
            {users.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography variant="body2" color="text.secondary">{t('users.noUsers')}</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('users.addUser')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label={t('users.username')}
              value={createForm.username}
              size="small"
              fullWidth
              required
              onChange={e => setCreateForm({ ...createForm, username: e.target.value })}
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('users.firstName')}
                value={createForm.first_name}
                size="small"
                fullWidth
                onChange={e => setCreateForm({ ...createForm, first_name: e.target.value })}
              />
              <TextField
                label={t('users.lastName')}
                value={createForm.last_name}
                size="small"
                fullWidth
                onChange={e => setCreateForm({ ...createForm, last_name: e.target.value })}
              />
            </Box>
            <TextField
              label={t('common.email')}
              value={createForm.email}
              size="small"
              fullWidth
              type="email"
              onChange={e => setCreateForm({ ...createForm, email: e.target.value })}
            />
            <TextField
              label={t('users.password')}
              value={createForm.password}
              size="small"
              fullWidth
              type="password"
              required
              onChange={e => setCreateForm({ ...createForm, password: e.target.value })}
            />
            <TextField
              label={t('users.role')}
              value={createForm.role}
              size="small"
              select
              fullWidth
              onChange={e => setCreateForm({ ...createForm, role: e.target.value as 'admin' | 'accountant' | 'viewer' })}
            >
              <MenuItem value="admin">{t('users.admin')}</MenuItem>
              <MenuItem value="accountant">{t('users.accountant')}</MenuItem>
              <MenuItem value="viewer">{t('users.viewer')}</MenuItem>
            </TextField>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleCreate} sx={{ bgcolor: '#2e7d32' }}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('users.editUser')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            {editError && <Alert severity="error">{editError}</Alert>}
            <TextField label={t('users.username')} value={editForm.username} size="small" fullWidth required
              onChange={e => setEditForm({ ...editForm, username: e.target.value })} />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label={t('users.firstName')} value={editForm.first_name} size="small" fullWidth
                onChange={e => setEditForm({ ...editForm, first_name: e.target.value })} />
              <TextField label={t('users.lastName')} value={editForm.last_name} size="small" fullWidth
                onChange={e => setEditForm({ ...editForm, last_name: e.target.value })} />
            </Box>
            <TextField label={t('common.email')} value={editForm.email} size="small" fullWidth type="email"
              onChange={e => setEditForm({ ...editForm, email: e.target.value })} />
            <TextField label={t('users.role')} value={editForm.role} size="small" select fullWidth
              onChange={e => setEditForm({ ...editForm, role: e.target.value as Role })}>
              <MenuItem value="admin">{t('users.admin')}</MenuItem>
              <MenuItem value="accountant">{t('users.accountant')}</MenuItem>
              <MenuItem value="viewer">{t('users.viewer')}</MenuItem>
            </TextField>
            <FormControlLabel
              control={<Switch checked={editForm.is_active}
                onChange={e => setEditForm({ ...editForm, is_active: e.target.checked })} />}
              label={t('users.active')} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleEditSave} sx={{ bgcolor: '#2e7d32' }}>
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={pwOpen} onClose={() => setPwOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{t('users.changePassword')}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            {pwUser && (
              <Typography variant="body2">
                {t('users.userLabel')} <strong>{pwUser.username}</strong> ({pwUser.first_name} {pwUser.last_name})
              </Typography>
            )}
            {pwError && <Alert severity="error">{pwError}</Alert>}
            {pwResult ? (
              <Alert severity="success">
                {t('users.generatedPassword')} <strong style={{ fontFamily: 'monospace', fontSize: 15 }}>{pwResult}</strong>
                <br /><Typography variant="caption">{t('users.generatedPasswordNote')}</Typography>
              </Alert>
            ) : (
              <>
                <TextField label={t('users.newPassword')} value={pw1} size="small" fullWidth type="password"
                  autoComplete="new-password" onChange={e => setPw1(e.target.value)}
                  helperText={t('users.passwordRule')} />
                <TextField label={t('users.repeatPassword')} value={pw2} size="small" fullWidth type="password"
                  autoComplete="new-password" onChange={e => setPw2(e.target.value)} />
              </>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPwOpen(false)}>{pwResult ? t('common.close') : t('common.cancel')}</Button>
          {!pwResult && (
            <>
              <Button onClick={() => handlePwSave(true)}>{t('users.generatePassword')}</Button>
              <Button variant="contained" onClick={() => handlePwSave(false)} sx={{ bgcolor: '#2e7d32' }}>
                {t('common.save')}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Users;
