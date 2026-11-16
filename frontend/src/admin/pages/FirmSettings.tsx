import React, { useEffect, useState } from 'react';
import {
  Alert, Box, Button, CircularProgress, Divider, Grid, Paper, TextField, Typography,
} from '@mui/material';
import { Search } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { errorText } from '../api';
import { FirmSettings as Firm, useAdmin } from '../AdminContext';

/** Revisorhusets stamdata (bruges i skabeloner, mails og brevhoveder) og branding (logo og farve). */
const FirmSettings: React.FC = () => {
  const { firm, isPartner, setFirm } = useAdmin();
  const [form, setForm] = useState<Firm | null>(firm);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [looking, setLooking] = useState(false);

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
  const lookup = async () => {
    const cvr = (form.cvr || '').replace(/\D/g, '');
    if (cvr.length !== 8) { setMsg({ ok: false, text: 'CVR-nummeret skal være 8 cifre.' }); return; }
    setLooking(true);
    setMsg(null);
    try {
      const r = await firmApi.get(`/cvr/${cvr}`);
      const d = r.data?.data ?? r.data;
      setForm((f) => f && ({
        ...f, cvr, name: d.name || f.name, address: d.address || f.address, zip_code: d.zip_code || f.zip_code,
        city: d.city || f.city, email: d.email || f.email, phone: d.phone || f.phone,
      }));
      setMsg({
        ok: d.source !== 'mock',
        text: d.source === 'mock'
          ? 'CVR-opslaget kører med testdata – tjek oplysningerne selv.'
          : 'Oplysningerne er hentet fra CVR-registret. Tjek dem, og tryk Gem.',
      });
    } catch (e) {
      setMsg({ ok: false, text: errorText(e, 'CVR-opslaget mislykkedes') });
    } finally { setLooking(false); }
  };
  const save = async () => {
    try {
      const r = await firmApi.put('/settings', form);
      setFirm(r.data.data.firm);
      setMsg({ ok: true, text: 'Gemt' });
    } catch (e) { setMsg({ ok: false, text: errorText(e) }); }
  };

  const tf = (k: keyof Firm, label: string, sm: number, props: any = {}) => (
    <Grid item xs={12} sm={sm}>
      <TextField fullWidth size="small" label={label} value={form[k] ?? ''} onChange={set(k)} disabled={!isPartner} {...props} />
    </Grid>
  );

  return (
    <Box sx={{ maxWidth: 760 }}>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Revisorhuset</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Oplysningerne bruges i skabeloner (brevhoved, opdragsbreve, erklæringer og underskrift) og over for kunderne.
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Virksomhed</Typography>
        <Grid container spacing={2}>
          {tf('name', 'Navn', 8)}
          <Grid item xs={12} sm={4} sx={{ display: 'flex', gap: 1 }}>
            <TextField fullWidth size="small" label="CVR" value={form.cvr ?? ''} onChange={set('cvr')} disabled={!isPartner}
              inputProps={{ inputMode: 'numeric' }} />
            {isPartner && (
              <Button variant="outlined" onClick={lookup} disabled={looking} sx={{ minWidth: 0, px: 1.2 }} title="Hent fra CVR">
                {looking ? <CircularProgress size={18} /> : <Search fontSize="small" />}
              </Button>
            )}
          </Grid>
          {tf('address', 'Adresse (vej og nr.)', 12)}
          {tf('zip_code', 'Postnr.', 3)}
          {tf('city', 'By', 9)}
        </Grid>
        <Divider sx={{ my: 2.5 }} />
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Kontakt</Typography>
        <Grid container spacing={2}>
          {tf('email', 'E-mail', 6, { type: 'email' })}
          {tf('phone', 'Telefon', 6)}
          {tf('website', 'Hjemmeside', 12, { placeholder: 'www.ajanpartners.dk' })}
        </Grid>
        <Divider sx={{ my: 2.5 }} />
        <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Udseende</Typography>
        <Grid container spacing={2}>
          {tf('primary_color', 'Primær farve', 4, { type: 'color' })}
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
