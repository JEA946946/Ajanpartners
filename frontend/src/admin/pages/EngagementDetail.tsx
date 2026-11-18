import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Autocomplete, Box, Button, Chip, Dialog, DialogActions,
  DialogContent, DialogTitle, Grid, LinearProgress, MenuItem, Paper, Stack, TextField, ToggleButton,
  ToggleButtonGroup, Typography,
} from '@mui/material';
import { ArrowBack, Description, ExpandMore } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { useAdmin } from '../AdminContext';
import { Meta, STATUS_COLOR } from './Engagements';
import FeePanel from '../components/FeePanel';

interface Item { id: string; section: string; text: string; status: string; note: string; by: string | null; at: string | null }
interface Run { id: string; template_id: string; title: string; items: Item[]; done: number; total: number }
interface Sign { id: string; step: string; step_label: string; user: string; at: string; note: string; revoked_at: string | null; revoked_by: string | null }
interface Detail {
  id: string; client: string; client_name: string; kind: string; kind_label: string; title: string; year_label: string;
  partner_id: number | null; manager_id: number | null; status: string; status_label: string; deadline: string | null;
  budget_hours: string | null; note: string; checklists: Run[]; signoffs: Sign[]; signoff_history: Sign[];
  letter_template: string | null; acceptance_status: string; kyc_status: string; open_conflicts: number;
  year_start: string | null;
}
const STEPS: [string, string][] = [['udfoert', 'Udført'], ['gennemgaaet', 'Gennemgået'], ['godkendt', 'Godkendt']];
const plain = (s: string) => s.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\*(.+?)\*/g, '$1');

