import { AsyncRouteComponent } from './route.js';
import * as React from 'react';
export declare function ClientOnly({ children, fallback, }: React.PropsWithChildren<{
    fallback?: React.ReactNode;
}>): import("react/jsx-runtime").JSX.Element;
export declare function useHydrated(): boolean;
export declare function lazyRouteComponent<T extends Record<string, any>, TKey extends keyof T = 'default'>(importer: () => Promise<T>, exportName?: TKey, ssr?: () => boolean): T[TKey] extends (props: infer TProps) => any ? AsyncRouteComponent<TProps> : never;
