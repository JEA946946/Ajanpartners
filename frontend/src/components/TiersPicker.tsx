import React, { useEffect, useState } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

export interface TiersOption {
  id: string;
  name: string;
}

interface Props {
  kind: 'customer' | 'supplier';
  value: TiersOption | null;
  onChange: (v: TiersOption | null) => void;
}

// Debitor eller kreditor på en linje på debitor-, forudbetalings- eller kreditorkontoen.
const TiersPicker: React.FC<Props> = ({ kind, value, onChange }) => {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState<TiersOption[]>([]);

  useEffect(() => {
    const path = kind === 'customer' ? '/customers' : '/suppliers';
    const key = kind === 'customer' ? 'customers' : 'suppliers';
    const timer = setTimeout(() => {
      api.get(`${path}?is_active=true&search=${encodeURIComponent(search)}`).then(res => {
        if (res.data.success) {
          // customers come at the top level, suppliers under data
          setOptions(((res.data.data || res.data)[key] || []).slice(0, 50).map((x: { id: string; name: string }) => ({ id: x.id, name: x.name })));
        }
      });
    }, 250);
    return () => clearTimeout(timer);
  }, [kind, search]);

  return (
    <Autocomplete
      size="small"
      options={options}
      value={value}
      getOptionLabel={o => o.name}
      isOptionEqualToValue={(a, b) => a.id === b.id}
      filterOptions={x => x}
      onInputChange={(_, v, reason) => reason === 'input' && setSearch(v)}
      onChange={(_, v) => onChange(v)}
      renderInput={params => (
        <TextField {...params} placeholder={kind === 'customer' ? t('lettrage.customer') : t('lettrage.supplier')} />
      )}
    />
  );
};

export default TiersPicker;
