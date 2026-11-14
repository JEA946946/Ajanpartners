import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { firmApi } from '../services/api';
import { useClient } from '../hooks/useClient';
import { Package, Staff } from './api';

export interface FirmSettings {
  name: string;
  cvr: string;
  email: string;
  phone: string;
  logo: string;
  primary_color: string;
}

interface AdminContextType {
  firm: FirmSettings | null;
  role: string;
  isPartner: boolean;
  staff: Staff[];
  packages: Package[];
  features: Record<string, string>;
  reload: () => Promise<void>;
  setFirm: (f: FirmSettings) => void;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export const useAdmin = () => {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error('useAdmin skal bruges inde i AdminProvider');
  return ctx;
};

export const AdminProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { firmStaff } = useClient();
  const [firm, setFirm] = useState<FirmSettings | null>(null);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [features, setFeatures] = useState<Record<string, string>>({});

  const reload = useCallback(async () => {
    const [s, st, p] = await Promise.allSettled([
      firmApi.get('/settings'), firmApi.get('/staff'), firmApi.get('/packages'),
    ]);
    if (s.status === 'fulfilled') setFirm(s.value.data.data.firm);
    if (st.status === 'fulfilled') setStaff(st.value.data.data.staff);
    if (p.status === 'fulfilled') {
      setPackages(p.value.data.data.packages);
      setFeatures(p.value.data.data.features);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const role = firmStaff?.role || '';
  return (
    <AdminContext.Provider value={{
      firm, role, isPartner: role === 'partner', staff, packages, features, reload, setFirm,
    }}>
      {children}
    </AdminContext.Provider>
  );
};

/** Navn på en medarbejder ud fra bruger-id. */
export const staffName = (staff: Staff[], userId: number | null | undefined) => {
  const s = staff.find((x) => x.user_id === userId);
  return s ? (`${s.first_name} ${s.last_name}`.trim() || s.username) : '';
};
