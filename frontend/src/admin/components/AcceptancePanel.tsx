import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert, Box, Button, Chip, FormControlLabel, MenuItem, Paper, Radio, RadioGroup, Stack, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, Typography,
} from '@mui/material';
import { firmApi } from '../../services/api';
import { formatDate } from '../../utils/dateFormat';
import { errorText } from '../api';
import { KYC_STATUS } from './KycPanel';

interface Answer { answer: string; note: string }
interface Question { id: string; text: string; ref: string; block_if?: string; block_text?: string; note_if?: string; allow_na?: boolean }
interface Acceptance {
  id: string; kind: string; kind_label: string; engagement_text: string; answers: Record<string, Answer>;
  conclusion: string; status: string; status_label: string; created_by: string | null; created_at: string;
  approved_by: string | null; approved_at: string | null; sha256: string;
}
interface Data {
  status: string; acceptances: Acceptance[]; kyc_status: string; can_approve: boolean;
  checklist: { title: string; source: string; questions: Question[] };
  open_conflicts: { staff: string; question: string; note: string }[];
}

const STATUS: Record<string, { text: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
  approved: { text: 'Accepteret', color: 'success' },
  rejected: { text: 'Afvist', color: 'error' },
  draft: { text: 'Kladde – afventer partner', color: 'warning' },
  none: { text: 'Ingen accept registreret', color: 'error' },
};

