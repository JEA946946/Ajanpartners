import React, { useState } from 'react';
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, Grid, MenuItem,
  Paper, Step, StepLabel, Stepper, TextField, Typography,
} from '@mui/material';
import { ContentCopy as CopyIcon, Search as SearchIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { firmApi } from '../../services/api';
import {
  ACCOUNTING_CLASSES, CHART_TEMPLATES, errorText, label, LEGAL_FORMS, MONTHS, VAT_PERIODS,
} from '../api';
import { useAdmin } from '../AdminContext';

const STEPS = ['Virksomhed', 'Regnskab og moms', 'Pakke og ejer', 'Bekræft'];

interface Form {
  cvr: string; name: string; legal_form: string; address: string; zip_code: string; city: string;
  industry_code: string; email: string; phone: string;
  vat_period: string; fiscal_year_start_month: number; accounting_class: string; chart_template: string;
  package: string; responsible_id: number | ''; owner_email: string; owner_name: string; grant_scope: string;
}

const EMPTY: Form = {
  cvr: '', name: '', legal_form: 'aps', address: '', zip_code: '', city: '', industry_code: '', email: '', phone: '',
  vat_period: 'quarter', fiscal_year_start_month: 1, accounting_class: 'B', chart_template: 'standard',
  package: 'standard', responsible_id: '', owner_email: '', owner_name: '', grant_scope: 'bookkeeping',
};

const PERSONAL = ['enk', 'pmv', 'is'];

/** Kortlæg svaret fra CVR-opslaget (feltnavne kan variere mellem adaptere). */
const fromCvr = (raw: any): Partial<Form> => {
  const d = raw?.company || raw || {};
  const pick = (...keys: string[]) => keys.map((k) => d[k]).find((v) => v !== undefined && v !== null && v !== '');
  const out: Partial<Form> = {};
  const set = (k: keyof Form, v: any) => { if (v !== undefined) (out as any)[k] = String(v); };
  set('name', pick('name', 'navn'));
  set('address', pick('address', 'adresse'));
  set('zip_code', pick('zip_code', 'zipcode', 'postnr'));
  set('city', pick('city', 'by'));
  set('industry_code', pick('industry_code', 'industrycode', 'branchekode'));
  set('email', pick('email'));
  set('phone', pick('phone', 'telefon'));
  const lf = pick('legal_form');
  if (lf && LEGAL_FORMS.some(([k]) => k === lf)) out.legal_form = lf;
  const fy = Number(pick('fiscal_year_start_month'));
  if (fy >= 1 && fy <= 12) out.fiscal_year_start_month = fy;
  return out;
};

const CreateClient: React.FC = () => {
  const navigate = useNavigate();
  const { packages, staff } = useAdmin();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>(EMPTY);
  const [lookup, setLookup] = useState<{ loading: boolean; message: string; severity: 'info' | 'warning' | 'success' }>({
    loading: false, message: '', severity: 'info',
  });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<{ slug: string; username?: string; password?: string | null } | null>(null);

  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = k === 'fiscal_year_start_month' ? Number(e.target.value) : e.target.value;
    setForm((f) => {
      const next = { ...f, [k]: value };
      // Forslag ud fra virksomhedsformen (kan ændres bagefter).
      if (k === 'legal_form') {
        if (PERSONAL.includes(value as string)) { next.accounting_class = 'A'; next.chart_template = 'enkeltmand'; }
        else if (value === 'holding') { next.accounting_class = 'B'; next.chart_template = 'holding'; }
        else if (f.chart_template === 'enkeltmand') { next.accounting_class = 'B'; next.chart_template = 'standard'; }
      }
      return next;
    });
  };

  const doLookup = async () => {
    if (!/^\d{8}$/.test(form.cvr)) {
      setLookup({ loading: false, message: 'CVR-nummeret skal være 8 cifre.', severity: 'warning' });
      return;
    }
    setLookup({ loading: true, message: '', severity: 'info' });
    try {
      const r = await firmApi.get(`/cvr/${form.cvr}`);
      const found = fromCvr(r.data?.data ?? r.data);
      setForm((f) => ({ ...f, ...found }));
      setLookup({ loading: false, message: 'Oplysningerne er hentet fra CVR. Tjek dem, før du går videre.', severity: 'success' });
    } catch (e: any) {
      const code = e?.response?.status;
      const message = code === 404
        ? 'CVR-nummeret blev ikke fundet. Udfyld felterne manuelt.'
        : code === 501 || code === 503
          ? 'CVR-opslag er ikke sat op endnu. Udfyld felterne manuelt.'
          : `CVR-opslaget mislykkedes (${errorText(e, 'ukendt fejl')}). Udfyld felterne manuelt.`;
      setLookup({ loading: false, message, severity: 'warning' });
    }
  };

  const validStep = () => {
    if (step === 0) return form.name.trim() !== '' && (!form.cvr || /^\d{8}$/.test(form.cvr));
    if (step === 2) return !form.owner_email || /.+@.+\..+/.test(form.owner_email);
    return true;
  };

  const submit = async () => {
    setSaving(true);
    setError('');
    try {
      const body: any = { ...form, responsible_id: form.responsible_id || undefined };
      const r = await firmApi.post('/clients', body, { timeout: 120000 });
      const d = r.data.data;
      setResult({ slug: d.client.slug, username: d.owner?.username, password: d.owner?.temporary_password });
    } catch (e) {
      setError(errorText(e, 'Kunden kunne ikke oprettes'));
    } finally {
      setSaving(false);
    }
  };

  const tf = (k: keyof Form, lbl: string, props: any = {}) => (
    <TextField fullWidth size="small" label={lbl} value={form[k]} onChange={set(k)} {...props} />
  );

  return (
    <Box sx={{ maxWidth: 860 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Opret kunde</Typography>
      <Stepper activeStep={step} sx={{ mb: 3 }}>
        {STEPS.map((s) => <Step key={s}><StepLabel>{s}</StepLabel></Step>)}
      </Stepper>
      <Paper sx={{ p: 3 }}>
        {step === 0 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} sx={{ display: 'flex', gap: 1 }}>
              {tf('cvr', 'CVR-nummer', { inputProps: { maxLength: 8, inputMode: 'numeric' },
                onKeyDown: (e: React.KeyboardEvent) => { if (e.key === 'Enter') doLookup(); } })}
              <Button variant="outlined" onClick={doLookup} disabled={lookup.loading}
                startIcon={lookup.loading ? <CircularProgress size={14} /> : <SearchIcon />}>
                Slå op
              </Button>
            </Grid>
            <Grid item xs={12}>
              {lookup.message && <Alert severity={lookup.severity}>{lookup.message}</Alert>}
            </Grid>
            <Grid item xs={12} sm={8}>{tf('name', 'Navn', { required: true })}</Grid>
            <Grid item xs={12} sm={4}>
              {tf('legal_form', 'Virksomhedsform', { select: true, children: LEGAL_FORMS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12}>{tf('address', 'Adresse')}</Grid>
            <Grid item xs={4}>{tf('zip_code', 'Postnr.')}</Grid>
            <Grid item xs={8}>{tf('city', 'By')}</Grid>
            <Grid item xs={12} sm={4}>{tf('industry_code', 'Branchekode (DB07)')}</Grid>
            <Grid item xs={12} sm={4}>{tf('email', 'E-mail')}</Grid>
            <Grid item xs={12} sm={4}>{tf('phone', 'Telefon')}</Grid>
          </Grid>
        )}

        {step === 1 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              {tf('vat_period', 'Momsperiode', { select: true, children: VAT_PERIODS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={6}>
              {tf('fiscal_year_start_month', 'Regnskabsåret starter', { select: true,
                helperText: form.fiscal_year_start_month === 1 ? 'Kalenderår' : `Forskudt regnskabsår (slutter ultimo ${MONTHS[(form.fiscal_year_start_month + 10) % 12]})`,
                children: MONTHS.map((m, i) => <MenuItem key={m} value={i + 1}>1. {m}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={6}>
              {tf('accounting_class', 'Regnskabsklasse (ÅRL)', { select: true, children: ACCOUNTING_CLASSES.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={6}>
              {tf('chart_template', 'Kontoplan', { select: true, children: CHART_TEMPLATES.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>) })}
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                Momsperiode, regnskabsår og regnskabsklasse styrer fristkalenderen. Kontoplanen oprettes fra skabelonen og kan tilpasses bagefter.
              </Alert>
            </Grid>
          </Grid>
        )}

        {step === 2 && (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              {tf('package', 'Pakke', { select: true, children: packages.filter((p) => p.is_active).map((p) =>
                <MenuItem key={p.code} value={p.code}>{p.name} – {p.description}</MenuItem>) })}
            </Grid>
            <Grid item xs={12} sm={6}>
              {tf('responsible_id', 'Ansvarlig', { select: true, helperText: 'Tom = dig selv', children: [
                <MenuItem key="" value="">Mig selv</MenuItem>,
                ...staff.filter((s) => s.is_active).map((s) =>
                  <MenuItem key={s.user_id} value={s.user_id}>{`${s.first_name} ${s.last_name}`.trim() || s.username}</MenuItem>),
              ] })}
            </Grid>
            <Grid item xs={12} sm={6}>{tf('owner_email', 'Ejerens e-mail', { type: 'email', helperText: 'Ejeren får et login og skal godkende jeres adgang' })}</Grid>
            <Grid item xs={12} sm={6}>{tf('owner_name', 'Ejerens navn')}</Grid>
            <Grid item xs={12} sm={6}>
              {tf('grant_scope', 'Adgang der anmodes om', { select: true, children: [
                <MenuItem key="read" value="read">Læse</MenuItem>,
                <MenuItem key="bookkeeping" value="bookkeeping">Bogføre</MenuItem>,
                <MenuItem key="full" value="full">Fuld adgang</MenuItem>,
              ] })}
            </Grid>
            {!form.owner_email && (
              <Grid item xs={12}>
                <Alert severity="warning">Uden en ejer kan ingen godkende adgangen, så I kan ikke arbejde i bøgerne endnu.</Alert>
              </Grid>
            )}
          </Grid>
        )}

        {step === 3 && (
          <Box>
            <Typography variant="h6" gutterBottom>{form.name}</Typography>
            <Typography>CVR: {form.cvr || '—'} · {label(LEGAL_FORMS, form.legal_form)}</Typography>
            <Typography>{form.address} {form.zip_code} {form.city}</Typography>
            <Typography sx={{ mt: 1 }}>
              Moms: {label(VAT_PERIODS, form.vat_period)} · Regnskabsår fra 1. {MONTHS[form.fiscal_year_start_month - 1]} · Klasse {form.accounting_class}
            </Typography>
            <Typography>Kontoplan: {label(CHART_TEMPLATES, form.chart_template)} · Pakke: {packages.find((p) => p.code === form.package)?.name}</Typography>
            <Typography>Ejer: {form.owner_email || 'ingen'}</Typography>
            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
            {saving && <Alert severity="info" sx={{ mt: 2 }}>Opretter skema og kontoplan – det kan tage et halvt minut …</Alert>}
          </Box>
        )}

        <Box sx={{ display: 'flex', mt: 3 }}>
          <Button onClick={() => (step === 0 ? navigate('/admin/clients') : setStep(step - 1))} disabled={saving}>
            {step === 0 ? 'Annullér' : 'Tilbage'}
          </Button>
          <Box sx={{ ml: 'auto' }}>
            {step < 3 ? (
              <Button variant="contained" disabled={!validStep()} onClick={() => setStep(step + 1)}>Næste</Button>
            ) : (
              <Button variant="contained" disabled={saving} onClick={submit}
                startIcon={saving ? <CircularProgress size={14} color="inherit" /> : undefined}>
                Opret kunde
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      <Dialog open={!!result} maxWidth="sm" fullWidth>
        <DialogTitle>Kunden er oprettet</DialogTitle>
        <DialogContent>
          {result?.password ? (
            <>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Den midlertidige adgangskode vises kun denne ene gang. Giv den til kunden på en sikker måde.
              </Alert>
              <Typography>Brugernavn: <b>{result.username}</b></Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography>Adgangskode: <b style={{ fontFamily: 'monospace' }}>{result.password}</b></Typography>
                <Button size="small" startIcon={<CopyIcon />} onClick={() => navigator.clipboard?.writeText(result.password || '')}>Kopiér</Button>
              </Box>
            </>
          ) : result?.username ? (
            <Typography>Ejeren ({result.username}) har allerede et login og kan bruge sin nuværende adgangskode.</Typography>
          ) : (
            <Typography>Der er ingen ejer endnu. Invitér en bruger fra kundens side.</Typography>
          )}
          <Typography sx={{ mt: 2 }} color="text.secondary">
            Kunden skal godkende adgangen ved første login, før I kan arbejde i bøgerne.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => navigate(`/admin/clients/${result?.slug}`)}>Gå til kunden</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CreateClient;
