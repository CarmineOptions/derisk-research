import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

export const Route = createRootRoute({
  component: () => (
    <>
      <div className='hidden'>
        <Link to="/" className="[&.active]:font-bold">
          Dashboard
        </Link>{' '}
        <Link to="/subscribe" className="[&.active]:font-bold">
          Subscribe
        </Link>
      </div>
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
})