import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import api, { CLIENT_KEY, getClientSlug } from '../services/api';
import { useAuth } from './useAuth';

/** En kunde, brugeren kan åbne (fra /api/v1/me). */
export interface ClientSummary {
  id: number;
  slug: string;
  name: string;
  cvr: string;
  status: 'onboarding' | 'active' | 'archived';
  package: string;
  package_name: string;
  role: 'admin' | 'accountant' | 'viewer';
  via: 'member' | 'firm';
}

/** Betingelser, brugeren mangler at acceptere for en virksomhed (fra /me). */
export interface TermsRequired {
  client: string;
  client_name: string;
  role: string;
  documents: { id: number; kind: string; kind_label: string; version: string; title: string; sha256: string }[];
}

export interface Firm {
  name: string;
  cvr: string;
  email: string;
  phone: string;
  logo: string;
  primary_color: string;
}

/** Den valgte kunde (fra /api/v1/me/clients/<slug>). */
export interface ClientDetail {
  client: ClientSummary & {
    vat_period: string;
    legal_form: string;
    fiscal_year_start_month: number;
    accounting_class: string;
  };
  package: { code: string; name: string; description: string; features: string[]; limits: Record<string, number | null> };
  /** Funktioner brugeren må bruge. Revisorhuset har alle; kundens brugere har pakkens. */
  features: string[];
  package_features: string[];
  limits: Record<string, number | null>;
  access: { role: string; via: 'member' | 'firm'; can_write: boolean; grant_scope: string | null };
}

interface ClientContextType {
  loading: boolean;
  firm: Firm | null;
  firmStaff: { role: string; title: string } | null;
  mfa: { enabled: boolean; required: boolean };
  clients: ClientSummary[];
  termsRequired: TermsRequired[];
  current: ClientDetail | null;
  slug: string;
  selectClient: (slug: string) => void;
  clearClient: () => void;
  refresh: () => Promise<void>;
  hasFeature: (feature?: string) => boolean;
  canWrite: boolean;
}

const ClientContext = createContext<ClientContextType | undefined>(undefined);

export const useClient = () => {
  const ctx = useContext(ClientContext);
  if (!ctx) throw new Error('useClient must be used within a ClientProvider');
  return ctx;
};

/** Kort form til komponenter, der kun skal vide om en funktion er med i pakken. */
export const useFeature = (feature?: string) => useClient().hasFeature(feature);

export const ClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [firm, setFirm] = useState<Firm | null>(null);
  const [firmStaff, setFirmStaff] = useState<{ role: string; title: string } | null>(null);
  const [mfa, setMfa] = useState<{ enabled: boolean; required: boolean }>({ enabled: false, required: false });
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [termsRequired, setTermsRequired] = useState<TermsRequired[]>([]);
  const [current, setCurrent] = useState<ClientDetail | null>(null);
  const [slug, setSlug] = useState<string>(getClientSlug());

  // Hvilken login-tilstand data er hentet for. Uden den når siderne at se "logget ind,
  // men ingen kunde" i ét render, før /me er hentet – og sender brugeren tilbage til kundevalget.
  const [loadedFor, setLoadedFor] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      setLoadedFor(false);
      return;
    }
    setLoading(true);
    try {
      const me = await api.get('/me');
      const d = me.data.data;
      setFirm(d.firm);
      setFirmStaff(d.firm_staff);
      setMfa(d.mfa || { enabled: false, required: false });
      setClients(d.clients);
      setTermsRequired(d.terms_required || []);
      let chosen = getClientSlug();
      if (chosen && !d.clients.some((c: ClientSummary) => c.slug === chosen)) chosen = '';
      if (!chosen && d.clients.length === 1 && !d.firm_staff) chosen = d.clients[0].slug;
      if (chosen) {
        localStorage.setItem(CLIENT_KEY, chosen);
        const detail = await api.get(`/me/clients/${chosen}`);
        setCurrent(detail.data.data);
      } else {
        localStorage.removeItem(CLIENT_KEY);
        setCurrent(null);
      }
      setSlug(chosen);
    } catch {
      setCurrent(null);
    } finally {
      setLoading(false);
      setLoadedFor(true);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    load();
  }, [load]);

  const selectClient = (next: string) => {
    localStorage.setItem(CLIENT_KEY, next);
    // Fuld genindlæsning: ingen data fra den forrige kunde må hænge ved i sidernes state.
    window.location.href = '/dashboard';
  };

  const clearClient = () => {
    localStorage.removeItem(CLIENT_KEY);
    setSlug('');
    setCurrent(null);
  };

  const hasFeature = (feature?: string) => !feature || !!current?.features.includes(feature);

  return (
    <ClientContext.Provider value={{
      loading: loading || loadedFor !== isAuthenticated, firm, firmStaff, mfa, clients, termsRequired, current, slug,
      selectClient, clearClient, refresh: load, hasFeature,
      canWrite: !!current?.access.can_write,
    }}>
      {children}
    </ClientContext.Provider>
  );
};