/** Admin → Opdrag → et opdrag: stamdata, tjeklister og sign-off. */
const EngagementDetail: React.FC = () => {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { staff, isPartner } = useAdmin();
  const [e, setE] = useState<Detail | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [addTpl, setAddTpl] = useState<string | null>(null);
  const [reopen, setReopen] = useState<string | null>(null);
  const [noteEdit, setNoteEdit] = useState<{ run: string; item: Item } | null>(null);

  const load = useCallback(() => {
    firmApi.get(`/engagements/${id}`).then((r) => setE(r.data.data.engagement))
      .catch((err) => setError(errorText(err, 'Opdraget kunne ikke hentes')));
  }, [id]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => { firmApi.get('/engagements/meta').then((r) => setMeta(r.data.data)).catch(() => undefined); }, []);
  if (!e) return error ? <Alert severity="error">{error}</Alert> : null;

  const locked = e.signoffs.length > 0;
  const update = async (patch: Record<string, unknown>) => {
    try { const r = await firmApi.put(`/engagements/${id}`, patch); setE(r.data.data.engagement); setError(''); } catch (err) { setError(errorText(err)); }
  };
  const setItem = async (run: string, item: Item, status: string, note = item.note) => {
    try {
      const r = await firmApi.put(`/checklist-runs/${run}/items/${item.id}`, { status, note });
      const updated: Run = r.data.data.checklist;
      setE((prev) => prev && ({ ...prev, checklists: prev.checklists.map((c) => (c.id === run ? { ...c, ...updated } : c)) }));
      setError('');
    } catch (err) { setError(errorText(err)); }
  };
  const sign = async (step: string) => {
    try { const r = await firmApi.post(`/engagements/${id}/signoff`, { step }); setE(r.data.data.engagement); setError(''); } catch (err) { setError(errorText(err)); }
  };
  const doReopen = async () => {
    try { const r = await firmApi.post(`/engagements/${id}/reopen`, { note: reopen }); setE(r.data.data.engagement); setReopen(null); } catch (err) { setError(errorText(err)); }
  };
  const addList = async () => {
    if (!addTpl) return;
    try { await firmApi.post(`/engagements/${id}/checklists`, { template_id: addTpl }); setAddOpen(false); setAddTpl(null); load(); } catch (err) { setError(errorText(err)); }
  };
  const removeList = async (run: Run) => {
    try { await firmApi.delete(`/checklist-runs/${run.id}/items/all`); load(); } catch (err) { setError(errorText(err)); }
  };
  const done = e.checklists.reduce((n, r) => n + r.done, 0);
  const total = e.checklists.reduce((n, r) => n + r.total, 0);
  const active = Object.fromEntries(e.signoffs.map((s) => [s.step, s]));
  const nextStep = STEPS.find(([k]) => !active[k])?.[0];
  const name = (uid: number | null) => {
    const s = staff.find((x) => x.user_id === uid);
    return s ? `${s.first_name} ${s.last_name}`.trim() || s.username : '';
  };

  return (
    <Box sx={{ maxWidth: 1100 }}>
      <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)} sx={{ mb: 1, ml: -1 }}>Tilbage</Button>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
        <Typography variant="h5">{e.title}{e.year_label && ` ${e.year_label}`}</Typography>
        <Chip size="small" color={STATUS_COLOR[e.status]} label={e.status_label} />
        <Box sx={{ flex: 1 }} />
        <Button size="small" onClick={() => navigate(`/admin/clients/${e.client}`)}>{e.client_name}</Button>
        <Button size="small" onClick={() => navigate(`/admin/time?client=${e.client}&engagement=${e.id}`)}>Registrér tid</Button>
        {e.letter_template && (
          <Button size="small" startIcon={<Description />} onClick={() => navigate(`/admin/templates?t=${e.letter_template}&client=${e.client}`)}>Opdragsbrev</Button>
        )}
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {meta?.kinds.find((k) => k.value === e.kind)?.assurance && (e.acceptance_status !== 'approved' || e.kyc_status !== 'ok' || e.open_conflicts > 0) && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Før en partner kan godkende opdraget, skal kunden være accepteret{e.acceptance_status !== 'approved' ? ' (mangler)' : ''},
          kundekendskabet være opdateret{e.kyc_status !== 'ok' ? ' (mangler)' : ''}
          {e.open_conflicts > 0 ? `, og ${e.open_conflicts} uafhængighedsforhold afklares` : ''}.
        </Alert>
      )}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Partner" value={e.partner_id ?? ''} disabled={locked}
              onChange={(ev) => update({ partner_id: ev.target.value || null })}>
              <MenuItem value="">–</MenuItem>
              {staff.filter((s) => s.role === 'partner').map((s) => <MenuItem key={s.user_id} value={s.user_id}>{name(s.user_id)}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField select fullWidth size="small" label="Opgaveansvarlig" value={e.manager_id ?? ''}
              onChange={(ev) => update({ manager_id: ev.target.value || null })}>
              <MenuItem value="">–</MenuItem>
              {staff.filter((s) => s.is_active).map((s) => <MenuItem key={s.user_id} value={s.user_id}>{name(s.user_id)}</MenuItem>)}
            </TextField>
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField fullWidth size="small" type="date" label="Frist" InputLabelProps={{ shrink: true }} value={e.deadline || ''}
              onChange={(ev) => update({ deadline: ev.target.value || null })} />
          </Grid>
          <Grid item xs={6} sm={2}>
            <TextField fullWidth size="small" type="number" label="Timebudget" defaultValue={e.budget_hours || ''}
              onBlur={(ev) => update({ budget_hours: ev.target.value })} />
          </Grid>
          <Grid item xs={12} sm={2}>
            {e.status === 'afsluttet' && <Button fullWidth variant="outlined" onClick={() => update({ status: 'leveret' })}>Markér leveret</Button>}
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline minRows={1} size="small" label="Noter" defaultValue={e.note} key={e.note}
              onBlur={(ev) => ev.target.value !== e.note && update({ note: ev.target.value })} />
          </Grid>
        </Grid>
      </Paper>

      <FeePanel engagementId={e.id} />

      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Sign-off</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems={{ sm: 'center' }}>
          {STEPS.map(([k, lbl]) => (
            <Box key={k} sx={{ flex: 1, p: 1.5, border: 1, borderColor: active[k] ? 'success.main' : 'divider', borderRadius: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>{lbl}</Typography>
              {active[k]
                ? <Typography variant="body2">{active[k].user} · {formatDate(active[k].at)}</Typography>
                : k === nextStep
                  ? <Button size="small" variant="contained" sx={{ mt: 0.5 }} onClick={() => sign(k)}>Signér som {lbl.toLowerCase()}</Button>
                  : <Typography variant="body2" color="text.secondary">Afventer</Typography>}
            </Box>
          ))}
        </Stack>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          Udført kræver, at alle tjeklistepunkter er besvaret. Gennemgang skal foretages af en anden revisor eller partner end den,
          der har udført arbejdet. Godkendelse foretages af en partner. Når opdraget er signeret, er tjeklisterne låst.
        </Typography>
        {locked && isPartner && <Button size="small" color="warning" sx={{ mt: 1 }} onClick={() => setReopen('')}>Genåbn opdraget</Button>}
        {e.signoff_history.some((s) => s.revoked_at) && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Tidligere sign-off: {e.signoff_history.filter((s) => s.revoked_at).map((s) => `${s.step_label} (${s.user}, ${formatDate(s.at)}, fortrudt ${formatDate(s.revoked_at)})`).join(' · ')}
          </Typography>
        )}
      </Paper>

      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 2 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Tjeklister</Typography>
        {total > 0 && <Box sx={{ flex: 1, maxWidth: 300 }}><LinearProgress variant="determinate" value={(100 * done) / total} /></Box>}
        {total > 0 && <Typography variant="caption">{done}/{total}</Typography>}
        <Box sx={{ flex: 1 }} />
        {!locked && <Button size="small" variant="outlined" onClick={() => setAddOpen(true)}>Tilføj tjekliste</Button>}
      </Box>
      {e.checklists.length === 0 && <Typography variant="body2" color="text.secondary">Ingen tjeklister. Tilføj en fra skabelonerne.</Typography>}
      {e.checklists.map((run) => {
        let section = '';
        return (
          <Accordion key={run.id} disableGutters variant="outlined">
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', width: '100%' }}>
                <Typography sx={{ fontWeight: 500, flex: 1 }}>{run.title}</Typography>
                <Chip size="small" color={run.done === run.total ? 'success' : 'default'} label={`${run.done}/${run.total}`} />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              {run.items.map((it) => {
                const head = it.section !== section ? (section = it.section) : null;
                return (
                  <React.Fragment key={it.id}>
                    {head && <Typography variant="subtitle2" sx={{ mt: 1.5, mb: 0.5 }}>{head}</Typography>}
                    <Box sx={{ display: 'flex', gap: 1, py: 0.75, borderTop: 1, borderColor: 'divider', alignItems: 'flex-start' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body2">{plain(it.text)}</Typography>
                        {it.note && <Typography variant="caption" color="warning.dark" sx={{ display: 'block' }}>{it.note}</Typography>}
                        {it.by && <Typography variant="caption" color="text.secondary">{it.by} · {formatDate(it.at)}</Typography>}
                      </Box>
                      <ToggleButtonGroup size="small" exclusive value={it.status} disabled={locked}
                        onChange={(_, v) => {
                          if (v === 'bemaerkning') setNoteEdit({ run: run.id, item: it });
                          else if (v !== null) setItem(run.id, it, v);
                          else setItem(run.id, it, '');
                        }}>
                        <ToggleButton value="ok" color="success">OK</ToggleButton>
                        <ToggleButton value="ikke_relevant">I/R</ToggleButton>
                        <ToggleButton value="bemaerkning" color="warning">Bem.</ToggleButton>
                      </ToggleButtonGroup>
                    </Box>
                  </React.Fragment>
                );
              })}
              {!locked && run.done === 0 && <Button size="small" color="inherit" sx={{ mt: 1 }} onClick={() => removeList(run)}>Fjern tjeklisten</Button>}
            </AccordionDetails>
          </Accordion>
        );
      })}

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Tilføj tjekliste</DialogTitle>
        <DialogContent sx={{ pt: '8px !important' }}>
          <Autocomplete size="small" options={meta?.checklist_templates || []} groupBy={(o) => o.category}
            getOptionLabel={(o) => o.title} value={meta?.checklist_templates.find((t) => t.id === addTpl) || null}
            onChange={(_, v) => setAddTpl(v?.id || null)} renderInput={(p) => <TextField {...p} label="Skabelon" />} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Annullér</Button>
          <Button variant="contained" disabled={!addTpl} onClick={addList}>Tilføj</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={reopen !== null} onClose={() => setReopen(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Genåbn opdraget</DialogTitle>
        <DialogContent sx={{ pt: '8px !important' }}>
          <TextField fullWidth multiline minRows={2} size="small" label="Begrundelse" value={reopen || ''} onChange={(ev) => setReopen(ev.target.value)} />
          <Typography variant="caption" color="text.secondary">Sign-off fortrydes, men bevares i historikken.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReopen(null)}>Annullér</Button>
          <Button variant="contained" color="warning" disabled={!reopen?.trim()} onClick={doReopen}>Genåbn</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!noteEdit} onClose={() => setNoteEdit(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Bemærkning</DialogTitle>
        <DialogContent sx={{ pt: '8px !important' }}>
          <Typography variant="body2" sx={{ mb: 1 }}>{noteEdit && plain(noteEdit.item.text)}</Typography>
          <TextField fullWidth multiline minRows={2} size="small" label="Bemærkning / henvisning til arbejdspapir" autoFocus
            defaultValue={noteEdit?.item.note} id="item-note" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteEdit(null)}>Annullér</Button>
          <Button variant="contained" onClick={() => {
            const v = (document.getElementById('item-note') as HTMLInputElement)?.value || '';
            if (noteEdit) setItem(noteEdit.run, noteEdit.item, 'bemaerkning', v);
            setNoteEdit(null);
          }}>Gem</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EngagementDetail;
