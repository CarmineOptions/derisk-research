"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const routerCore = require("@tanstack/router-core");
const createRouter = (options) => {
  return new Router(options);
};
class Router extends routerCore.RouterCore {
  constructor(options) {
    super(options);
  }
}
exports.Router = Router;
exports.createRouter = createRouter;
//# sourceMappingURL=router.cjs.map
