import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Accordion, AccordionDetails, AccordionSummary, Autocomplete, Box, Button, CircularProgress, Dialog,
  DialogContent, DialogTitle, IconButton, InputAdornment, List, ListItemButton, ListItemText, TextField,
  Tooltip, Typography,
} from '@mui/material';
import { ExpandMore, ListAlt, Close } from '@mui/icons-material';
import { firmApi } from '../../services/api';

/** En branchekode fra Dansk Branchekode DB25 (Danmarks Statistik). */
interface Industry {
  code: string;     // 692000 (som i CVR)
  display: string;  // 69.20.00
  title: string;
  section?: string;
  hint?: string;
}

interface Tree {
  version: string;
  sections: { display: string; title: string; groups: { display: string; title: string; codes: Industry[] }[] }[];
}

let treeCache: Tree | null = null;

const fmt = (code: string) => (/^\d{6}$/.test(code) ? `${code.slice(0, 2)}.${code.slice(2, 4)}.${code.slice(4)}` : code);

interface Props {
  value: string;
  onChange: (code: string) => void;
  disabled?: boolean;
  label?: string;
}

/**
 * Branchekode med søgning: skriv kode eller ord (fx "frisør", "tømrer", "69.20"),
 * eller åbn oversigten over alle koder. Gemmer koden med 6 cifre som i CVR.
 */
