import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Alert, Autocomplete, Box, Button, Card, CardContent, Checkbox, Chip, CircularProgress, Divider, FormControlLabel,
  InputAdornment, List, ListItemButton, ListItemText, ListSubheader, MenuItem, Paper, Snackbar, Stack, Tab, Tabs,
  TextField, ToggleButton, ToggleButtonGroup, Tooltip, Typography,
} from '@mui/material';
import {
  ArrowBack, ContentCopy, Description, Print, Search, WarningAmber,
} from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { errorText, FirmClient, LEGAL_FORMS } from '../api';
import MarkdownText from '../../components/MarkdownText';

interface Meta {
  id: string; category: string; title: string; description: string; kind: string; kind_label: string;
  references: string[]; legal_forms: string[]; industry_aware: boolean;
}
interface Field {
  name: string; label: string; type: 'text' | 'textarea' | 'number' | 'date' | 'select' | 'checkbox';
  options?: string[]; default?: string; help?: string;
}
interface Rendered {
  template: Meta & { fields: Field[] };
  text: string;
  values: Record<string, any>;
  applicable: boolean;
  missing: number;
  client: null | {
    slug: string; name: string; legal_form: string; industry_code: string; industry_title: string;
    industry_groups: string[]; industry_label: string; aml_risk: string; figures: boolean;
  };
  years: { id: string; label: string; start: string; end: string }[];
  year: string | null;
}

const FORM_LABEL = Object.fromEntries(LEGAL_FORMS);
const KIND_COLOR: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'info'> = {
  brev: 'primary', erklaering: 'secondary', beslutning: 'success', arbejdspapir: 'info', tjekliste: 'warning',
};
const RISK_COLOR: Record<string, 'error' | 'warning' | 'success'> = { høj: 'error', forhøjet: 'warning', normal: 'success' };

const printText = (title: string, html: string) => {
  const w = window.open('', '_blank', 'width=900,height=1000');
  if (!w) return;
  w.document.write(`<!doctype html><html lang="da"><head><meta charset="utf-8"><title>${title.replace(/[<>&]/g, '')}</title>
    <style>body{font-family:Calibri,Arial,sans-serif;font-size:11pt;line-height:1.45;margin:2cm;color:#111}
    h1,h2,h3,h4,h5,h6{margin:1em 0 .4em}table{border-collapse:collapse;width:100%;margin:.6em 0}
    td,th{border:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top}ul,ol{padding-left:1.4em}
    p{margin:.35em 0}@page{margin:2cm}</style></head><body>${html}</body></html>`);
  w.document.close();
  w.focus();
  setTimeout(() => w.print(), 300);
};

