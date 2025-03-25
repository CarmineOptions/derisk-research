"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const reactRouterDevtools = require("@tanstack/react-router-devtools");
console.warn(
  "[@tanstack/router-devtools] This package has moved to @tanstack/react-router-devtools. Please switch to the new package at your earliest convenience, as this package will be dropped in the next major version release."
);
Object.defineProperty(exports, "TanStackRouterDevtools", {
  enumerable: true,
  get: () => reactRouterDevtools.TanStackRouterDevtoolsInProd
});
Object.defineProperty(exports, "TanStackRouterDevtoolsPanel", {
  enumerable: true,
  get: () => reactRouterDevtools.TanStackRouterDevtoolsPanelInProd
});
//# sourceMappingURL=index.cjs.map