const IndustryCodeField: React.FC<Props> = ({ value, onChange, disabled, label = 'Branchekode (DB25)' }) => {
  const [input, setInput] = useState('');
  const [options, setOptions] = useState<Industry[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Industry | null>(null);
  const [converted, setConverted] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const timer = useRef<number>();

  // Slå den gemte kode op, så titlen vises.
  useEffect(() => {
    if (!value) { setSelected(null); return; }
    if (selected?.code === value) return;
    firmApi.get('/industry-codes', { params: { code: value } })
      .then((r) => {
        const c = r.data.data.code;
        setSelected({ code: c.code, display: c.display, title: c.title });
        setConverted(c.converted_from_db07);
        if (c.code !== value) onChange(c.code);
      })
      .catch(() => setSelected({ code: value, display: fmt(value), title: 'Ukendt kode' }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  useEffect(() => {
    window.clearTimeout(timer.current);
    const q = input.trim();
    if (q.length < 2 || (selected && input === `${selected.display} ${selected.title}`)) {
      setOptions([]);
      return;
    }
    timer.current = window.setTimeout(() => {
      setLoading(true);
      firmApi.get('/industry-codes', { params: { q } })
        .then((r) => setOptions(r.data.data.results))
        .catch(() => setOptions([]))
        .finally(() => setLoading(false));
    }, 200);
    return () => window.clearTimeout(timer.current);
  }, [input, selected]);

  const choose = (item: Industry | null) => {
    setSelected(item);
    setConverted(null);
    onChange(item ? item.code : '');
  };

  return (
    <>
      <Autocomplete<Industry>
        size="small"
        disabled={disabled}
        value={selected}
        options={options}
        filterOptions={(x) => x}
        loading={loading}
        isOptionEqualToValue={(a, b) => a.code === b.code}
        getOptionLabel={(o) => `${o.display} ${o.title}`}
        onChange={(_, v) => choose(v)}
        onInputChange={(_, v) => setInput(v)}
        noOptionsText={input.trim().length < 2 ? 'Skriv kode eller fx "frisør", "tømrer", "rådgivning"' : 'Ingen koder fundet'}
        renderOption={(props, o) => (
          <li {...props} key={o.code}>
            <Box>
              <Typography variant="body2"><b>{o.display}</b> {o.title}</Typography>
              {o.hint && <Typography variant="caption" color="text.secondary">{o.hint}</Typography>}
            </Box>
          </li>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            label={label}
            helperText={converted ? `Omregnet fra den gamle DB07-kode ${fmt(converted)}` : undefined}
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <>
                  {loading && <CircularProgress size={16} />}
                  {params.InputProps.endAdornment}
                  <InputAdornment position="end">
                    <Tooltip title="Oversigt over alle branchekoder">
                      <span>
                        <IconButton size="small" disabled={disabled} onClick={() => setOpen(true)} edge="end">
                          <ListAlt fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </InputAdornment>
                </>
              ),
            }}
          />
        )}
      />
      <IndustryCodeBrowser open={open} onClose={() => setOpen(false)} onPick={(i) => { choose(i); setOpen(false); }}
        current={value} />
    </>
  );
};

/** Oversigt over alle branchekoder, grupperet efter hovedafdeling og hovedgruppe, med filter. */
const IndustryCodeBrowser: React.FC<{
  open: boolean; onClose: () => void; onPick: (i: Industry) => void; current?: string;
}> = ({ open, onClose, onPick, current }) => {
  const [tree, setTree] = useState<Tree | null>(treeCache);
  const [filter, setFilter] = useState('');
  const [expanded, setExpanded] = useState<string | false>(false);

  useEffect(() => {
    if (!open || tree) return;
    firmApi.get('/industry-codes').then((r) => { treeCache = r.data.data; setTree(treeCache); });
  }, [open, tree]);

  const filtered = useMemo(() => {
    if (!tree) return [];
    const f = filter.trim().toLowerCase();
    if (!f) return tree.sections;
    const digits = f.replace(/[\s.]/g, '');
    return tree.sections
      .map((s) => ({
        ...s,
        groups: s.groups
          .map((g) => ({
            ...g,
            codes: g.codes.filter((c) => (/^\d+$/.test(digits) ? c.code.startsWith(digits)
              : c.title.toLowerCase().includes(f) || g.title.toLowerCase().includes(f))),
          }))
          .filter((g) => g.codes.length),
      }))
      .filter((s) => s.groups.length);
  }, [tree, filter]);

  const showAll = filter.trim().length > 0;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth scroll="paper">
      <DialogTitle sx={{ pr: 6 }}>
        Branchekoder
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          Dansk Branchekode {tree?.version || 'DB25'} fra Danmarks Statistik – den CVR bruger fra 2025
        </Typography>
        <IconButton onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8 }}><Close /></IconButton>
      </DialogTitle>
      <Box sx={{ px: 3, pb: 1 }}>
        <TextField fullWidth size="small" autoFocus placeholder="Filtrér på kode eller titel …" value={filter}
          onChange={(e) => setFilter(e.target.value)} />
      </Box>
      <DialogContent dividers sx={{ p: 0 }}>
        {!tree && <Box sx={{ p: 3, textAlign: 'center' }}><CircularProgress /></Box>}
        {filtered.map((s) => (
          <Accordion key={s.display} disableGutters square elevation={0}
            expanded={showAll || expanded === s.display}
            onChange={(_, isOpen) => setExpanded(isOpen ? s.display : false)}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography sx={{ fontWeight: 600 }}>{s.display}</Typography>
              <Typography sx={{ ml: 1.5 }}>{s.title}</Typography>
              <Typography color="text.secondary" sx={{ ml: 'auto', mr: 1 }}>
                {s.groups.reduce((n, g) => n + g.codes.length, 0)}
              </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ pt: 0 }}>
              {s.groups.map((g) => (
                <Box key={g.display} sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    {g.display} {g.title}
                  </Typography>
                  <List dense disablePadding>
                    {g.codes.map((c) => (
                      <ListItemButton key={c.code} selected={c.code === current} onClick={() => onPick(c)}
                        sx={{ py: 0.25 }}>
                        <ListItemText primary={<><b>{c.display}</b> {c.title}</>} />
                      </ListItemButton>
                    ))}
                  </List>
                </Box>
              ))}
            </AccordionDetails>
          </Accordion>
        ))}
        {tree && filtered.length === 0 && (
          <Typography sx={{ p: 3 }} color="text.secondary">Ingen koder matcher. Prøv søgningen i feltet i stedet –
            den søger også i beskrivelserne.</Typography>
        )}
      </DialogContent>
      <Box sx={{ p: 1.5, textAlign: 'right' }}><Button onClick={onClose}>Luk</Button></Box>
    </Dialog>
  );
};

export default IndustryCodeField;
