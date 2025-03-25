import * as React from "react";
import { useRouter } from "./useRouter.js";
function useNavigate(_defaultOpts) {
  const { navigate } = useRouter();
  return React.useCallback(
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
  const router = useRouter();
  const previousPropsRef = React.useRef(null);
  React.useEffect(() => {
    if (previousPropsRef.current !== props) {
      router.navigate({
        ...props
      });
      previousPropsRef.current = props;
    }
  }, [router, props]);
  return null;
}
export {
  Navigate,
  useNavigate
};
//# sourceMappingURL=useNavigate.js.map
