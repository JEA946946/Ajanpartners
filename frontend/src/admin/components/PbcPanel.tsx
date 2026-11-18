import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions,
  DialogContent, DialogTitle, FormControlLabel, LinearProgress, MenuItem, Paper, TextField, Typography,
} from '@mui/material';
import { ExpandMore } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';

interface PbcItem { id: string; title: string; description: string; status: string; status_label: string; due_date: string | null }
interface PbcList { name: string; items: PbcItem[]; done: number; answered: number; overdue: number }
interface Data { lists: PbcList[]; templates: { id: string; title: string }[] }

const STATUS_COLOR: Record<string, 'warning' | 'info' | 'default' | 'success' | 'primary'> = {
  open: 'warning', answered: 'info', in_progress: 'primary', closed: 'success',
};
const plain = (s: string) => s.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1');

/** Materialeliste (PBC) til kunden: punkter fra de verificerede skabeloner, besvares i kundens indbakke. */
const PbcPanel: React.FC<{ engagementId: string; yearLabel: string }> = ({ engagementId, yearLabel }) => {
  const [d, setD] = useState<Data | null>(null);
  const [send, setSend] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/engagements/${engagementId}/pbc`).then((r) => setD(r.data.data)).catch((e) => setError(errorText(e)));
  }, [engagementId]);
  useEffect(() => { load(); }, [load]);
  if (!d) return null;

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Materialeliste til kunden</Typography>
        <Button size="small" variant="outlined" onClick={() => setSend(true)}>Send materialeliste</Button>
      </Box>
      <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
        Punkterne sendes som forespørgsler til kundens indbakke, hvor kunden svarer og vedhæfter bilag. Svarene ses under
        Opgaver og forespørgsler; luk et punkt, når materialet er modtaget.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}
      {d.lists.length === 0 && <Typography variant="body2" color="text.secondary">Ingen materialeliste sendt.</Typography>}
      {d.lists.map((l) => (
        <Accordion key={l.name} disableGutters>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', flexWrap: 'wrap' }}>
              <Typography sx={{ fontWeight: 600 }}>{l.name}</Typography>
              <Box sx={{ minWidth: 140 }}>
                <LinearProgress variant="determinate" value={(100 * l.done) / l.items.length} />
                <Typography variant="caption">{l.done}/{l.items.length} modtaget · {l.answered} besvaret</Typography>
              </Box>
              {l.overdue > 0 && <Chip size="small" color="error" label={`${l.overdue} over frist`} />}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {l.items.map((i) => (
              <Box key={i.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5, borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="body2" sx={{ flex: 1 }}>{i.title}</Typography>
                {i.due_date && <Typography variant="caption">{formatDate(i.due_date)}</Typography>}
                <Chip size="small" color={STATUS_COLOR[i.status]} label={i.status_label} />
              </Box>
            ))}
          </AccordionDetails>
        </Accordion>
      ))}
      {send && <SendDialog engagementId={engagementId} templates={d.templates} yearLabel={yearLabel}
        onClose={() => setSend(false)} onSent={(x) => { setD(x); setSend(false); }} />}
    </Paper>
  );
};

const SendDialog: React.FC<{
  engagementId: string; templates: { id: string; title: string }[]; yearLabel: string;
  onClose: () => void; onSent: (d: Data) => void;
}> = ({ engagementId, templates, yearLabel, onClose, onSent }) => {
  const [tpl, setTpl] = useState(templates[0]?.id || '');
  const [items, setItems] = useState<{ section: string; text: string }[]>([]);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [name, setName] = useState('');
  const [due, setDue] = useState('');
  const [extra, setExtra] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!tpl) return;
    firmApi.get(`/engagements/${engagementId}/pbc/preview`, { params: { template: tpl } }).then((r) => {
      const its = r.data.data.items;
      setItems(its); setSel(new Set(its.map((_: unknown, n: number) => n)));
      setName(`${r.data.data.template.title.replace(/\s*\(PBC\)\s*/, '')}${yearLabel ? ` ${yearLabel}` : ''}`);
    }).catch((e) => setError(errorText(e)));
  }, [tpl, engagementId, yearLabel]);

  const sections = useMemo(() => {
    const m = new Map<string, number[]>();
    items.forEach((i, n) => m.set(i.section, [...(m.get(i.section) || []), n]));
    return [...m.entries()];
  }, [items]);
  const toggle = (ns: number[], on: boolean) => setSel((s) => { const x = new Set(s); ns.forEach((n) => (on ? x.add(n) : x.delete(n))); return x; });

  const submit = async () => {
    const chosen = items.filter((_, n) => sel.has(n)).map((i) => ({ title: plain(i.text), section: i.section }));
    extra.split('\n').map((s) => s.trim()).filter(Boolean).forEach((t) => chosen.push({ title: t, section: 'Øvrigt' }));
    try {
      const r = await firmApi.post(`/engagements/${engagementId}/pbc`, { list_name: name, due_date: due || null, items: chosen });
      onSent(r.data.data);
    } catch (e) { setError(errorText(e)); }
  };

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Send materialeliste</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Box sx={{ display: 'flex', gap: 2, mt: 1, mb: 2, flexWrap: 'wrap' }}>
          <TextField select size="small" label="Skabelon" sx={{ minWidth: 260 }} value={tpl} onChange={(e) => setTpl(e.target.value)}>
            {templates.map((t) => <MenuItem key={t.id} value={t.id}>{t.title}</MenuItem>)}
          </TextField>
          <TextField size="small" label="Listens navn" sx={{ flex: 1, minWidth: 220 }} value={name} onChange={(e) => setName(e.target.value)} />
          <TextField size="small" type="date" label="Frist for kunden" InputLabelProps={{ shrink: true }} value={due} onChange={(e) => setDue(e.target.value)} />
        </Box>
        <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 1 }}>
          Punkterne er flettet for kunden og året (branche- og selskabsafhængige punkter er med). Fravælg dem, der ikke er relevante.
          Valgt: {sel.size} af {items.length}.
        </Typography>
        {sections.map(([sec, ns]) => {
          const all = ns.every((n) => sel.has(n));
          return (
            <Accordion key={sec} disableGutters>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <FormControlLabel onClick={(e) => e.stopPropagation()} label={`${sec || 'Generelt'} (${ns.filter((n) => sel.has(n)).length}/${ns.length})`}
                  control={<Checkbox size="small" checked={all} indeterminate={!all && ns.some((n) => sel.has(n))} onChange={(e) => toggle(ns, e.target.checked)} />} />
              </AccordionSummary>
              <AccordionDetails>
                {ns.map((n) => (
                  <FormControlLabel key={n} sx={{ display: 'flex', alignItems: 'flex-start' }} label={<Typography variant="body2">{plain(items[n].text)}</Typography>}
                    control={<Checkbox size="small" checked={sel.has(n)} onChange={(e) => toggle([n], e.target.checked)} />} />
                ))}
              </AccordionDetails>
            </Accordion>
          );
        })}
        <TextField fullWidth multiline minRows={2} size="small" sx={{ mt: 2 }} label="Ekstra punkter (ét pr. linje)"
          value={extra} onChange={(e) => setExtra(e.target.value)} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Annullér</Button>
        <Button variant="contained" disabled={!name.trim() || (sel.size === 0 && !extra.trim())} onClick={submit}>
          Send til kundens indbakke
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PbcPanel;