/** Fanen "Kundeaccept": accept/fortsættelse af klientforhold og opgave (BEK 512/2024 § 3, stk. 1, nr. 4). */
const AcceptancePanel: React.FC<{ slug: string }> = ({ slug }) => {
  const [data, setData] = useState<Data | null>(null);
  const [draft, setDraft] = useState<Acceptance | null>(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const load = useCallback(() => {
    firmApi.get(`/clients/${slug}/acceptances`).then((r) => {
      const d: Data = r.data.data;
      setData(d);
      setDraft(d.acceptances.find((a) => a.status === 'kladde') || null);
    }).catch((e) => setError(errorText(e, 'Kundeaccept kunne ikke hentes')));
  }, [slug]);
  useEffect(() => { load(); }, [load]);
  if (!data) return error ? <Alert severity="error">{error}</Alert> : null;

  const create = async () => {
    try { await firmApi.post(`/clients/${slug}/acceptances`, {}); load(); } catch (e) { setError(errorText(e)); }
  };
  const save = async (quiet = false) => {
    if (!draft) return false;
    try {
      const r = await firmApi.put(`/acceptances/${draft.id}`, draft);
      setDraft(r.data.data.acceptance);
      if (!quiet) setInfo('Kladden er gemt.');
      return true;
    } catch (e) { setError(errorText(e)); return false; }
  };
  const decide = async (decision: 'godkendt' | 'afvist') => {
    if (!draft || !(await save(true))) return;
    try {
      await firmApi.post(`/acceptances/${draft.id}/approve`, { decision });
      setInfo(decision === 'godkendt' ? 'Kunden/opgaven er accepteret, og vurderingen er låst.' : 'Kunden/opgaven er afvist.');
      load();
    } catch (e) { setError(errorText(e)); }
  };
  const setAnswer = (id: string, patch: Partial<Answer>) => draft && setDraft({
    ...draft, answers: { ...draft.answers, [id]: { ...{ answer: '', note: '' }, ...draft.answers[id], ...patch } },
  });
  const decided = data.acceptances.filter((a) => a.status !== 'kladde');

  return (
    <Stack spacing={2}>
      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
      {info && <Alert severity="success" onClose={() => setInfo('')}>{info}</Alert>}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Accept og fortsættelse</Typography>
          <Chip size="small" color={STATUS[data.status].color} label={STATUS[data.status].text} />
          <Chip size="small" variant="outlined" color={KYC_STATUS[data.kyc_status].color} label={`Kundekendskab: ${KYC_STATUS[data.kyc_status].text}`} />
          <Box sx={{ flex: 1 }} />
          {!draft && <Button size="small" variant="contained" onClick={create}>{decided.length ? 'Ny vurdering (fortsættelse)' : 'Ny vurdering (accept)'}</Button>}
        </Box>
        {data.open_conflicts.length > 0 && (
          <Alert severity="warning" sx={{ mt: 1 }}>
            Uafklarede uafhængighedsforhold: {data.open_conflicts.map((c) => c.staff).join(', ')}. De afklares under Uafhængighed.
          </Alert>
        )}
      </Paper>

      {draft && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 2, mb: 1, flexWrap: 'wrap' }}>
            <TextField select size="small" label="Type" value={draft.kind} sx={{ minWidth: 220 }}
              onChange={(e) => setDraft({ ...draft, kind: e.target.value })}>
              <MenuItem value="accept">Accept af ny kunde/opgave</MenuItem>
              <MenuItem value="fortsaettelse">Fortsættelse</MenuItem>
            </TextField>
            <TextField size="small" label="Opgave" placeholder="Fx Opstilling af årsregnskab 2026" sx={{ flex: 1, minWidth: 240 }}
              value={draft.engagement_text} onChange={(e) => setDraft({ ...draft, engagement_text: e.target.value })} />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>{data.checklist.source}</Typography>
          {data.checklist.questions.map((q, i) => {
            const a = draft.answers[q.id] || { answer: '', note: '' };
            return (
              <Box key={q.id} sx={{ py: 1, borderTop: i ? 1 : 0, borderColor: 'divider' }}>
                <Typography variant="body2">{i + 1}. {q.text} <Typography component="span" variant="caption" color="text.secondary">({q.ref})</Typography></Typography>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                  <RadioGroup row value={a.answer} onChange={(e) => setAnswer(q.id, { answer: e.target.value })}>
                    <FormControlLabel value="ja" control={<Radio size="small" />} label="Ja" />
                    <FormControlLabel value="nej" control={<Radio size="small" />} label="Nej" />
                    {q.allow_na && <FormControlLabel value="ikke_relevant" control={<Radio size="small" />} label="Ikke relevant" />}
                  </RadioGroup>
                  <TextField size="small" placeholder={q.note_if && a.answer === q.note_if ? 'Trusler og sikkerhedsforanstaltninger (krævet)' : 'Bemærkning'}
                    value={a.note} sx={{ flex: 1, minWidth: 200 }} onChange={(e) => setAnswer(q.id, { note: e.target.value })} />
                </Box>
                {q.block_if && a.answer === q.block_if && <Alert severity="error" sx={{ py: 0 }}>{q.block_text}</Alert>}
              </Box>
            );
          })}
          <TextField fullWidth multiline minRows={2} size="small" sx={{ mt: 1 }} label="Konklusion"
            value={draft.conclusion} onChange={(e) => setDraft({ ...draft, conclusion: e.target.value })} />
          <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end', alignItems: 'center' }}>
            {!data.can_approve && <Typography variant="caption" color="text.secondary">En partner skal afgøre vurderingen.</Typography>}
            <Button variant="outlined" onClick={() => save()}>Gem kladde</Button>
            {data.can_approve && <Button color="error" onClick={() => decide('afvist')}>Afvis</Button>}
            {data.can_approve && <Button variant="contained" onClick={() => decide('godkendt')}>Acceptér og lås</Button>}
          </Box>
        </Paper>
      )}

      {decided.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Historik</Typography>
          <Table size="small">
            <TableHead><TableRow><TableCell>Type</TableCell><TableCell>Opgave</TableCell><TableCell>Afgørelse</TableCell><TableCell>Partner</TableCell><TableCell>Konklusion</TableCell></TableRow></TableHead>
            <TableBody>
              {decided.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{a.kind_label}</TableCell>
                  <TableCell>{a.engagement_text || '–'}</TableCell>
                  <TableCell><Chip size="small" color={a.status === 'godkendt' ? 'success' : 'error'} label={`${a.status_label} ${formatDate(a.approved_at)}`} /></TableCell>
                  <TableCell>{a.approved_by}</TableCell>
                  <TableCell sx={{ whiteSpace: 'pre-wrap' }}>{a.conclusion}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Stack>
  );
};

export default AcceptancePanel;
