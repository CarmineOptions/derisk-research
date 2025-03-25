"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const React = require("react");
const useRouter = require("./useRouter.cjs");
function _interopNamespaceDefault(e) {
  const n = Object.create(null, { [Symbol.toStringTag]: { value: "Module" } });
  if (e) {
    for (const k in e) {
      if (k !== "default") {
        const d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: () => e[k]
        });
      }
    }
  }
  n.default = e;
  return Object.freeze(n);
}
const React__namespace = /* @__PURE__ */ _interopNamespaceDefault(React);
function useNavigate(_defaultOpts) {
  const { navigate } = useRouter.useRouter();
  return React__namespace.useCallback(
    (options) => {
      return navigate({
        from: _defaultOpts == null ? void 0 : _defaultOpts.from,
        ...options
      });
    },
    [_defaultOpts == null ? void 0 : _defaultOpts.from, navigate]
  );
}
function Navigate(props) {
  const router = useRouter.useRouter();
  const previousPropsRef = React__namespace.useRef(null);
  React__namespace.useEffect(() => {
    if (previousPropsRef.current !== props) {
      router.navigate({
        ...props
      });
      previousPropsRef.current = props;
    }
  }, [router, props]);
  return null;
}
exports.Navigate = Navigate;
exports.useNavigate = useNavigate;
//# sourceMappingURL=useNavigate.cjs.map
