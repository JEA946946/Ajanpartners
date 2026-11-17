import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Autocomplete, Box, Button, Card, CardContent, Checkbox, Chip, Dialog, DialogActions, DialogContent,
  DialogTitle, FormControlLabel, MenuItem, Paper, Radio, RadioGroup, Table, TableBody, TableCell, TableHead, TableRow,
  TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText, STAFF_ROLES } from '../api';

interface Question { id: string; text: string; ref: string }
interface Answer { answer: string; note: string; clients: string[] }
interface Conflict {
  id: string; staff: string; staff_id: number; year: number; client: string; client_name: string; question_id: string;
  note: string; created_at: string; resolution: string; resolution_label: string; resolution_note: string;
  resolved_by: string | null; resolved_at: string | null; is_responsible: boolean;
}
interface Data {
  year: number; is_partner: boolean; clients: { slug: string; name: string }[];
  checklist: { title: string; source: string; intro: string; intro_ref: string; questions: Question[] };
  declaration: { signed_at: string | null; answers: Record<string, Answer>; sha256: string; conflicts: Conflict[] } | null;
  staff?: { id: number; name: string; role: string; signed_at: string | null }[];
  conflicts?: Conflict[];
}
const RESOLUTIONS: [string, string][] = [
  ['fjernet', 'Fjernet fra opgaven / udelukket fra beslutninger'],
  ['afhaendet', 'Økonomisk interesse afhændet / forhold ophørt'],
  ['sikkerhed', 'Sikkerhedsforanstaltninger truffet (kun øvrige trusler, § 7)'],
  ['afstaa', 'Huset afstår fra opgaven'],
];

