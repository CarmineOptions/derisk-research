import { createRootRoute, createRoute, createRouter, RouterProvider } from '@tanstack/react-router';
import { Outlet } from '@tanstack/react-router';
import Home from './pages/Home';
import About from './pages/About';
import Navbar from './components/Navbar';


const rootRoute = createRootRoute({
  component: () => 
    <>
      <Navbar /> 
      <Outlet />
    </>,
});


const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Home,
});

const aboutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/about',
  component: About,
});


const routeTree = rootRoute.addChildren([homeRoute, aboutRoute]);
const router = createRouter({ routeTree });

export { RouterProvider, router };
