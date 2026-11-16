import React from 'react';
import { Box, Divider, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';

/** Lille markdown-visning (betingelser, skabeloner): overskrifter, afsnit, punkter, nummererede lister,
 *  afkrydsning, tabeller, citat, streg, **fed** og *kursiv*. Tomme flettefelter "[…]" fremhæves. */
const inline = (text: string, key: string | number) => {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|\[…\])/g);
  return (
    <React.Fragment key={key}>
      {parts.map((p, i) => {
        if (p.startsWith('**') && p.endsWith('**') && p.length > 4) return <b key={i}>{p.slice(2, -2)}</b>;
        if (p.startsWith('*') && p.endsWith('*') && p.length > 2) return <i key={i}>{p.slice(1, -1)}</i>;
        if (p === '[…]') {
          return <Box key={i} component="span" sx={{ bgcolor: 'warning.light', color: 'warning.contrastText', px: 0.5, borderRadius: 0.5 }}>[…]</Box>;
        }
        return p;
      })}
    </React.Fragment>
  );
};

const BULLET = /^(\s*)[-*] (?!\[[ xX]\] )/;
const CHECK = /^(\s*)- \[([ xX])\] /;
const NUMBER = /^(\s*)\d+[.)] /;

const MarkdownText: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split('\n');
  const out: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith('|')) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].startsWith('|')) {
        const cells = lines[i].trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
        if (!cells.every((c) => /^:?-+:?$/.test(c) || c === '')) rows.push(cells);
        i += 1;
      }
      const [head, ...body] = rows;
      if (head) {
        out.push(
          <Box key={`t${i}`} sx={{ overflowX: 'auto', my: 1 }}>
            <Table size="small">
              <TableHead><TableRow>{head.map((c, k) => <TableCell key={k} sx={{ bgcolor: 'action.hover' }}><b>{inline(c, k)}</b></TableCell>)}</TableRow></TableHead>
              <TableBody>{body.map((r, k) => <TableRow key={k}>{r.map((c, m) => <TableCell key={m}>{inline(c, m)}</TableCell>)}</TableRow>)}</TableBody>
            </Table>
          </Box>,
        );
      }
      continue;
    }
    if (CHECK.test(line)) {
      const items: [string, boolean, boolean][] = [];
      while (i < lines.length && CHECK.test(lines[i])) {
        const m = CHECK.exec(lines[i])!;
        items.push([lines[i].replace(CHECK, ''), m[2] !== ' ', m[1].length > 0]);
        i += 1;
      }
      out.push(
        <Box key={`c${i}`} sx={{ my: 0.5 }}>
          {items.map(([t, done, nested], k) => (
            <Typography key={k} variant="body2" sx={{ display: 'flex', gap: 1, pl: nested ? 3 : 0, py: 0.15 }}>
              <span>{done ? '☒' : '☐'}</span><span>{inline(t, k)}</span>
            </Typography>
          ))}
        </Box>,
      );
      continue;
    }
    if (BULLET.test(line) || NUMBER.test(line)) {
      const numbered = NUMBER.test(line);
      const re = numbered ? NUMBER : BULLET;
      const items: [string, boolean][] = [];
      while (i < lines.length && (re.test(lines[i]) || (lines[i].startsWith('  ') && BULLET.test(lines[i])))) {
        const nested = /^\s{2,}/.test(lines[i]);
        items.push([lines[i].replace(NUMBER, '').replace(BULLET, ''), nested]);
        i += 1;
      }
      out.push(
        <Box component={numbered ? 'ol' : 'ul'} key={`u${i}`} sx={{ my: 0.5, pl: 3 }}>
          {items.map(([t, nested], k) => (
            <li key={k} style={nested ? { marginLeft: 20, listStyleType: 'circle' } : undefined}>
              <Typography variant="body2">{inline(t, k)}</Typography>
            </li>
          ))}
        </Box>,
      );
      continue;
    }
    if (line.startsWith('# ')) out.push(<Typography key={i} variant="h6" sx={{ mt: 1 }}>{inline(line.slice(2), i)}</Typography>);
    else if (line.startsWith('## ')) out.push(<Typography key={i} variant="subtitle1" sx={{ fontWeight: 600, mt: 1.5 }}>{inline(line.slice(3), i)}</Typography>);
    else if (/^#{3,} /.test(line)) out.push(<Typography key={i} variant="subtitle2" sx={{ fontWeight: 600, mt: 1 }}>{inline(line.replace(/^#+ /, ''), i)}</Typography>);
    else if (line.startsWith('>')) out.push(<Box key={i} sx={{ borderLeft: 3, borderColor: 'warning.main', pl: 1.5, my: 1 }}><Typography variant="body2">{inline(line.replace(/^>\s?/, ''), i)}</Typography></Box>);
    else if (/^(-{3,}|_{3,}|\*{3,})$/.test(line.trim())) out.push(<Divider key={i} sx={{ my: 1.5 }} />);
    else if (line.trim()) out.push(<Typography key={i} variant="body2" sx={{ my: 0.5 }}>{inline(line, i)}</Typography>);
    i += 1;
  }
  return <Box>{out}</Box>;
};

export default MarkdownText;
