import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Checkbox, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Grid,
  MenuItem, Paper, Radio, RadioGroup, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { Description, Download } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';

export interface KycPerson {
  id: string; role: string; role_label: string; name: string; birth_date: string | null; country: string;
  ownership: string; is_pep: boolean; pep_note: string; id_method: string; has_document: boolean;
  verified_on: string | null; verified_by: string | null; active: boolean;
}
interface Answer { answer: string; note: string }
export interface KycAssessment {
  id: string; version: number; risk_level: string; risk_label: string; purpose: string; source_of_funds: string;
  reasons: string; answers: Record<string, Answer>; next_review_on: string | null; status: string;
  created_by: string | null; created_at: string; approved_by: string | null; approved_at: string | null; sha256: string;
}
interface Question { id: string; text: string; ref: string; risk_if?: string }
interface Suggestion {
  risk_level: string; reasons: string[]; focus: string[]; industry: string; industry_risk: string | null;
  official_risk_industry: boolean; note: string;
}
interface KycData {
  status: string; persons: KycPerson[]; assessments: KycAssessment[]; suggestion: Suggestion;
  checklist: { title: string; version: string; source: string; questions: Question[] }; can_approve: boolean;
}

export const KYC_STATUS: Record<string, { text: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
  ok: { text: 'Opdateret', color: 'success' },
  due: { text: 'Skal opdateres', color: 'error' },
  missing: { text: 'Mangler', color: 'error' },
  draft: { text: 'Kladde – afventer godkendelse', color: 'warning' },
};
export const RISK_LEVELS: [string, string][] = [['lav', 'Lav'], ['normal', 'Normal'], ['hoej', 'Høj']];
const RISK_COLOR: Record<string, 'success' | 'warning' | 'error'> = { lav: 'success', normal: 'warning', hoej: 'error' };
const ROLES: [string, string][] = [
  ['reel_ejer', 'Reel ejer'], ['ledelse', 'Ledelse'], ['tegningsberettiget', 'Tegningsberettiget'],
  ['fuldmagt', 'Handler på kundens vegne'],
];
const EMPTY_PERSON = {
  role: 'reel_ejer', name: '', birth_date: '', country: 'Danmark', ownership: '', is_pep: false, pep_note: '',
  id_method: '', verified_on: '',
};

