import React, { useRef, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Typography } from '@mui/material';
import { DocumentScanner as ScanIcon } from '@mui/icons-material';
import api from '../services/api';

/** Svar fra POST /bills/read-invoice. */
export interface ReadInvoiceResult {
  document_id: string;
  filename: string;
  read: boolean;
  message?: string;
  source?: 'xml' | 'pdf_embedded_xml' | 'pdf_text' | 'pdf_ocr' | 'image_ocr';
  confidence?: Record<string, 'high' | 'medium' | 'low'>;
  warnings?: string[];
  duplicate_of?: { bill_id: string; bill_number: string };
  proposal?: {
    supplier_id: string | null;
    new_supplier: { name: string; tax_id: string; address: string } | null;
    reference: string;
    date: string | null;
    due_date: string | null;
    currency: string;
    notes: string;
    lines: { description: string; quantity: string; unit_price: string; account_id: string; tax_code_id: string;
      amount: string }[];
    totals: { net: string; vat: string; total: string };
  };
}

const SOURCE: Record<string, string> = {
  xml: 'e-faktura (XML) – præcis aflæsning',
  pdf_embedded_xml: 'e-faktura indlejret i PDF\'en – præcis aflæsning',
  pdf_text: 'teksten i PDF\'en – tjek felterne',
  pdf_ocr: 'scanning (lokal OCR) – tjek felterne grundigt',
  image_ocr: 'billede (lokal OCR) – tjek felterne grundigt',
};
const FIELD: Record<string, string> = {
  supplier: 'Leverandør', number: 'Fakturanr.', issue_date: 'Fakturadato', due_date: 'Forfald',
  lines: 'Linjer', totals: 'Beløb',
};

/** Knap: vælg en PDF/XML-faktura, læs den på serveren (lokalt) og returnér forslaget. */
export const ReadInvoiceButton: React.FC<{ onRead: (r: ReadInvoiceResult) => void; disabled?: boolean }> = ({
  onRead, disabled,
}) => {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const upload = async (file: File) => {
    setBusy(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await api.post('/bills/read-invoice', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000,
      });
      onRead(r.data.data);
    } catch (e: any) {
      setError(e.response?.data?.message || 'Fakturaen kunne ikke uploades');
    } finally {
      setBusy(false);
      if (input.current) input.current.value = '';
    }
  };

  return (
    <>
      <input ref={input} type="file" hidden accept=".pdf,.xml,.png,.jpg,.jpeg,.tif,.tiff"
        onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
      <Button variant="outlined" size="small" disabled={disabled || busy} onClick={() => input.current?.click()}
        startIcon={busy ? <CircularProgress size={14} /> : <ScanIcon />}
        title="Upload en leverandørfaktura (PDF eller e-faktura-XML). Den læses på serveren – intet sendes videre.">
        {busy ? 'Læser faktura …' : 'Læs faktura (PDF/XML)'}
      </Button>
      {error && <Alert severity="error" sx={{ mt: 1 }} onClose={() => setError('')}>{error}</Alert>}
    </>
  );
};

/** Oplysning i regningsdialogen om, hvad der blev læst, og hvad der skal tjekkes. */
export const ReadInvoiceNotice: React.FC<{
  info: ReadInvoiceResult;
  onCreateSupplier?: () => void;
}> = ({ info, onCreateSupplier }) => {
  if (!info.read) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        {info.message} Bilaget <b>{info.filename}</b> er gemt og kobles på regningen, når du gemmer.
      </Alert>
    );
  }
  const low = Object.entries(info.confidence || {}).filter(([, v]) => v !== 'high').map(([k]) => FIELD[k] || k);
  const t = info.proposal?.totals;
  return (
    <Alert severity={low.length ? 'info' : 'success'} sx={{ mb: 2 }}>
      <Typography variant="body2">
        Udfyldt fra {SOURCE[info.source || ''] || info.source} (<b>{info.filename}</b>). Regningen gemmes som
        kladde, og bilaget kobles på.
      </Typography>
      {t && t.total && (
        <Typography variant="body2">Fakturaen: netto {t.net} · moms {t.vat} · i alt {t.total}</Typography>
      )}
      {low.length > 0 && (
        <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
          <Typography variant="body2">Tjek især:</Typography>
          {low.map((f) => <Chip key={f} size="small" color="warning" variant="outlined" label={f} />)}
        </Box>
      )}
      {(info.warnings || []).map((w) => <Typography key={w} variant="body2">• {w}</Typography>)}
      {info.duplicate_of && (
        <Typography variant="body2" color="error">
          Samme fil er allerede bogført som regning {info.duplicate_of.bill_number}.
        </Typography>
      )}
      {info.proposal?.new_supplier && onCreateSupplier && (
        <Box sx={{ mt: 1 }}>
          <Button size="small" variant="contained" onClick={onCreateSupplier}>
            Opret leverandør: {info.proposal.new_supplier.name || 'ukendt navn'}
            {info.proposal.new_supplier.tax_id ? ` (CVR ${info.proposal.new_supplier.tax_id})` : ''}
          </Button>
        </Box>
      )}
    </Alert>
  );
};