/** Admin → Uafhængighed: årlig erklæring pr. medarbejder (BEK 520/2024) og partnerens afklaring af forhold. */
const Independence: React.FC = () => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState<Data | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [newConflict, setNewConflict] = useState<{ client: string; question_id: string; note: string } | null>(null);
  const [resolve, setResolve] = useState<{ c: Conflict; resolution: string; note: string } | null>(null);

  const load = useCallback(() => {
    firmApi.get('/independence', { params: { year } }).then((r) => {
      setData(r.data.data);
      setAnswers({});
      setConfirm(false);
    }).catch((e) => setError(errorText(e, 'Kunne ikke hentes')));
  }, [year]);
  useEffect(() => { load(); }, [load]);
  if (!data) return error ? <Alert severity="error">{error}</Alert> : null;

  const q = data.checklist.questions;
  const qText = (id: string) => q.find((x) => x.id === id)?.text.slice(0, 70) + '…';
  const set = (id: string, patch: Partial<Answer>) => setAnswers({
    ...answers, [id]: { ...{ answer: '', note: '', clients: [] }, ...answers[id], ...patch },
  });
  const sign = async () => {
    try {
      await firmApi.post('/independence/sign', { year, answers, confirm });
      setInfo('Erklæringen er underskrevet.');
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const addConflict = async () => {
    try { await firmApi.post('/independence/conflicts', { ...newConflict, year }); setNewConflict(null); load(); } catch (e) { setError(errorText(e)); }
  };
  const doResolve = async () => {
    if (!resolve) return;
    try {
      await firmApi.post(`/independence/conflicts/${resolve.c.id}/resolve`, { resolution: resolve.resolution, note: resolve.note });
      setResolve(null);
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const decl = data.declaration;
  const signed = !!decl?.signed_at;

  return (
    <Box sx={{ maxWidth: 1000 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
        <Typography variant="h5" sx={{ flex: 1 }}>Uafhængighed</Typography>
        <TextField select size="small" label="År" value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[0, 1, 2].map((i) => new Date().getFullYear() - i).map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
        </TextField>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Hver medarbejder erklærer én gang om året, om der foreligger forhold, der kan true uafhængigheden over for husets kunder.
        Et forhold fjerner straks medarbejderen fra kunden, indtil en partner har afklaret det.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setInfo('')}>{info}</Alert>}

      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>Min erklæring {year}</Typography>
          {signed
            ? <Chip size="small" color="success" label={`Underskrevet ${formatDate(decl!.signed_at)}`} />
            : <Chip size="small" color="warning" label="Ikke underskrevet" />}
          <Button size="small" variant="outlined" onClick={() => setNewConflict({ client: '', question_id: q[0].id, note: '' })}>Registrér nyt forhold</Button>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>{data.checklist.source}</Typography>
        {signed ? (
          <Typography variant="body2">
            {q.filter((x) => decl!.answers[x.id]?.answer === 'ja').length === 0
              ? 'Ingen forhold erklæret.'
              : `${q.filter((x) => decl!.answers[x.id]?.answer === 'ja').length} forhold erklæret – se listen nedenfor.`}
          </Typography>
        ) : (
          <>
            {q.map((x, i) => {
              const a = answers[x.id] || { answer: '', note: '', clients: [] };
              return (
                <Box key={x.id} sx={{ py: 1, borderTop: i ? 1 : 0, borderColor: 'divider' }}>
                  <Typography variant="body2">{i + 1}. {x.text} <Typography component="span" variant="caption" color="text.secondary">({x.ref})</Typography></Typography>
                  <RadioGroup row value={a.answer} onChange={(e) => set(x.id, { answer: e.target.value })}>
                    <FormControlLabel value="nej" control={<Radio size="small" />} label="Nej" />
                    <FormControlLabel value="ja" control={<Radio size="small" />} label="Ja" />
                  </RadioGroup>
                  {a.answer === 'ja' && (
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Autocomplete multiple size="small" sx={{ minWidth: 280, flex: 1 }} options={data.clients}
                        getOptionLabel={(o) => o.name} value={data.clients.filter((c) => a.clients.includes(c.slug))}
                        onChange={(_, v) => set(x.id, { clients: v.map((c) => c.slug) })}
                        renderInput={(p) => <TextField {...p} label="Kunde(r)" />} />
                      <TextField size="small" label="Beskriv forholdet" sx={{ flex: 1, minWidth: 240 }} value={a.note}
                        onChange={(e) => set(x.id, { note: e.target.value })} />
                    </Box>
                  )}
                </Box>
              );
            })}
            <FormControlLabel sx={{ mt: 1 }} control={<Checkbox checked={confirm} onChange={(e) => setConfirm(e.target.checked)} />}
              label={<Typography variant="body2">{data.checklist.intro} <Typography component="span" variant="caption" color="text.secondary">({data.checklist.intro_ref})</Typography></Typography>} />
            <Box sx={{ textAlign: 'right' }}>
              <Button variant="contained" disabled={!confirm} onClick={sign}>Underskriv erklæringen</Button>
            </Box>
          </>
        )}
      </Paper>

      {(decl?.conflicts.length || 0) > 0 && !data.is_partner && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Mine forhold</Typography>
          <ConflictTable rows={decl!.conflicts} qText={qText} />
        </Paper>
      )}

      {data.is_partner && data.staff && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Medarbejdernes erklæringer {year}</Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {data.staff.map((s) => (
                <Chip key={s.id} size="small" color={s.signed_at ? 'success' : 'warning'} variant={s.signed_at ? 'outlined' : 'filled'}
                  label={`${s.name} (${STAFF_ROLES[s.role] || s.role}) – ${s.signed_at ? formatDate(s.signed_at) : 'mangler'}`} />
              ))}
            </Box>
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Forhold</Typography>
            {(data.conflicts || []).length === 0
              ? <Typography variant="body2" color="text.secondary">Ingen forhold registreret.</Typography>
              : <ConflictTable rows={data.conflicts!} qText={qText} onResolve={(c) => setResolve({ c, resolution: 'fjernet', note: '' })} />}
          </CardContent>
        </Card>
      )}

      <Dialog open={!!newConflict} onClose={() => setNewConflict(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Registrér forhold</DialogTitle>
        {newConflict && (
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <TextField select size="small" label="Kunde" value={newConflict.client} onChange={(e) => setNewConflict({ ...newConflict, client: e.target.value })}>
              {data.clients.map((c) => <MenuItem key={c.slug} value={c.slug}>{c.name}</MenuItem>)}
            </TextField>
            <TextField select size="small" label="Forhold" value={newConflict.question_id} onChange={(e) => setNewConflict({ ...newConflict, question_id: e.target.value })}>
              {q.map((x) => <MenuItem key={x.id} value={x.id} sx={{ whiteSpace: 'normal' }}>{x.text.slice(0, 110)}…</MenuItem>)}
            </TextField>
            <TextField multiline minRows={2} size="small" label="Beskriv forholdet" value={newConflict.note} onChange={(e) => setNewConflict({ ...newConflict, note: e.target.value })} />
            <Alert severity="info">Du fjernes straks fra kunden, indtil en partner har afklaret forholdet.</Alert>
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setNewConflict(null)}>Annullér</Button>
          <Button variant="contained" disabled={!newConflict?.client || !newConflict?.note.trim()} onClick={addConflict}>Registrér</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={!!resolve} onClose={() => setResolve(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Afklar forhold</DialogTitle>
        {resolve && (
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '8px !important' }}>
            <Typography variant="body2"><b>{resolve.c.staff}</b> · {resolve.c.client_name}: {resolve.c.note}</Typography>
            {resolve.c.is_responsible && <Alert severity="warning">Medarbejderen er ansvarlig for kunden. Overvej at skifte ansvarlig.</Alert>}
            <TextField select size="small" label="Afklaring" value={resolve.resolution} onChange={(e) => setResolve({ ...resolve, resolution: e.target.value })}>
              {RESOLUTIONS.map(([k, v]) => <MenuItem key={k} value={k}>{v}</MenuItem>)}
            </TextField>
            <TextField multiline minRows={2} size="small" label="Begrundelse og evt. sikkerhedsforanstaltninger" value={resolve.note}
              onChange={(e) => setResolve({ ...resolve, note: e.target.value })} />
            <Typography variant="caption" color="text.secondary">
              Trusler efter BEK 520/2024 § 2 kan ikke afhjælpes med sikkerhedsforanstaltninger. Personen fjernes, interessen afhændes
              senest én måned efter kendskab (§ 4), eller huset afstår fra opgaven.
            </Typography>
          </DialogContent>
        )}
        <DialogActions>
          <Button onClick={() => setResolve(null)}>Annullér</Button>
          <Button variant="contained" disabled={!resolve?.note.trim()} onClick={doResolve}>Gem afklaring</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

const ConflictTable: React.FC<{ rows: Conflict[]; qText: (id: string) => string; onResolve?: (c: Conflict) => void }> = ({ rows, qText, onResolve }) => (
  <Table size="small">
    <TableHead>
      <TableRow><TableCell>Medarbejder</TableCell><TableCell>Kunde</TableCell><TableCell>Forhold</TableCell><TableCell>Afklaring</TableCell><TableCell /></TableRow>
    </TableHead>
    <TableBody>
      {rows.map((c) => (
        <TableRow key={c.id}>
          <TableCell>{c.staff}</TableCell>
          <TableCell>{c.client_name}</TableCell>
          <TableCell><Typography variant="body2">{c.note}</Typography><Typography variant="caption" color="text.secondary">{qText(c.question_id)}</Typography></TableCell>
          <TableCell>
            {c.resolution
              ? <><Chip size="small" color={c.resolution === 'fjernet' ? 'warning' : 'success'} label={c.resolution_label} />
                <Typography variant="caption" sx={{ display: 'block' }}>{c.resolved_by} {formatDate(c.resolved_at)}: {c.resolution_note}</Typography></>
              : <Chip size="small" color="error" label="Uafklaret" />}
          </TableCell>
          <TableCell align="right">{onResolve && !c.resolution && <Button size="small" onClick={() => onResolve(c)}>Afklar</Button>}</TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);

export default Independence;
