import { RouterCore } from "@tanstack/router-core";
const createRouter = (options) => {
  return new Router(options);
};
class Router extends RouterCore {
  constructor(options) {
    super(options);
  }
}
export {
  Router,
  createRouter
};
//# sourceMappingURL=router.js.map
