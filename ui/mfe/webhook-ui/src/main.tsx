import React from 'react';
import { createRoot } from 'react-dom/client';
import WebhookModule from './WebhookModule';

const root = document.getElementById('root')!;
createRoot(root).render(<WebhookModule />);
