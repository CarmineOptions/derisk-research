import { jsx } from "react/jsx-runtime";
function Asset({ tag, attrs, children }) {
  switch (tag) {
    case "title":
      return /* @__PURE__ */ jsx("title", { ...attrs, suppressHydrationWarning: true, children });
    case "meta":
      return /* @__PURE__ */ jsx("meta", { ...attrs, suppressHydrationWarning: true });
    case "link":
      return /* @__PURE__ */ jsx("link", { ...attrs, suppressHydrationWarning: true });
    case "style":
      return /* @__PURE__ */ jsx(
        "style",
        {
          ...attrs,
          dangerouslySetInnerHTML: { __html: children }
        }
      );
    case "script":
      if (attrs && attrs.src) {
        return /* @__PURE__ */ jsx("script", { ...attrs, suppressHydrationWarning: true });
      }
      if (typeof children === "string")
        return /* @__PURE__ */ jsx(
          "script",
          {
            ...attrs,
            dangerouslySetInnerHTML: {
              __html: children
            },
            suppressHydrationWarning: true
          }
        );
      return null;
    default:
      return null;
  }
}
export {
  Asset
};
//# sourceMappingURL=Asset.js.map
