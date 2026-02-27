import React from 'react';
import { createRoot } from 'react-dom/client';
import LogViewerModule from './LogViewerModule';

const root = document.getElementById('root')!;
createRoot(root).render(<LogViewerModule />);
