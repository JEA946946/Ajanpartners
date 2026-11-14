import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Alert, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../hooks/useAuth';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [code, setCode] = useState('');
  const { login, verifyMfa, loading } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!username || !password) {
      setError(t('login.required'));
      return;
    }
    try {
      if (mfaToken) {
        if (await verifyMfa(mfaToken, code)) navigate('/');
        return;
      }
      const result = await login(username, password);
      if (result === true) {
        navigate('/');
      } else if (result && typeof result === 'object') {
        setMfaToken(result.mfaToken);
      } else {
        setError('Login mislykkedes – kontakt Ajan Partners');
      }
    } catch (err: any) {
      const msg = err?.response?.data?.message || err?.message || 'Ukendt fejl';
      if (mfaToken && err?.response?.status === 401 && /udløbet/.test(msg)) {
        setMfaToken('');
        setCode('');
      }
      setError(msg);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', bgcolor: '#f5f5f5' }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h5" align="center" sx={{ mb: 3, fontWeight: 600, color: 'primary.main' }}>
          {t('login.title')}
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <form onSubmit={handleSubmit}>
          {mfaToken ? (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Indtast koden fra din godkendelsesapp – eller en af dine gendannelseskoder.
              </Typography>
              <TextField
                fullWidth label="Kode" value={code} autoFocus size="small" sx={{ mb: 3 }}
                inputProps={{ inputMode: 'numeric', autoComplete: 'one-time-code' }}
                onChange={(e) => setCode(e.target.value)}
              />
            </>
          ) : (<>
          <TextField
            fullWidth label={t('login.username')} value={username}
            onChange={(e) => setUsername(e.target.value)}
            sx={{ mb: 2 }} size="small" autoFocus
          />
          <TextField
            fullWidth label={t('login.password')} type="password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            sx={{ mb: 3 }} size="small"
          />
          </>)}
          <Button
            fullWidth type="submit" variant="contained"
            disabled={loading}
          >
            {loading ? t('login.signingIn') : t('login.signIn')}
          </Button>
        </form>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
          Ajan Partners – gratis bogføring til vores kunder
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
