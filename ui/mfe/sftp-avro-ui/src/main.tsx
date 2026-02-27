import React from 'react';
import { createRoot } from 'react-dom/client';
import SftpModule from './SftpModule';

// Default standalone entrypoint shows SFTP;
// AvroModule is exposed separately via Module Federation
const root = document.getElementById('root')!;
createRoot(root).render(<SftpModule />);
