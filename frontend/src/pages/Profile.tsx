import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Container, Stack, TextField, Typography,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useClient } from '../hooks/useClient';

/** Min profil: skift adgangskode og to-faktor-login. */
const Profile: React.FC = () => {
  const { user } = useAuth();
  const { mfa, refresh, firmStaff, current } = useClient();
  const navigate = useNavigate();
  const location = useLocation();
  // To-faktor er obligatorisk for revisorhuset: indtil den er slået til, sender alle sider tilbage hertil.
  const locked = mfa.required && !mfa.enabled;
  const fallback = current ? '/dashboard' : firmStaff ? '/admin' : '/select-client';
  // Tilbage til den side, man kom fra – eller en fast side, hvis profilen blev åbnet direkte.
  const goBack = () => (location.key !== 'default' ? navigate(-1) : navigate(fallback));
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [pw, setPw] = useState({ current_password: '', new_password: '', repeat: '' });
  const [setup, setSetup] = useState<{ secret: string; qr: string } | null>(null);
  const [code, setCode] = useState('');
  const [recovery, setRecovery] = useState<string[]>([]);
  const [left, setLeft] = useState<number | null>(null);
  const [disable, setDisable] = useState({ password: '', code: '' });

  useEffect(() => {
    api.get('/me/mfa').then((r) => setLeft(r.data.data.recovery_codes_left)).catch(() => undefined);
  }, [mfa.enabled]);

  const fail = (e: any) => setMsg({ type: 'error', text: e.response?.data?.message || 'Noget gik galt' });

  const changePassword = async () => {
    if (pw.new_password !== pw.repeat) { setMsg({ type: 'error', text: 'De to nye adgangskoder er ikke ens' }); return; }
    try {
      await api.post('/me/password', { current_password: pw.current_password, new_password: pw.new_password });
      setPw({ current_password: '', new_password: '', repeat: '' });
      setMsg({ type: 'success', text: 'Adgangskoden er skiftet' });
    } catch (e) { fail(e); }
  };

  const startSetup = async () => {
    try { setSetup((await api.post('/me/mfa/setup')).data.data); setMsg(null); } catch (e) { fail(e); }
  };

  const confirm = async () => {
    try {
      const r = await api.post('/me/mfa/confirm', { code });
      setRecovery(r.data.data.recovery_codes);
      setSetup(null);
      setCode('');
      await refresh();
      setMsg({ type: 'success', text: 'To-faktor-login er slået til' });
    } catch (e) { fail(e); }
  };

  const turnOff = async () => {
    try {
      await api.post('/me/mfa/disable', disable);
      setDisable({ password: '', code: '' });
      await refresh();
      setMsg({ type: 'success', text: 'To-faktor-login er slået fra' });
    } catch (e) { fail(e); }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      {!locked && (
        <Button startIcon={<ArrowBack />} onClick={goBack} sx={{ mb: 1, ml: -1 }}>Tilbage</Button>
      )}
      <Typography variant="h5" gutterBottom>Min profil</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {user?.first_name} {user?.last_name} · {user?.email || user?.username}
      </Typography>
      {mfa.required && !mfa.enabled && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Som medarbejder i revisorhuset skal du slå to-faktor-login til, før du kan komme videre i systemet.
          Indtil da sendes du tilbage til denne side.
        </Alert>
      )}
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>To-faktor-login</Typography>
          {mfa.enabled && !recovery.length && (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Slået til. Du har {left ?? '–'} ubrugte gendannelseskoder.
              </Typography>
              {!mfa.required && (
                <Stack direction="row" spacing={1}>
                  <TextField size="small" type="password" label="Adgangskode" value={disable.password}
                    onChange={(e) => setDisable({ ...disable, password: e.target.value })} />
                  <TextField size="small" label="Kode" value={disable.code}
                    onChange={(e) => setDisable({ ...disable, code: e.target.value })} />
                  <Button color="error" onClick={turnOff}>Slå fra</Button>
                </Stack>
              )}
            </>
          )}
          {!mfa.enabled && !setup && (
            <>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Brug en godkendelsesapp (fx Microsoft Authenticator eller Google Authenticator), så der kræves
                en kode fra din telefon, når du logger ind.
              </Typography>
              <Button variant="contained" onClick={startSetup}>Slå to-faktor til</Button>
            </>
          )}
          {setup && (
            <Box>
              <Typography variant="body2">1. Scan QR-koden med appen (eller indtast nøglen manuelt).</Typography>
              <Box component="img" src={setup.qr} alt="QR-kode" sx={{ width: 180, height: 180, my: 1 }} />
              <Typography variant="caption" sx={{ display: 'block', fontFamily: 'monospace', mb: 2 }}>
                {setup.secret}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>2. Indtast koden, appen viser.</Typography>
              <Stack direction="row" spacing={1}>
                <TextField size="small" label="Kode" value={code} inputProps={{ inputMode: 'numeric' }}
                  onChange={(e) => setCode(e.target.value)} />
                <Button variant="contained" onClick={confirm}>Bekræft</Button>
              </Stack>
            </Box>
          )}
          {recovery.length > 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Gem disse gendannelseskoder et sikkert sted. De vises kun nu, og hver kan bruges én gang,
                hvis du mister telefonen.
              </Typography>
              <Box sx={{ fontFamily: 'monospace', mt: 1, columns: 2 }}>
                {recovery.map((c) => <div key={c}>{c}</div>)}
              </Box>
              <Button size="small" sx={{ mt: 1 }} onClick={() => setRecovery([])}>Jeg har gemt dem</Button>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Skift adgangskode</Typography>
          <Stack spacing={1.5}>
            <TextField size="small" type="password" label="Nuværende adgangskode" value={pw.current_password}
              onChange={(e) => setPw({ ...pw, current_password: e.target.value })} />
            <TextField size="small" type="password" label="Ny adgangskode (mindst 10 tegn)" value={pw.new_password}
              onChange={(e) => setPw({ ...pw, new_password: e.target.value })} />
            <TextField size="small" type="password" label="Gentag ny adgangskode" value={pw.repeat}
              onChange={(e) => setPw({ ...pw, repeat: e.target.value })} />
            <Box><Button variant="outlined" onClick={changePassword}>Skift adgangskode</Button></Box>
          </Stack>
        </CardContent>
      </Card>

      {!locked && <Button sx={{ mt: 3 }} startIcon={<ArrowBack />} onClick={goBack}>Tilbage</Button>}
    </Container>
  );
};

export default Profile;