/** Admin-portalen → Skabeloner: vælg skabelon, vælg kunde, og få dokumentet flettet. */
const Templates: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const [list, setList] = useState<Meta[]>([]);
  const [cats, setCats] = useState<{ id: string; label: string }[]>([]);
  const [errors, setErrors] = useState<{ id: string; error: string }[]>([]);
  const [clients, setClients] = useState<FirmClient[]>([]);
  const [q, setQ] = useState('');
  const [kind, setKind] = useState('');
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const selected = params.get('t') || '';
  const clientSlug = params.get('client') || '';
  const [year, setYear] = useState('');
  const [values, setValues] = useState<Record<string, any>>({});
  const [result, setResult] = useState<Rendered | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState(0);
  const [edited, setEdited] = useState<string | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);
  const seq = useRef(0);

  useEffect(() => {
    firmApi.get('/templates').then((r) => {
      setList(r.data.data.templates);
      setCats(r.data.data.categories);
      setErrors(r.data.data.errors || []);
    }).catch((e) => setError(errorText(e, 'Skabelonerne kunne ikke hentes')));
    firmApi.get('/clients').then((r) => setClients(r.data.data.clients)).catch(() => undefined);
  }, []);

  const client = clients.find((c) => c.slug === clientSlug) || null;

  const setParam = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next, { replace: k === 'client' });
  };

  // Ny skabelon eller kunde: start forfra med felterne.
  useEffect(() => { setValues({}); setEdited(null); setTab(0); }, [selected, clientSlug]);
  useEffect(() => { setYear(''); }, [clientSlug]);

  // Flet (med lille forsinkelse mens man skriver i felterne).
  useEffect(() => {
    if (!selected) { setResult(null); return undefined; }
    const my = ++seq.current;
    setLoading(true);
    const t = setTimeout(() => {
      firmApi.post(`/templates/${selected}/render`, { client: clientSlug || undefined, year: year || undefined, values })
        .then((r) => { if (my === seq.current) { setResult(r.data.data); setError(''); } })
        .catch((e) => { if (my === seq.current) setError(errorText(e, 'Skabelonen kunne ikke flettes')); })
        .finally(() => { if (my === seq.current) setLoading(false); });
    }, 250);
    return () => clearTimeout(t);
  }, [selected, clientSlug, year, values]);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return list.filter((t) => (!kind || t.kind === kind)
      && (!client || !t.legal_forms.length || t.legal_forms.includes(client.legal_form))
      && (!needle || `${t.title} ${t.description} ${t.references.join(' ')}`.toLowerCase().includes(needle)));
  }, [list, q, kind, client]);

  const text = edited ?? result?.text ?? '';

  const finalize = () => firmApi.post(`/templates/${selected}/render`, {
    client: clientSlug || undefined, year: year || undefined, values, final: true,
  }).catch(() => undefined);

  const downloadWord = async () => {
    try {
      const r = await firmApi.post(`/templates/${selected}/docx`, {
        client: clientSlug || undefined, year: year || undefined, values, text,
      }, { responseType: 'blob' });
      const cd = r.headers['content-disposition'] || '';
      const name = decodeURIComponent(/filename\*=UTF-8''([^;]+)/.exec(cd)?.[1] || `${selected}.docx`);
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url; a.download = name; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setError(errorText(e, 'Word-filen kunne ikke dannes')); }
  };

  const print = () => {
    finalize();
    setTab(0);
    setTimeout(() => printText(result?.template.title || '', previewRef.current?.innerHTML || ''), 50);
  };

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    finalize();
    setToast('Teksten er kopieret');
  };

  const field = (f: Field) => {
    const v = values[f.name] ?? result?.values?.[f.name] ?? '';
    const set = (val: any) => setValues((old) => ({ ...old, [f.name]: val }));
    if (f.type === 'checkbox') {
      return <FormControlLabel key={f.name} label={f.label}
        control={<Checkbox size="small" checked={v === true || v === 'true'} onChange={(e) => set(e.target.checked)} />} />;
    }
    if (f.type === 'select') {
      return (
        <TextField key={f.name} select size="small" fullWidth label={f.label} value={v} onChange={(e) => set(e.target.value)} helperText={f.help}>
          {(f.options || []).map((o) => <MenuItem key={o} value={o}>{o}</MenuItem>)}
        </TextField>
      );
    }
    return (
      <TextField key={f.name} size="small" fullWidth label={f.label} value={v} helperText={f.help}
        type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'}
        InputLabelProps={f.type === 'date' ? { shrink: true } : undefined}
        multiline={f.type === 'textarea'} minRows={f.type === 'textarea' ? 2 : undefined}
        onChange={(e) => set(e.target.value)} />
    );
  };

  // ---------------------------------------------------------------- oversigt
  if (!selected) {
    return (
      <Box>
        <Typography variant="h5" sx={{ mb: 0.5 }}>Skabeloner</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          Opdragsbreve, erklæringer, ledelseserklæringer, selskabsdokumenter, hvidvask, årsafslutning, skat og kundebreve.
          Vælg en skabelon og en kunde – stamdata, regnskabsår, branche og tal fra bogføringen flettes ind.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {errors.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {errors.length} skabelon(er) kunne ikke indlæses: {errors.map((e) => e.id).join(', ')}
          </Alert>
        )}
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }} alignItems={{ md: 'center' }}>
          <TextField size="small" placeholder="Søg fx opdragsbrev, ISA 580, udbytte …" value={q} onChange={(e) => setQ(e.target.value)}
            sx={{ minWidth: 320 }} InputProps={{ startAdornment: <InputAdornment position="start"><Search fontSize="small" /></InputAdornment> }} />
          <Autocomplete size="small" sx={{ minWidth: 300 }} options={clients} value={client}
            getOptionLabel={(c) => `${c.name}${c.cvr ? ` (${c.cvr})` : ''}`}
            onChange={(_, c) => setParam('client', c?.slug || '')}
            renderInput={(p) => <TextField {...p} label="Kunde (valgfri – filtrerer efter selskabsform)" />} />
          <ToggleButtonGroup size="small" exclusive value={kind} onChange={(_, v) => setKind(v || '')}>
            <ToggleButton value="">Alle</ToggleButton>
            <ToggleButton value="brev">Breve</ToggleButton>
            <ToggleButton value="erklaering">Erklæringer</ToggleButton>
            <ToggleButton value="beslutning">Beslutninger</ToggleButton>
            <ToggleButton value="arbejdspapir">Arbejdspapirer</ToggleButton>
            <ToggleButton value="tjekliste">Tjeklister</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
        <Box sx={{ columnCount: { xs: 1, lg: 2 }, columnGap: 2 }}>
          {cats.map((c) => {
            const items = shown.filter((t) => t.category === c.id);
            if (!items.length) return null;
            return (
              <Paper key={c.id} variant="outlined" sx={{ mb: 2, breakInside: 'avoid' }}>
                <List dense disablePadding subheader={
                  <ListSubheader sx={{ bgcolor: 'action.hover', lineHeight: '36px', fontWeight: 600 }}>
                    {c.label} <Typography component="span" variant="caption" color="text.secondary">· {items.length}</Typography>
                  </ListSubheader>}>
                  {items.map((t) => (
                    <ListItemButton key={t.id} onClick={() => setParam('t', t.id)} sx={{ alignItems: 'flex-start' }}>
                      <Description fontSize="small" color="action" sx={{ mt: 0.4, mr: 1.2 }} />
                      <ListItemText
                        primary={<Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                          <span>{t.title}</span>
                          <Chip size="small" variant="outlined" color={KIND_COLOR[t.kind] || 'default'} label={t.kind_label} sx={{ height: 18, fontSize: 10.5 }} />
                          {t.industry_aware && <Tooltip title="Tilpasses kundens branchekode"><Chip size="small" label="Branche" sx={{ height: 18, fontSize: 10.5 }} /></Tooltip>}
                        </Box>}
                        secondary={t.description}
                        primaryTypographyProps={{ fontSize: 13.5 }} secondaryTypographyProps={{ fontSize: 12 }} />
                    </ListItemButton>
                  ))}
                </List>
              </Paper>
            );
          })}
        </Box>
        {list.length > 0 && shown.length === 0 && <Typography color="text.secondary">Ingen skabeloner matcher.</Typography>}
      </Box>
    );
  }

  // ---------------------------------------------------------------- én skabelon
  const meta = result?.template || list.find((t) => t.id === selected);
  const fields = result?.template.fields || [];
  return (
    <Box>
      <Button size="small" startIcon={<ArrowBack />} onClick={() => setParam('t', '')} sx={{ mb: 1 }}>Alle skabeloner</Button>
      {meta && (
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography variant="h5">{meta.title}</Typography>
            <Chip size="small" color={KIND_COLOR[meta.kind] || 'default'} label={meta.kind_label} />
          </Box>
          <Typography color="text.secondary" variant="body2" sx={{ mt: 0.5 }}>{meta.description}</Typography>
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
            {meta.references.map((r) => <Chip key={r} size="small" variant="outlined" label={r} />)}
            {meta.legal_forms.length > 0 && <Chip size="small" variant="outlined" color="info"
              label={`Gælder: ${meta.legal_forms.map((f) => FORM_LABEL[f] || f).join(', ')}`} />}
          </Box>
        </Box>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '340px 1fr' }, gap: 2, alignItems: 'start' }}>
        <Stack spacing={2}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Kunde</Typography>
              <Autocomplete size="small" options={clients} value={client}
                getOptionLabel={(c) => `${c.name}${c.cvr ? ` (${c.cvr})` : ''}`}
                onChange={(_, c) => setParam('client', c?.slug || '')}
                renderInput={(p) => <TextField {...p} label="Vælg kunde" />} />
              {result && result.years.length > 0 && (
                <TextField select size="small" fullWidth sx={{ mt: 1.5 }} label="Regnskabsår" value={year || result.year || ''}
                  onChange={(e) => setYear(e.target.value)}>
                  {result.years.map((y) => <MenuItem key={y.id} value={y.id}>{y.label} ({y.start} – {y.end})</MenuItem>)}
                </TextField>
              )}
              {result?.client && (
                <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 0.75 }}>
                  <Typography variant="caption" color="text.secondary">
                    {result.client.legal_form}
                    {result.client.industry_code ? ` · ${result.client.industry_code} ${result.client.industry_title}` : ' · ingen branchekode'}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {result.client.industry_label && <Chip size="small" label={`Branche: ${result.client.industry_label}`} />}
                    {result.client.industry_code && <Chip size="small" color={RISK_COLOR[result.client.aml_risk] || 'default'} variant="outlined"
                      label={`Hvidvaskrisiko: ${result.client.aml_risk}`} />}
                    <Chip size="small" variant="outlined" label={result.client.figures ? 'Tal fra bogføringen' : 'Ingen tal fra bogføringen'} />
                  </Box>
                  {meta?.industry_aware && !result.client.industry_code && (
                    <Alert severity="info" sx={{ py: 0 }}>Kunden har ingen branchekode – de branchespecifikke afsnit udelades. Tilføj den under kundens stamdata.</Alert>
                  )}
                </Box>
              )}
              {result && !result.applicable && (
                <Alert severity="warning" icon={<WarningAmber />} sx={{ mt: 1.5 }}>
                  Skabelonen er beregnet til {result.template.legal_forms.map((f) => FORM_LABEL[f] || f).join(', ')} – kunden er {result.client?.legal_form}.
                </Alert>
              )}
            </CardContent>
          </Card>
          {fields.length > 0 && (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" sx={{ mb: 1.5 }}>Oplysninger til dokumentet</Typography>
                <Stack spacing={1.5}>{fields.map(field)}</Stack>
              </CardContent>
            </Card>
          )}
        </Stack>

        <Card variant="outlined" sx={{ minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', px: 1, borderBottom: 1, borderColor: 'divider', flexWrap: 'wrap', gap: 1 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="Dokument" />
              <Tab label={edited !== null ? 'Redigér (ændret)' : 'Redigér'} />
            </Tabs>
            {loading && <CircularProgress size={16} />}
            <Box sx={{ ml: 'auto', display: 'flex', gap: 1, py: 0.75 }}>
              <Button size="small" variant="contained" startIcon={<Description />} disabled={!text} onClick={downloadWord}>Word</Button>
              <Button size="small" variant="outlined" startIcon={<Print />} disabled={!text} onClick={print}>Udskriv / PDF</Button>
              <Button size="small" startIcon={<ContentCopy />} disabled={!text} onClick={copy}>Kopiér</Button>
            </Box>
          </Box>
          {result && result.missing > 0 && (
            <Alert severity="info" sx={{ borderRadius: 0 }}>
              {result.missing} oplysning(er) mangler og er markeret med <b>[…]</b>{!client ? ' – vælg en kunde for at udfylde stamdata' : ''}.
            </Alert>
          )}
          {edited !== null && (
            <Alert severity="warning" sx={{ borderRadius: 0 }} action={<Button size="small" onClick={() => setEdited(null)}>Gendan</Button>}>
              Du har rettet i teksten. Ændringer i felterne slår først igennem, når du trykker Gendan – så går rettelserne tabt.
            </Alert>
          )}
          <CardContent>
            {tab === 0 ? (
              <Box ref={previewRef} sx={{ maxWidth: 820 }}>
                <MarkdownText text={text} />
              </Box>
            ) : (
              <TextField fullWidth multiline minRows={24} value={text} onChange={(e) => setEdited(e.target.value)}
                InputProps={{ sx: { fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 12.5 } }} />
            )}
          </CardContent>
          <Divider />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', p: 1.5 }}>
            Skabelonen er et udgangspunkt. Den underskrivende revisor er ansvarlig for, at dokumentet passer til den konkrete opgave.
          </Typography>
        </Card>
      </Box>
      <Snackbar open={!!toast} autoHideDuration={2500} onClose={() => setToast('')} message={toast} />
    </Box>
  );
};

export default Templates;
