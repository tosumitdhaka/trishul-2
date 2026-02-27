import React from 'react';
import { createRoot } from 'react-dom/client';
import PmDashboardModule from './PmDashboardModule';

const root = document.getElementById('root')!;
createRoot(root).render(<PmDashboardModule />);
