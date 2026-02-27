import React from 'react';
import { createRoot } from 'react-dom/client';
import FmConsoleModule from './FmConsoleModule';

// Standalone dev entrypoint — not used by Module Federation consumers
const root = document.getElementById('root')!;
createRoot(root).render(<FmConsoleModule />);
