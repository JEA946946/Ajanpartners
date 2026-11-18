/** Typer og små hjælpere til admin-portalen (/api/firm). */
import { firmApi } from '../services/api';

export interface Deadline {
  date: string;
  due: string;
  shifted: boolean;
  kind: 'moms' | 'a_skat' | 'aarsrapport' | 'selvangivelse' | 'oplysningsskema' | 'acontoskat' | 'opdrag';
  engagement?: string;
  title: string;
  period: string;
  authority: string;
  note: string;
  client?: string;
  client_name?: string;
  cvr?: string;
  responsible_id?: number | null;
  responsible_name?: string | null;
}

export interface FirmClient {
  id: number;
  slug: string;
  name: string;
  cvr: string;
  legal_form: string;
  address: string;
  zip_code: string;
  city: string;
  industry_code: string;
  industry_title?: string;
  email: string;
  phone: string;
  vat_period: string;
  fiscal_year_start_month: number;
  accounting_class: string;
  chart_template: string;
  package: string;
  package_name: string;
  extra_features: string[];
  status: 'onboarding' | 'active' | 'archived';
  responsible_id: number | null;
  responsible_name: string | null;
  /** Adgang for den aktuelle medarbejder; 'ended' = aftalen ophørt; null = ikke tildelt kunden. */
  access: 'read' | 'bookkeeping' | 'full' | 'ended' | null;
  agreement_reference?: string;
  agreement_accepted_on?: string | null;
  retain_until: string | null;
  created_at: string;
  assigned_staff: number[];
  next_deadline: Deadline | null;
  open_tasks: number;
  answered_tasks: number;
}

export interface Grant {
  id: string;
  scope: string;
  staff_scope: string;
  staff: { id: number; name: string; role: string }[];
  valid_until: string | null;
  state: 'pending' | 'active' | 'revoked' | 'expired';
  request_note: string;
  requested_by: string | null;
  requested_at: string | null;
  accepted_at: string | null;
  revoked_at: string | null;
}

export interface Member {
  id: string;
  user_id: number;
  username: string;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface Package {
  id: number;
  code: string;
  name: string;
  description: string;
  order: number;
  features: string[];
  limits: Record<string, number | null>;
  is_active: boolean;
  client_count: number;
}

export interface Staff {
  id: number;
  user_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'partner' | 'revisor' | 'bogholder' | 'assistent';
  title: string;
  is_active: boolean;
  hourly_rate?: string | null;
  clients: string[];
}

export interface TaskMessage {
  id: string;
  author: string | null;
  from_firm: boolean;
  body: string;
  document_id: string | null;
  created_at: string;
}

export interface FirmTask {
  id: string;
  client: string;
  client_name: string;
  title: string;
  description: string;
  kind: 'bilag_mangler' | 'spoergsmaal' | 'opgave';
  kind_label: string;
  reference_type: '' | 'entry' | 'bank_line' | 'document';
  reference_id: string;
  reference_label: string;
  status: 'open' | 'answered' | 'in_progress' | 'closed';
  status_label: string;
  visible_to_client?: boolean;
  assigned_to: number | null;
  assigned_name: string | null;
  due_date: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  message_count?: number | null;
  messages?: TaskMessage[];
}

export const LEGAL_FORMS: [string, string][] = [
  ['aps', 'ApS'], ['as', 'A/S'], ['ivs', 'IVS'], ['enk', 'Enkeltmandsvirksomhed'], ['is', 'I/S'],
  ['pmv', 'Personligt ejet mindre virksomhed'], ['fmba', 'F.m.b.a.'], ['forening', 'Forening'],
  ['holding', 'Holding'], ['andet', 'Andet'],
];
export const VAT_PERIODS: [string, string][] = [
  ['none', 'Ikke momsregistreret'], ['month', 'Måned'], ['quarter', 'Kvartal'], ['half', 'Halvår'],
];
export const MONTHS = ['januar', 'februar', 'marts', 'april', 'maj', 'juni', 'juli', 'august',
  'september', 'oktober', 'november', 'december'];
export const ACCOUNTING_CLASSES: [string, string][] = [
  ['A', 'A – personlig virksomhed (ingen årsrapport)'], ['B', 'B – små virksomheder'],
  ['C', 'C – mellemstore/store'], ['D', 'D – børsnoterede/statslige'],
];
export const CHART_TEMPLATES: [string, string][] = [
  ['standard', 'Standard (driftsselskab)'], ['holding', 'Holdingselskab'], ['enkeltmand', 'Enkeltmandsvirksomhed'],
];
export const STAFF_ROLES: Record<string, string> = {
  partner: 'Partner', revisor: 'Revisor', bogholder: 'Bogholder', assistent: 'Assistent',
};
export const CLIENT_ROLES: Record<string, string> = { admin: 'Administrator', accountant: 'Bogholder', viewer: 'Læser' };
export const SCOPES: Record<string, string> = { read: 'Læse', bookkeeping: 'Bogføre', full: 'Fuld adgang' };
export const GRANT_STATES: Record<string, string> = {
  pending: 'Ikke aktiv', active: 'Aktiv', revoked: 'Afsluttet', expired: 'Udløbet',
};
export const CLIENT_STATUS: Record<string, string> = {
  onboarding: 'Under oprettelse', active: 'Aktiv', archived: 'Arkiveret',
};
export const DEADLINE_KINDS: Record<string, string> = {
  moms: 'Moms', a_skat: 'A-skat/AM', aarsrapport: 'Årsrapport', selvangivelse: 'Selvangivelse',
  oplysningsskema: 'Oplysningsskema', acontoskat: 'Acontoskat', opdrag: 'Opdrag (internt)',
};
export const TASK_KINDS: Record<string, string> = {
  bilag_mangler: 'Bilag mangler', spoergsmaal: 'Spørgsmål', opgave: 'Opgave',
};
export const TASK_STATUS: Record<string, string> = {
  open: 'Afventer kunden', answered: 'Kunden har svaret', in_progress: 'Under behandling', closed: 'Lukket',
};
export const REF_TYPES: Record<string, string> = {
  '': 'Ingen', entry: 'Postering', bank_line: 'Banklinje', document: 'Bilag',
};

export const label = (pairs: [string, string][], value: string) =>
  pairs.find(([k]) => k === value)?.[1] || value;

/** Fejltekst fra et axios-kald. */
export const errorText = (e: any, fallback = 'Noget gik galt') =>
  e?.response?.data?.message || e?.response?.data?.detail || fallback;

/** Adgangsstatus til visning: aktiv / afsluttet / ikke tildelt. */
export const accessState = (access: FirmClient['access']): 'active' | 'ended' | 'none' =>
  access === 'ended' ? 'ended' : access ? 'active' : 'none';

export const isoDate = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

export const formatAmount = (v: string | number) =>
  Number(v).toLocaleString('da-DK', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Hent en fil (CSV, bilag) fra /api/firm med login-tokenet og gem den. */
export async function downloadFile(url: string, fallbackName: string) {
  const res = await firmApi.get(url, { responseType: 'blob' });
  const cd: string = res.headers['content-disposition'] || '';
  const match = cd.match(/filename="?([^";]+)"?/);
  const href = URL.createObjectURL(res.data);
  const a = document.createElement('a');
  a.href = href;
  a.download = match?.[1] || fallbackName;
  a.click();
  URL.revokeObjectURL(href);
}
