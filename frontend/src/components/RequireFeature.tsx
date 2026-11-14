import React from 'react';
import { Alert, Box, Typography } from '@mui/material';
import { useClient } from '../hooks/useClient';

/** Viser siden, hvis funktionen indgår i kundens pakke (revisorhuset har alt). */
const RequireFeature: React.FC<{ feature?: string; children: React.ReactNode }> = ({ feature, children }) => {
  const { hasFeature, current, firm } = useClient();
  if (hasFeature(feature)) return <>{children}</>;
  return (
    <Box sx={{ maxWidth: 560, mx: 'auto', mt: 6 }}>
      <Alert severity="info">
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Funktionen indgår ikke i jeres pakke ({current?.package.name})
        </Typography>
        <Typography variant="body2">
          Kontakt {firm?.name || 'Ajan Partners'}{firm?.email ? ` på ${firm.email}` : ''}, hvis I vil have den med.
          Pakkerne er gratis og følger jeres aftale med os.
        </Typography>
      </Alert>
    </Box>
  );
};

export default RequireFeature;
