/* eslint-disable */

// @ts-nocheck

// noinspection JSUnusedGlobalSymbols

// This file was automatically generated by TanStack Router.
// You should NOT make any changes in this file as it will be overwritten.
// Additionally, you should also exclude this file from your linter and/or formatter to prevent it from being checked or modified.

// Import Routes

import { Route as rootRoute } from './routes/__root'
import { Route as AboutImport } from './routes/about'
import { Route as DashboardImport } from './routes/Dashboard'
import { Route as IndexImport } from './routes/index'

// Create/Update Routes

const AboutRoute = AboutImport.update({
  id: '/about',
  path: '/about',
  getParentRoute: () => rootRoute,
} as any)

const DashboardRoute = DashboardImport.update({
  id: '/Dashboard',
  path: '/Dashboard',
  getParentRoute: () => rootRoute,
} as any)

const IndexRoute = IndexImport.update({
  id: '/',
  path: '/',
  getParentRoute: () => rootRoute,
} as any)

// Populate the FileRoutesByPath interface

declare module '@tanstack/react-router' {
  interface FileRoutesByPath {
    '/': {
      id: '/'
      path: '/'
      fullPath: '/'
      preLoaderRoute: typeof IndexImport
      parentRoute: typeof rootRoute
    }
    '/Dashboard': {
      id: '/Dashboard'
      path: '/Dashboard'
      fullPath: '/Dashboard'
      preLoaderRoute: typeof DashboardImport
      parentRoute: typeof rootRoute
    }
    '/about': {
      id: '/about'
      path: '/about'
      fullPath: '/about'
      preLoaderRoute: typeof AboutImport
      parentRoute: typeof rootRoute
    }
  }
}

// Create and export the route tree

export interface FileRoutesByFullPath {
  '/': typeof IndexRoute
  '/Dashboard': typeof DashboardRoute
  '/about': typeof AboutRoute
}

export interface FileRoutesByTo {
  '/': typeof IndexRoute
  '/Dashboard': typeof DashboardRoute
  '/about': typeof AboutRoute
}

export interface FileRoutesById {
  __root__: typeof rootRoute
  '/': typeof IndexRoute
  '/Dashboard': typeof DashboardRoute
  '/about': typeof AboutRoute
}

export interface FileRouteTypes {
  fileRoutesByFullPath: FileRoutesByFullPath
  fullPaths: '/' | '/Dashboard' | '/about'
  fileRoutesByTo: FileRoutesByTo
  to: '/' | '/Dashboard' | '/about'
  id: '__root__' | '/' | '/Dashboard' | '/about'
  fileRoutesById: FileRoutesById
}

export interface RootRouteChildren {
  IndexRoute: typeof IndexRoute
  DashboardRoute: typeof DashboardRoute
  AboutRoute: typeof AboutRoute
}

const rootRouteChildren: RootRouteChildren = {
  IndexRoute: IndexRoute,
  DashboardRoute: DashboardRoute,
  AboutRoute: AboutRoute,
}

export const routeTree = rootRoute
  ._addFileChildren(rootRouteChildren)
  ._addFileTypes<FileRouteTypes>()

/* ROUTE_MANIFEST_START
{
  "routes": {
    "__root__": {
      "filePath": "__root.tsx",
      "children": [
        "/",
        "/Dashboard",
        "/about"
      ]
    },
    "/": {
      "filePath": "index.tsx"
    },
    "/Dashboard": {
      "filePath": "Dashboard.jsx"
    },
    "/about": {
      "filePath": "about.tsx"
    }
  }
}
ROUTE_MANIFEST_END */
