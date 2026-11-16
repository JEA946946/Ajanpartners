import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Card, CardContent, Chip, Stack, TextField,
  Typography,
} from '@mui/material';
import { ExpandMore } from '@mui/icons-material';
import { firmApi } from '../../services/api';
import { errorText } from '../api';

interface Group {
  group: string; label: string; level: 'høj' | 'forhøjet' | 'normal'; reasons: string[]; focus: string[];
  prefixes: string[]; clients: number;
}
interface ClientRow { slug: string; name: string; industry_code: string; groups: string[] }
interface Check { code: string; title: string; groups: string[]; level: string; reasons: string[]; focus: string[]; risikobranche: boolean }
interface Official { source: string; codes: { code: string; title: string }[]; clients: { slug: string; name: string; industry_code: string }[] }

const COLOR: Record<string, 'error' | 'warning' | 'success' | 'default'> = {
  høj: 'error', forhøjet: 'warning', normal: 'success', ukendt: 'default',
};
const LEVEL_TEXT: Record<string, string> = {
  høj: 'Høj', forhøjet: 'Forhøjet', normal: 'Normal', ukendt: 'Ingen branchekode',
};
const fmtPrefix = (p: string) => (p.length > 2 ? `${p.slice(0, 2)}.${p.slice(2)}` : p);

