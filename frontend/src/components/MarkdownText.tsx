import React from 'react';
import { Box, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';

/** Lille markdown-visning til betingelser: overskrifter, afsnit, punkter, tabeller, citat og **fed**. */
const inline = (text: string, key: string | number) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <React.Fragment key={key}>
      {parts.map((p, i) => (p.startsWith('**') && p.endsWith('**') ? <b key={i}>{p.slice(2, -2)}</b> : p))}
    </React.Fragment>
  );
};

const MarkdownText: React.FC<{ text: string }> = ({ text }) => {
  const lines = text.split('\n');
  const out: React.ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith('|')) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].startsWith('|')) {
        const cells = lines[i].split('|').slice(1, -1).map((c) => c.trim());
        if (!cells.every((c) => /^-+$/.test(c))) rows.push(cells);
        i += 1;
      }
      const [head, ...body] = rows;
      out.push(
        <Table key={`t${i}`} size="small" sx={{ my: 1 }}>
          <TableHead><TableRow>{head.map((c, k) => <TableCell key={k}><b>{c}</b></TableCell>)}</TableRow></TableHead>
          <TableBody>{body.map((r, k) => <TableRow key={k}>{r.map((c, m) => <TableCell key={m}>{inline(c, m)}</TableCell>)}</TableRow>)}</TableBody>
        </Table>,
      );
      continue;
    }
    if (line.startsWith('- ')) {
      const items: string[] = [];
      while (i < lines.length && lines[i].startsWith('- ')) { items.push(lines[i].slice(2)); i += 1; }
      out.push(<Box component="ul" key={`u${i}`} sx={{ my: 0.5, pl: 3 }}>{items.map((t, k) => <li key={k}><Typography variant="body2">{inline(t, k)}</Typography></li>)}</Box>);
      continue;
    }
    if (line.startsWith('# ')) out.push(<Typography key={i} variant="h6" sx={{ mt: 1 }}>{line.slice(2)}</Typography>);
    else if (line.startsWith('## ')) out.push(<Typography key={i} variant="subtitle1" sx={{ fontWeight: 600, mt: 1.5 }}>{line.slice(3)}</Typography>);
    else if (line.startsWith('> ')) out.push(<Box key={i} sx={{ borderLeft: 3, borderColor: 'warning.main', pl: 1.5, my: 1 }}><Typography variant="body2">{inline(line.slice(2), i)}</Typography></Box>);
    else if (line.trim()) out.push(<Typography key={i} variant="body2" sx={{ my: 0.5 }}>{inline(line, i)}</Typography>);
    i += 1;
  }
  return <Box>{out}</Box>;
};

export default MarkdownText;
