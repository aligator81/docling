'use client';

import { useEffect } from 'react';
import { suppressAntdWarning } from '@/lib/antd-patch';

export default function AntdPatchProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Apply Antd warning suppression after component mounts (client-side only)
    suppressAntdWarning();
  }, []);

  return <>{children}</>;
}