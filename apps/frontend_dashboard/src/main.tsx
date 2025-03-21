import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider, router } from './router';
import './index.css';
import { TanStackRouterDevtools } from '@tanstack/router-devtools';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
    <TanStackRouterDevtools router={router} />
  </StrictMode>,
);