/** Fanen "Hvidvask" på en kunde: personer, risikovurdering (kladde → partnergodkendelse) og historik. */
const KycPanel: React.FC<{ slug: string; templateClient: string }> = ({ slug, templateClient }) => {
  const navigate = useNavigate();
  const [data, setData] = useState<KycData | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [personDlg, setPersonDlg] = useState<{ id?: string; form: typeof EMPTY_PERSON; file: File | null } | null>(null);
  const [draft, setDraft] = useState<KycAssessment | null>(null);

  const load = useCallback(() => {
    firmApi.get(`/clients/${slug}/kyc`).then((r) => {
      const d: KycData = r.data.data;
      setData(d);
      setDraft(d.assessments.find((a) => a.status === 'kladde') || null);
    }).catch((e) => setError(errorText(e, 'Kundekendskab kunne ikke hentes')));
  }, [slug]);
  useEffect(() => { load(); }, [load]);

  if (!data) return error ? <Alert severity="error">{error}</Alert> : null;
  const { suggestion: sug, checklist } = data;
  const approved = data.assessments.filter((a) => a.status === 'godkendt');
  const hasPep = data.persons.some((p) => p.active && p.is_pep);

  const savePerson = async () => {
    if (!personDlg) return;
    const fd = new FormData();
    Object.entries(personDlg.form).forEach(([k, v]) => fd.append(k, String(v ?? '')));
    if (personDlg.file) fd.append('id_document', personDlg.file);
    try {
      if (personDlg.id) await firmApi.put(`/kyc/persons/${personDlg.id}`, fd);
      else await firmApi.post(`/clients/${slug}/kyc/persons`, fd);
      setPersonDlg(null);
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const inactivate = async (p: KycPerson) => {
    try { await firmApi.delete(`/kyc/persons/${p.id}`); load(); } catch (e) { setError(errorText(e)); }
  };
  const download = async (p: KycPerson) => {
    const r = await firmApi.get(`/kyc/persons/${p.id}/document`, { responseType: 'blob' });
    const url = URL.createObjectURL(r.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `id-${p.name}`;
    a.click();
    URL.revokeObjectURL(url);
  };
  const newAssessment = async () => {
    try { await firmApi.post(`/clients/${slug}/kyc`, {}); load(); } catch (e) { setError(errorText(e)); }
  };
  const saveDraft = async (quiet = false) => {
    if (!draft) return false;
    try {
      const r = await firmApi.put(`/kyc/assessments/${draft.id}`, draft);
      setDraft(r.data.data.assessment);
      if (!quiet) setInfo('Kladden er gemt.');
      return true;
    } catch (e) { setError(errorText(e)); return false; }
  };
  const approve = async () => {
    if (!draft || !(await saveDraft(true))) return;
    try {
      await firmApi.post(`/kyc/assessments/${draft.id}/approve`);
      setInfo('Kundekendskabet er godkendt og låst.');
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const setAnswer = (id: string, patch: Partial<Answer>) => draft && setDraft({
    ...draft, answers: { ...draft.answers, [id]: { ...{ answer: '', note: '' }, ...draft.answers[id], ...patch } },
  });
  const edit = (p?: KycPerson) => setPersonDlg({
    id: p?.id, file: null,
    form: p ? {
      role: p.role, name: p.name, birth_date: p.birth_date || '', country: p.country, ownership: p.ownership,
      is_pep: p.is_pep, pep_note: p.pep_note, id_method: p.id_method, verified_on: p.verified_on || '',
    } : { ...EMPTY_PERSON },
  });
  const pf = personDlg?.form;
  const setPf = (patch: Partial<typeof EMPTY_PERSON>) => personDlg && setPersonDlg({ ...personDlg, form: { ...personDlg.form, ...patch } });

  return (
    <Stack spacing={2}>
      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" onClose={() => setInfo('')}>{info}</Alert>}

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Kundekendskab</Typography>
          <Chip size="small" color={KYC_STATUS[data.status].color} label={KYC_STATUS[data.status].text} />
          {approved[0] && (
            <Typography variant="body2" color="text.secondary">
              Godkendt {formatDate(approved[0].approved_at)} af {approved[0].approved_by} · risiko {approved[0].risk_label}
              {approved[0].next_review_on && <> · næste opdatering {formatDate(approved[0].next_review_on)}</>}
            </Typography>
          )}
          <Box sx={{ flex: 1 }} />
          <Button size="small" startIcon={<Description />}
            onClick={() => navigate(`/admin/templates?t=kyc-juridisk-person&client=${templateClient}`)}>
            Kundekendskabsskema (Word)
          </Button>
        </Box>
        <Alert severity="info" variant="outlined" sx={{ mt: 1 }}>
          <b>Systemets forslag: risiko {RISK_LEVELS.find(([k]) => k === sug.risk_level)?.[1]}</b>
          {sug.industry && <> · branche: {sug.industry}</>}
          {sug.official_risk_industry && <> · <b>officiel risikobranche</b> (ÅRL § 135, stk. 5)</>}
          {sug.reasons.length > 0 && (
            <Box component="ul" sx={{ my: 0.5, pl: 2.5 }}>{sug.reasons.map((r) => <li key={r}>{r}</li>)}</Box>
          )}
          <Typography variant="caption" color="text.secondary">{sug.note} Du skal selv tage stilling.</Typography>
        </Alert>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Reelle ejere, ledelse og fuldmagtshavere</Typography>
          <Button size="small" variant="outlined" onClick={() => edit()}>Tilføj person</Button>
        </Box>
        {data.persons.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            Ingen personer registreret. Find de reelle ejere i CVR (Erhvervsstyrelsen) og kontrollér deres identitet (HVL § 11, stk. 1, nr. 3).
          </Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Navn</TableCell><TableCell>Rolle</TableCell><TableCell>Ejerskab</TableCell>
                <TableCell>Identitet kontrolleret</TableCell><TableCell>PEP</TableCell><TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {data.persons.map((p) => (
                <TableRow key={p.id} sx={{ opacity: p.active ? 1 : 0.5 }}>
                  <TableCell>{p.name}{p.birth_date && <Typography variant="caption" sx={{ display: 'block' }}>f. {formatDate(p.birth_date)}</Typography>}</TableCell>
                  <TableCell>{p.role_label}{!p.active && ' (ikke længere aktuel)'}</TableCell>
                  <TableCell>{p.ownership || '–'}</TableCell>
                  <TableCell>
                    {p.verified_on ? `${formatDate(p.verified_on)} (${p.verified_by || '–'})` : <Chip size="small" color="warning" label="Ikke kontrolleret" />}
                    {p.id_method && <Typography variant="caption" sx={{ display: 'block' }}>{p.id_method}</Typography>}
                  </TableCell>
                  <TableCell>{p.is_pep ? <Chip size="small" color="error" label="PEP" /> : 'Nej'}</TableCell>
                  <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                    {p.has_document && <Button size="small" startIcon={<Download />} onClick={() => download(p)}>ID</Button>}
                    {p.active && <Button size="small" onClick={() => edit(p)}>Ret</Button>}
                    {p.active && <Button size="small" color="inherit" onClick={() => inactivate(p)}>Ikke aktuel</Button>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>
            Risikovurdering{draft ? ` – version ${draft.version} (kladde)` : ''}
          </Typography>
          {!draft && <Button size="small" variant="contained" onClick={newAssessment}>{approved.length ? 'Opdatér vurdering' : 'Ny vurdering'}</Button>}
        </Box>
        {!draft && approved.length === 0 && (
          <Typography variant="body2" color="text.secondary">Der er ingen vurdering endnu.</Typography>
        )}
        {draft && (
          <>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>{checklist.source}</Typography>
            {checklist.questions.map((q, i) => {
              const a = draft.answers[q.id] || { answer: '', note: '' };
              const flag = q.risk_if && a.answer === q.risk_if;
              return (
                <Box key={q.id} sx={{ py: 1, borderTop: i ? 1 : 0, borderColor: 'divider' }}>
                  <Typography variant="body2">{i + 1}. {q.text} <Typography component="span" variant="caption" color="text.secondary">({q.ref})</Typography></Typography>
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                    <RadioGroup row value={a.answer} onChange={(e) => setAnswer(q.id, { answer: e.target.value })}>
                      <FormControlLabel value="ja" control={<Radio size="small" />} label="Ja" />
                      <FormControlLabel value="nej" control={<Radio size="small" />} label="Nej" />
                      <FormControlLabel value="ikke_relevant" control={<Radio size="small" />} label="Ikke relevant" />
                    </RadioGroup>
                    <TextField size="small" placeholder="Bemærkning" value={a.note} sx={{ flex: 1, minWidth: 200 }}
                      onChange={(e) => setAnswer(q.id, { note: e.target.value })} />
                  </Box>
                  {flag && <Alert severity="warning" sx={{ py: 0 }}>Dette svar øger risikoen – beskriv håndteringen i begrundelsen.</Alert>}
                </Box>
              );
            })}
            <Grid container spacing={2} sx={{ mt: 0.5 }}>
              <Grid item xs={12}>
                <TextField fullWidth multiline minRows={2} size="small" label="Forretningsforbindelsens formål og tilsigtede beskaffenhed"
                  value={draft.purpose} onChange={(e) => setDraft({ ...draft, purpose: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth multiline minRows={2} size="small"
                  label={`Midlernes og formuens oprindelse${hasPep ? ' (krævet ved PEP)' : ''}`} required={hasPep}
                  value={draft.source_of_funds} onChange={(e) => setDraft({ ...draft, source_of_funds: e.target.value })} />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField select fullWidth size="small" label="Samlet risiko" value={draft.risk_level}
                  onChange={(e) => setDraft({ ...draft, risk_level: e.target.value })}>
                  {RISK_LEVELS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField fullWidth size="small" type="date" label="Næste opdatering" InputLabelProps={{ shrink: true }}
                  helperText="Tom = beregnes ud fra husets politik" value={draft.next_review_on || ''}
                  onChange={(e) => setDraft({ ...draft, next_review_on: e.target.value || null })} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth multiline minRows={3} size="small" label="Begrundelse for risikovurderingen"
                  value={draft.reasons} onChange={(e) => setDraft({ ...draft, reasons: e.target.value })} />
              </Grid>
            </Grid>
            <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end', alignItems: 'center' }}>
              {!data.can_approve && <Typography variant="caption" color="text.secondary">En partner skal godkende vurderingen.</Typography>}
              <Button variant="outlined" onClick={() => saveDraft()}>Gem kladde</Button>
              {data.can_approve && <Button variant="contained" onClick={approve}>Godkend og lås</Button>}
            </Box>
          </>
        )}
      </Paper>

      {approved.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Godkendte vurderinger</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Version</TableCell><TableCell>Risiko</TableCell><TableCell>Godkendt</TableCell>
                <TableCell>Næste opdatering</TableCell><TableCell>Kontrolsum (SHA-256)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {approved.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{a.version}</TableCell>
                  <TableCell><Chip size="small" color={RISK_COLOR[a.risk_level]} label={a.risk_label} /></TableCell>
                  <TableCell>{formatDate(a.approved_at)} · {a.approved_by}</TableCell>
                  <TableCell>{a.next_review_on ? formatDate(a.next_review_on) : '–'}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: 11 }}>{a.sha256.slice(0, 16)}…</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <Typography variant="caption" color="text.secondary">
            Oplysningerne opbevares i mindst 5 år efter forretningsforbindelsens ophør (HVL § 30, stk. 2) og vises aldrig for kunden.
          </Typography>
        </Paper>
      )}

      <Dialog open={!!personDlg} onClose={() => setPersonDlg(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{personDlg?.id ? 'Ret person' : 'Tilføj person'}</DialogTitle>
        {pf && (
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 0 }}>
              <Grid item xs={12} sm={6}>
                <TextField select fullWidth size="small" label="Rolle" value={pf.role} onChange={(e) => setPf({ role: e.target.value })}>
                  {ROLES.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}><TextField fullWidth size="small" label="Navn" value={pf.name} onChange={(e) => setPf({ name: e.target.value })} /></Grid>
              <Grid item xs={12} sm={6}>
                <TextField fullWidth size="small" type="date" label="Fødselsdato" InputLabelProps={{ shrink: true }}
                  value={pf.birth_date} onChange={(e) => setPf({ birth_date: e.target.value })} helperText="Der gemmes ikke CPR-nummer" />
              </Grid>
              <Grid item xs={12} sm={6}><TextField fullWidth size="small" label="Bopælsland" value={pf.country} onChange={(e) => setPf({ country: e.target.value })} /></Grid>
              <Grid item xs={12}>
                <TextField fullWidth size="small" label="Ejerskab / kontrol" placeholder="Fx 60 % af kapital og stemmer"
                  value={pf.ownership} onChange={(e) => setPf({ ownership: e.target.value })} />
              </Grid>
              <Grid item xs={12} sm={7}>
                <TextField fullWidth size="small" label="Sådan er identiteten kontrolleret" placeholder="Fx pas forevist ved møde"
                  value={pf.id_method} onChange={(e) => setPf({ id_method: e.target.value })} />
              </Grid>
              <Grid item xs={12} sm={5}>
                <TextField fullWidth size="small" type="date" label="Kontrolleret den" InputLabelProps={{ shrink: true }}
                  value={pf.verified_on} onChange={(e) => setPf({ verified_on: e.target.value })} />
              </Grid>
              <Grid item xs={12}>
                <Button component="label" size="small" variant="outlined">
                  {personDlg?.file ? personDlg.file.name : 'Vedhæft kopi af legitimation'}
                  <input hidden type="file" accept="image/*,application/pdf"
                    onChange={(e) => personDlg && setPersonDlg({ ...personDlg, file: e.target.files?.[0] || null })} />
                </Button>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel control={<Checkbox checked={pf.is_pep} onChange={(e) => setPf({ is_pep: e.target.checked })} />}
                  label="Politisk eksponeret person (PEP), nærtstående eller nær samarbejdspartner" />
                {pf.is_pep && (
                  <TextField fullWidth size="small" multiline label="PEP – hvilken funktion / relation" value={pf.pep_note}
                    onChange={(e) => setPf({ pep_note: e.target.value })} />
                )}
              </Grid>
            </Grid>
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setPersonDlg(null)}>Annullér</Button>
          <Button variant="contained" onClick={savePerson} disabled={!pf?.name.trim()}>Gem</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default KycPanel;