/** Admin → Brancherisiko: revisorhusets egen, begrundede vurdering af brancherisiko efter hvidvaskloven. */
const IndustryRisk: React.FC = () => {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [clients, setClients] = useState<Record<string, ClientRow[]>>({});
  const [official, setOfficial] = useState<Official | null>(null);
  const [error, setError] = useState('');
  const [code, setCode] = useState('');
  const [check, setCheck] = useState<Check | null>(null);
  const [checkError, setCheckError] = useState('');

  useEffect(() => {
    firmApi.get('/industry-risk').then((r) => {
      setGroups(r.data.data.groups);
      setClients(r.data.data.clients);
      setOfficial(r.data.data.official);
    }).catch((e) => setError(errorText(e, 'Vurderingen kunne ikke hentes')));
  }, []);

  const lookup = async () => {
    setCheck(null);
    setCheckError('');
    try {
      const r = await firmApi.get('/industry-risk', { params: { code } });
      setCheck(r.data.data);
    } catch (e) { setCheckError(errorText(e, 'Koden kunne ikke slås op')); }
  };

  const label = (g: string) => groups.find((x) => x.group === g)?.label || g;

  return (
    <Box sx={{ maxWidth: 1000 }}>
      <Typography variant="h5" sx={{ mb: 0.5 }}>Brancherisiko – hvidvask</Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Vores egen vurdering af, hvilke brancher der som udgangspunkt har højere risiko for hvidvask og
        terrorfinansiering, og hvorfor. Den bruges i skabelonerne til kundekendskab, risikovurdering og kundeaccept.
      </Typography>
      <Alert severity="warning" sx={{ mb: 2 }}>
        <b>Intern, indikativ vurdering – ikke en officiel klassificering.</b> Den er ikke listen over
        "klassificerede risikobrancher" efter årsregnskabslovens § 135, og den erstatter ikke den konkrete
        risikovurdering af hver kunde, som hvidvaskloven kræver. Kundens forhold (ejere, lande, betalingsformer,
        pengestrømme, ydelser) kan gøre risikoen både højere og lavere end brancheniveauet.
      </Alert>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Slå en branchekode op</Typography>
          <Stack direction="row" spacing={1}>
            <TextField size="small" placeholder="Fx 56.10.10" value={code} onChange={(e) => setCode(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') lookup(); }} />
            <Button variant="outlined" onClick={lookup} disabled={!code.trim()}>Vurdér</Button>
          </Stack>
          {checkError && <Alert severity="error" sx={{ mt: 1.5 }}>{checkError}</Alert>}
          {check && (
            <Box sx={{ mt: 1.5 }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Typography variant="body2"><b>{check.code}</b> {check.title}</Typography>
                <Chip size="small" color={COLOR[check.level]} label={`Risiko: ${LEVEL_TEXT[check.level]}`} />
                {check.groups.map((g) => <Chip key={g} size="small" variant="outlined" label={label(g)} />)}
                {check.risikobranche && <Chip size="small" color="error" variant="outlined" label="Officiel risikobranche (BEK 1488/2025)" />}
              </Box>
              <Box component="ul" sx={{ my: 1, pl: 3 }}>
                {check.reasons.map((r) => <li key={r}><Typography variant="body2">{r}</Typography></li>)}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {official && (
        <Card variant="outlined" sx={{ mb: 2, borderColor: 'error.light' }}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Officielle risikobrancher (årsregnskabslovens § 135, stk. 5)</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {official.source}. I kraft 1. januar 2026 med virkning for regnskabsår, der begynder 1. januar 2025 eller senere, og gælder i to regnskabsår (§§ 2–3). Afløser BEK nr. 32/2023. Hovedbranchekoden i CVR på
              balancedagen er afgørende. Klasse B-virksomheder i disse brancher med en nettoomsætning over 5 mio. kr.
              i to år i træk kan ikke fravælge revisorerklæring – de skal mindst have en opstillingserklæring.
              Listen er en del af lovgivningen og er adskilt fra vores egen vurdering nedenfor.
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
              {official.codes.map((c) => <Chip key={c.code} size="small" variant="outlined" label={`${c.code} ${c.title}`} />)}
            </Box>
            {official.clients.length > 0 && (
              <Box sx={{ mt: 1.5 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Vores kunder i en officiel risikobranche</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {official.clients.map((c) => (
                    <Chip key={c.slug} size="small" color="error" onClick={() => navigate(`/admin/clients/${c.slug}`)} label={c.name} />
                  ))}
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>Vores egen vurdering – brancher og begrundelser</Typography>
      {groups.map((g) => (
        <Accordion key={g.group} disableGutters variant="outlined" defaultExpanded={g.level === 'høj'}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap', width: '100%' }}>
              <Chip size="small" color={COLOR[g.level]} label={LEVEL_TEXT[g.level]} sx={{ minWidth: 76 }} />
              <Typography sx={{ fontWeight: 500, textTransform: 'capitalize' }}>{g.label}</Typography>
              <Typography variant="caption" color="text.secondary">DB25 {g.prefixes.map(fmtPrefix).join(', ')}</Typography>
              {g.clients > 0 && <Chip size="small" variant="outlined" label={`${g.clients} kunde${g.clients === 1 ? '' : 'r'}`} sx={{ ml: 'auto' }} />}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>Begrundelse</Typography>
            <Box component="ul" sx={{ mt: 0.5, pl: 3 }}>
              {g.reasons.map((r) => <li key={r}><Typography variant="body2">{r}</Typography></li>)}
            </Box>
            {g.focus.length > 0 && (
              <>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>Det ser vi særligt efter</Typography>
                <Box component="ul" sx={{ mt: 0.5, pl: 3, mb: 0 }}>
                  {g.focus.map((r) => <li key={r}><Typography variant="body2">{r}</Typography></li>)}
                </Box>
              </>
            )}
          </AccordionDetails>
        </Accordion>
      ))}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
        Kontantintensive virksomheder uden for grupperne ovenfor (fx kiosker, tankstationer, taxa) vurderes som
        forhøjet. Holdingselskaber vurderes ikke som finansielle virksomheder.
      </Typography>

      <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 3, mb: 1 }}>Vores kunder</Typography>
      <Stack spacing={1}>
        {(['høj', 'forhøjet', 'ukendt'] as const).map((lvl) => (clients[lvl] || []).length > 0 && (
          <Card key={lvl} variant="outlined">
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                <Chip size="small" color={COLOR[lvl]} label={LEVEL_TEXT[lvl]} />
                <Typography variant="body2" color="text.secondary">{clients[lvl].length} kunde(r)</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {clients[lvl].map((c) => (
                  <Chip key={c.slug} size="small" variant="outlined" onClick={() => navigate(`/admin/clients/${c.slug}`)}
                    label={`${c.name}${c.groups.length ? ` · ${c.groups.map(label).join(', ')}` : ''}`} />
                ))}
              </Box>
            </CardContent>
          </Card>
        ))}
        {(clients['normal'] || []).length > 0 && (
          <Typography variant="body2" color="text.secondary">{clients['normal'].length} kunde(r) med normal brancherisiko.</Typography>
        )}
      </Stack>
    </Box>
  );
};

export default IndustryRisk;
