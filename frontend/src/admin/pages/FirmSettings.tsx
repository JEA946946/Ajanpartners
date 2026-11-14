import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Grid, Paper, TextField, Typography } from '@mui/material';
import { firmApi } from '../../services/api';
import { errorText } from '../api';
import { FirmSettings as Firm, useAdmin } from '../AdminContext';

/** Revisorhusets oplysninger og branding (logo og farve i begge UI'er). */
const FirmSettings: React.FC = () => {
  const { firm, isPartner, setFirm } = useAdmin();
  const [form, setForm] = useState<Firm | null>(firm);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => { setForm(firm); }, [firm]);
  if (!form) return null;

  const set = (k: keyof Firm) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });
  const onLogo = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 300_000) { setMsg({ ok: false, text: 'Logoet må højst fylde 300 kB.' }); return; }
    const reader = new FileReader();
    reader.onload = () => setForm({ ...form, logo: String(reader.result) });
    reader.readAsDataURL(file);
  };
  const save = async () => {
    try {
      const r = await firmApi.put('/settings', form);
      setFirm(r.data.data.firm);
      setMsg({ ok: true, text: 'Gemt' });
    } catch (e) { setMsg({ ok: false, text: errorText(e) }); }
  };

  return (
    <Box sx={{ maxWidth: 720 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Revisorhuset</Typography>
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={8}><TextField fullWidth size="small" label="Navn" value={form.name} onChange={set('name')} disabled={!isPartner} /></Grid>
          <Grid item xs={12} sm={4}><TextField fullWidth size="small" label="CVR" value={form.cvr} onChange={set('cvr')} disabled={!isPartner} /></Grid>
          <Grid item xs={12} sm={6}><TextField fullWidth size="small" label="E-mail" value={form.email} onChange={set('email')} disabled={!isPartner} /></Grid>
          <Grid item xs={12} sm={6}><TextField fullWidth size="small" label="Telefon" value={form.phone} onChange={set('phone')} disabled={!isPartner} /></Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth size="small" type="color" label="Primær farve" value={form.primary_color} onChange={set('primary_color')} disabled={!isPartner} />
          </Grid>
          <Grid item xs={12} sm={8} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {form.logo && <Box component="img" src={form.logo} alt="" sx={{ height: 40, maxWidth: 160, objectFit: 'contain' }} />}
            {isPartner && (
              <>
                <Button variant="outlined" component="label">Vælg logo<input hidden type="file" accept="image/*" onChange={onLogo} /></Button>
                {form.logo && <Button onClick={() => setForm({ ...form, logo: '' })}>Fjern</Button>}
              </>
            )}
          </Grid>
        </Grid>
        {msg && <Alert severity={msg.ok ? 'success' : 'error'} sx={{ mt: 2 }}>{msg.text}</Alert>}
        {isPartner ? (
          <Box sx={{ mt: 2, textAlign: 'right' }}><Button variant="contained" onClick={save}>Gem</Button></Box>
        ) : <Alert severity="info" sx={{ mt: 2 }}>Kun partnere kan ændre firmaoplysningerne.</Alert>}
      </Paper>
    </Box>
  );
};

export default FirmSettings;
