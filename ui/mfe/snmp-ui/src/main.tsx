import React from 'react';
import { createRoot } from 'react-dom/client';
import SnmpModule from './SnmpModule';

const root = document.getElementById('root')!;
createRoot(root).render(<SnmpModule />);
