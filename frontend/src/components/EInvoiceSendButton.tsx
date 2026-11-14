import React, { useState } from 'react';
import {
  Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Snackbar, TextField, Tooltip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import api from '../services/api';
import { useFeature } from '../hooks/useClient';

interface Props {
  /** id på fakturaen (eller kreditnotaen) */
  documentId: string;
  documentType?: 'invoice' | 'credit_note';
  /** fakturaens status; kladder og annullerede kan ikke sendes */
  status?: string;
  size?: 'small' | 'medium';
  onSent?: (result: { id: string; status: string; access_point_id: string }) => void;
}

/**
 * Send en faktura eller kreditnota som e-faktura (Peppol BIS 3.0 / OIOUBL 2.1).
 * Vises kun, når kunden har funktionen einvoice_send. Modtageren findes ud fra
 * kundens EAN/GLN-nummer eller CVR-nummer.
 */
const EInvoiceSendButton: React.FC<Props> = ({ documentId, documentType = 'invoice', status, size = 'small', onSent }) => {
  const allowed = useFeature('einvoice_send');
  const [open, setOpen] = useState(false);
  const [format, setFormat] = useState('peppol');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState('');
  const [alreadySent, setAlreadySent] = useState(false);

  if (!allowed) return null;
  const blocked = status === 'draft' || status === 'cancelled';

  const send = async (resend = false) => {
    setBusy(true); setError('');
    try {
      const r = await api.post(`/einvoice/send/${documentId}`, { document_type: documentType, format, resend });
      setDone(r.data.message || 'E-fakturaen er sendt.');
      setOpen(false); setAlreadySent(false);
      onSent?.(r.data.data);
    } catch (e: any) {
      if (e.response?.data?.code === 'already_sent') setAlreadySent(true);
      setError(e.response?.data?.message || 'E-fakturaen kunne ikke sendes');
    } finally { setBusy(false); }
  };

  return (
    <>
      <Tooltip title={blocked ? 'Udsted fakturaen, før den sendes som e-faktura' : 'Send som e-faktura (Peppol/NemHandel)'}>
        <span>
          <Button size={size} startIcon={<SendIcon />} disabled={blocked} onClick={() => { setError(''); setOpen(true); }}>
            E-faktura
          </Button>
        </span>
      </Tooltip>
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Send som e-faktura</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField select fullWidth size="small" label="Format" value={format} onChange={(e) => setFormat(e.target.value)} sx={{ mt: 1 }}>
            <MenuItem value="peppol">Peppol BIS Billing 3.0</MenuItem>
            <MenuItem value="oioubl">OIOUBL 2.1 (NemHandel)</MenuItem>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Annullér</Button>
          {alreadySent
            ? <Button variant="contained" disabled={busy} onClick={() => send(true)}>Send igen</Button>
            : <Button variant="contained" disabled={busy} onClick={() => send(false)}>Send</Button>}
        </DialogActions>
      </Dialog>
      <Snackbar open={!!done} autoHideDuration={4000} onClose={() => setDone('')} message={done} />
    </>
  );
};

export default EInvoiceSendButton;
