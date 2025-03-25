import { template, spread, mergeProps, insert, addEventListener, effect, className, createComponent, memo, setAttribute, delegateEvents } from "solid-js/web";
import { clsx } from "clsx";
import invariant from "tiny-invariant";
import { rootRouteId, trimPath } from "@tanstack/router-core";
import { createMemo } from "solid-js";
import { useDevtoolsOnClose } from "./context.js";
import { useStyles } from "./useStyles.js";
import useLocalStorage from "./useLocalStorage.js";
import { Explorer } from "./Explorer.js";
import { multiSortBy, getStatusColor, getRouteStatusColor } from "./utils.js";
import { AgeTicker } from "./AgeTicker.js";
var _tmpl$ = /* @__PURE__ */ template(`<button><div>TANSTACK</div><div>TanStack Router v1`), _tmpl$2 = /* @__PURE__ */ template(`<div><div role=button><div></div><div><div><code> </code><code>`), _tmpl$3 = /* @__PURE__ */ template(`<div>`), _tmpl$4 = /* @__PURE__ */ template(`<div><button><svg xmlns=http://www.w3.org/2000/svg width=10 height=6 fill=none viewBox="0 0 10 6"><path stroke=currentColor stroke-linecap=round stroke-linejoin=round stroke-width=1.667 d="M1 1l4 4 4-4"></path></svg></button><div><div></div><div><div></div></div></div><div><div><div><span>Pathname</span></div><div><code></code></div><div><div><button type=button>Routes</button><button type=button>Matches</button></div><div><div>age / staleTime / gcTime</div></div></div><div>`), _tmpl$5 = /* @__PURE__ */ template(`<div><span>masked`), _tmpl$6 = /* @__PURE__ */ template(`<code>`), _tmpl$7 = /* @__PURE__ */ template(`<div role=button><div></div><code>`), _tmpl$8 = /* @__PURE__ */ template(`<div><div><div>Cached Matches</div><div>age / staleTime / gcTime</div></div><div>`), _tmpl$9 = /* @__PURE__ */ template(`<div><div>Match Details</div><div><div><div><div></div></div><div><div>ID:</div><div><code></code></div></div><div><div>State:</div><div></div></div><div><div>Last Updated:</div><div></div></div></div></div><div>Explorer</div><div>`), _tmpl$10 = /* @__PURE__ */ template(`<div>Loader Data`), _tmpl$11 = /* @__PURE__ */ template(`<div><div>Search Params</div><div>`);
function Logo(props) {
  const {
    className: className$1,
    ...rest
  } = props;
  const styles = useStyles();
  return (() => {
    var _el$ = _tmpl$(), _el$2 = _el$.firstChild, _el$3 = _el$2.nextSibling;
    spread(_el$, mergeProps(rest, {
      get ["class"]() {
        return clsx(styles().logo, className$1 ? className$1() : "");
      }
    }), false, true);
    effect((_p$) => {
      var _v$ = styles().tanstackLogo, _v$2 = styles().routerLogo;
      _v$ !== _p$.e && className(_el$2, _p$.e = _v$);
      _v$2 !== _p$.t && className(_el$3, _p$.t = _v$2);
      return _p$;
    }, {
      e: void 0,
      t: void 0
    });
    return _el$;
  })();
}
function RouteComp({
  routerState,
  router,
  route,
  isRoot,
  activeId,
  setActiveId
}) {
  const styles = useStyles();
  const matches = createMemo(() => routerState().pendingMatches || routerState().matches);
  const match = createMemo(() => routerState().matches.find((d) => d.routeId === route.id));
  const param = createMemo(() => {
    var _a, _b;
    try {
      if ((_a = match()) == null ? void 0 : _a.params) {
        const p = (_b = match()) == null ? void 0 : _b.params;
        const r = route.path || trimPath(route.id);
        if (r.startsWith("$")) {
          const trimmed = r.slice(1);
          if (p[trimmed]) {
            return `(${p[trimmed]})`;
          }
        }
      }
      return "";
    } catch (error) {
      return "";
    }
  });
  return (() => {
    var _el$4 = _tmpl$2(), _el$5 = _el$4.firstChild, _el$6 = _el$5.firstChild, _el$7 = _el$6.nextSibling, _el$8 = _el$7.firstChild, _el$9 = _el$8.firstChild, _el$10 = _el$9.firstChild, _el$11 = _el$9.nextSibling;
    _el$5.$$click = () => {
      if (match()) {
        setActiveId(activeId() === route.id ? "" : route.id);
      }
    };
    insert(_el$9, () => isRoot ? rootRouteId : route.path || trimPath(route.id), _el$10);
    insert(_el$11, param);
    insert(_el$7, createComponent(AgeTicker, {
      get match() {
        return match();
      },
      router
    }), null);
    insert(_el$4, (() => {
      var _c$ = memo(() => {
        var _a;
        return !!((_a = route.children) == null ? void 0 : _a.length);
      });
      return () => _c$() ? (() => {
        var _el$12 = _tmpl$3();
        insert(_el$12, () => [...route.children].sort((a, b) => {
          return a.rank - b.rank;
        }).map((r) => createComponent(RouteComp, {
          routerState,
          router,
          route: r,
          activeId,
          setActiveId
        })));
        effect(() => className(_el$12, styles().nestedRouteRow(!!isRoot)));
        return _el$12;
      })() : null;
    })(), null);
    effect((_p$) => {
      var _v$3 = `Open match details for ${route.id}`, _v$4 = clsx(styles().routesRowContainer(route.id === activeId(), !!match())), _v$5 = clsx(styles().matchIndicator(getRouteStatusColor(matches(), route))), _v$6 = clsx(styles().routesRow(!!match())), _v$7 = styles().code, _v$8 = styles().routeParamInfo;
      _v$3 !== _p$.e && setAttribute(_el$5, "aria-label", _p$.e = _v$3);
      _v$4 !== _p$.t && className(_el$5, _p$.t = _v$4);
      _v$5 !== _p$.a && className(_el$6, _p$.a = _v$5);
      _v$6 !== _p$.o && className(_el$7, _p$.o = _v$6);
      _v$7 !== _p$.i && className(_el$9, _p$.i = _v$7);
      _v$8 !== _p$.n && className(_el$11, _p$.n = _v$8);
      return _p$;
    }, {
      e: void 0,
      t: void 0,
      a: void 0,
      o: void 0,
      i: void 0,
      n: void 0
    });
    return _el$4;
  })();
}
const BaseTanStackRouterDevtoolsPanel = function BaseTanStackRouterDevtoolsPanel2({
  ...props
}) {
  const {
    isOpen = true,
    setIsOpen,
    handleDragStart,
    router,
    routerState,
    shadowDOMTarget,
    ...panelProps
  } = props;
  const {
    onCloseClick
  } = useDevtoolsOnClose();
  const styles = useStyles();
  const {
    className: className$1,
    style,
    ...otherPanelProps
  } = panelProps;
  invariant(router, "No router was found for the TanStack Router Devtools. Please place the devtools in the <RouterProvider> component tree or pass the router instance to the devtools manually.");
  const [showMatches, setShowMatches] = useLocalStorage("tanstackRouterDevtoolsShowMatches", true);
  const [activeId, setActiveId] = useLocalStorage("tanstackRouterDevtoolsActiveRouteId", "");
  const activeMatch = createMemo(() => {
    const matches = [...routerState().pendingMatches ?? [], ...routerState().matches, ...routerState().cachedMatches];
    return matches.find((d) => d.routeId === activeId() || d.id === activeId());
  });
  const hasSearch = createMemo(() => Object.keys(routerState().location.search).length);
  const explorerState = createMemo(() => {
    return {
      ...router(),
      state: routerState()
    };
  });
  const routerExplorerValue = createMemo(() => Object.fromEntries(multiSortBy(Object.keys(explorerState()), ["state", "routesById", "routesByPath", "flatRoutes", "options", "manifest"].map((d) => (dd) => dd !== d)).map((key) => [key, explorerState()[key]]).filter((d) => typeof d[1] !== "function" && !["__store", "basepath", "injectedHtml", "subscribers", "latestLoadPromise", "navigateTimeout", "resetNextScroll", "tempLocationKey", "latestLocation", "routeTree", "history"].includes(d[0]))));
  const activeMatchLoaderData = createMemo(() => {
    var _a;
    return (_a = activeMatch()) == null ? void 0 : _a.loaderData;
  });
  const activeMatchValue = createMemo(() => activeMatch());
  const locationSearchValue = createMemo(() => routerState().location.search);
  return (() => {
    var _el$13 = _tmpl$4(), _el$14 = _el$13.firstChild, _el$15 = _el$14.firstChild, _el$16 = _el$14.nextSibling, _el$17 = _el$16.firstChild, _el$18 = _el$17.nextSibling, _el$19 = _el$18.firstChild, _el$20 = _el$16.nextSibling, _el$21 = _el$20.firstChild, _el$22 = _el$21.firstChild;
    _el$22.firstChild;
    var _el$24 = _el$22.nextSibling, _el$25 = _el$24.firstChild, _el$26 = _el$24.nextSibling, _el$27 = _el$26.firstChild, _el$28 = _el$27.firstChild, _el$29 = _el$28.nextSibling, _el$30 = _el$27.nextSibling, _el$31 = _el$26.nextSibling;
    spread(_el$13, mergeProps({
      get ["class"]() {
        return clsx(styles().devtoolsPanel, "TanStackRouterDevtoolsPanel", className$1 ? className$1() : "");
      },
      get style() {
        return style ? style() : "";
      }
    }, otherPanelProps), false, true);
    insert(_el$13, handleDragStart ? (() => {
      var _el$32 = _tmpl$3();
      addEventListener(_el$32, "mousedown", handleDragStart, true);
      effect(() => className(_el$32, styles().dragHandle));
      return _el$32;
    })() : null, _el$14);
    _el$14.$$click = (e) => {
      if (setIsOpen) {
        setIsOpen(false);
      }
      onCloseClick(e);
    };
    insert(_el$17, createComponent(Logo, {
      "aria-hidden": true,
      onClick: (e) => {
        if (setIsOpen) {
          setIsOpen(false);
        }
        onCloseClick(e);
      }
    }));
    insert(_el$19, createComponent(Explorer, {
      label: "Router",
      value: routerExplorerValue,
      defaultExpanded: {
        state: {},
        context: {},
        options: {}
      },
      filterSubEntries: (subEntries) => {
        return subEntries.filter((d) => typeof d.value() !== "function");
      }
    }));
    insert(_el$22, (() => {
      var _c$2 = memo(() => !!routerState().location.maskedLocation);
      return () => _c$2() ? (() => {
        var _el$33 = _tmpl$5(), _el$34 = _el$33.firstChild;
        effect((_p$) => {
          var _v$27 = styles().maskedBadgeContainer, _v$28 = styles().maskedBadge;
          _v$27 !== _p$.e && className(_el$33, _p$.e = _v$27);
          _v$28 !== _p$.t && className(_el$34, _p$.t = _v$28);
          return _p$;
        }, {
          e: void 0,
          t: void 0
        });
        return _el$33;
      })() : null;
    })(), null);
    insert(_el$25, () => routerState().location.pathname);
    insert(_el$24, (() => {
      var _c$3 = memo(() => !!routerState().location.maskedLocation);
      return () => _c$3() ? (() => {
        var _el$35 = _tmpl$6();
        insert(_el$35, () => {
          var _a;
          return (_a = routerState().location.maskedLocation) == null ? void 0 : _a.pathname;
        });
        effect(() => className(_el$35, styles().maskedLocation));
        return _el$35;
      })() : null;
    })(), null);
    _el$28.$$click = () => {
      setShowMatches(false);
    };
    _el$29.$$click = () => {
      setShowMatches(true);
    };
    insert(_el$31, (() => {
      var _c$4 = memo(() => !!!showMatches());
      return () => _c$4() ? createComponent(RouteComp, {
        routerState,
        router,
        get route() {
          return router().routeTree;
        },
        isRoot: true,
        activeId,
        setActiveId
      }) : (() => {
        var _el$36 = _tmpl$3();
        insert(_el$36, () => {
          var _a, _b;
          return (_b = ((_a = routerState().pendingMatches) == null ? void 0 : _a.length) ? routerState().pendingMatches : routerState().matches) == null ? void 0 : _b.map((match, i) => {
            return (() => {
              var _el$37 = _tmpl$7(), _el$38 = _el$37.firstChild, _el$39 = _el$38.nextSibling;
              _el$37.$$click = () => setActiveId(activeId() === match.id ? "" : match.id);
              insert(_el$39, () => `${match.routeId === rootRouteId ? rootRouteId : match.pathname}`);
              insert(_el$37, createComponent(AgeTicker, {
                match,
                router
              }), null);
              effect((_p$) => {
                var _v$29 = `Open match details for ${match.id}`, _v$30 = clsx(styles().matchRow(match === activeMatch())), _v$31 = clsx(styles().matchIndicator(getStatusColor(match))), _v$32 = styles().matchID;
                _v$29 !== _p$.e && setAttribute(_el$37, "aria-label", _p$.e = _v$29);
                _v$30 !== _p$.t && className(_el$37, _p$.t = _v$30);
                _v$31 !== _p$.a && className(_el$38, _p$.a = _v$31);
                _v$32 !== _p$.o && className(_el$39, _p$.o = _v$32);
                return _p$;
              }, {
                e: void 0,
                t: void 0,
                a: void 0,
                o: void 0
              });
              return _el$37;
            })();
          });
        });
        return _el$36;
      })();
    })());
    insert(_el$20, (() => {
      var _c$5 = memo(() => !!routerState().cachedMatches.length);
      return () => _c$5() ? (() => {
        var _el$40 = _tmpl$8(), _el$41 = _el$40.firstChild, _el$42 = _el$41.firstChild, _el$43 = _el$42.nextSibling, _el$44 = _el$41.nextSibling;
        insert(_el$44, () => routerState().cachedMatches.map((match) => {
          return (() => {
            var _el$45 = _tmpl$7(), _el$46 = _el$45.firstChild, _el$47 = _el$46.nextSibling;
            _el$45.$$click = () => setActiveId(activeId() === match.id ? "" : match.id);
            insert(_el$47, () => `${match.id}`);
            insert(_el$45, createComponent(AgeTicker, {
              match,
              router
            }), null);
            effect((_p$) => {
              var _v$36 = `Open match details for ${match.id}`, _v$37 = clsx(styles().matchRow(match === activeMatch())), _v$38 = clsx(styles().matchIndicator(getStatusColor(match))), _v$39 = styles().matchID;
              _v$36 !== _p$.e && setAttribute(_el$45, "aria-label", _p$.e = _v$36);
              _v$37 !== _p$.t && className(_el$45, _p$.t = _v$37);
              _v$38 !== _p$.a && className(_el$46, _p$.a = _v$38);
              _v$39 !== _p$.o && className(_el$47, _p$.o = _v$39);
              return _p$;
            }, {
              e: void 0,
              t: void 0,
              a: void 0,
              o: void 0
            });
            return _el$45;
          })();
        }));
        effect((_p$) => {
          var _v$33 = styles().cachedMatchesContainer, _v$34 = styles().detailsHeader, _v$35 = styles().detailsHeaderInfo;
          _v$33 !== _p$.e && className(_el$40, _p$.e = _v$33);
          _v$34 !== _p$.t && className(_el$41, _p$.t = _v$34);
          _v$35 !== _p$.a && className(_el$43, _p$.a = _v$35);
          return _p$;
        }, {
          e: void 0,
          t: void 0,
          a: void 0
        });
        return _el$40;
      })() : null;
    })(), null);
    insert(_el$13, (() => {
      var _c$6 = memo(() => {
        var _a;
        return !!(activeMatch() && ((_a = activeMatch()) == null ? void 0 : _a.status));
      });
      return () => _c$6() ? (() => {
        var _el$48 = _tmpl$9(), _el$49 = _el$48.firstChild, _el$50 = _el$49.nextSibling, _el$51 = _el$50.firstChild, _el$52 = _el$51.firstChild, _el$53 = _el$52.firstChild, _el$54 = _el$52.nextSibling, _el$55 = _el$54.firstChild, _el$56 = _el$55.nextSibling, _el$57 = _el$56.firstChild, _el$58 = _el$54.nextSibling, _el$59 = _el$58.firstChild, _el$60 = _el$59.nextSibling, _el$61 = _el$58.nextSibling, _el$62 = _el$61.firstChild, _el$63 = _el$62.nextSibling, _el$64 = _el$50.nextSibling, _el$65 = _el$64.nextSibling;
        insert(_el$53, (() => {
          var _c$8 = memo(() => {
            var _a, _b;
            return !!(((_a = activeMatch()) == null ? void 0 : _a.status) === "success" && ((_b = activeMatch()) == null ? void 0 : _b.isFetching));
          });
          return () => {
            var _a;
            return _c$8() ? "fetching" : (_a = activeMatch()) == null ? void 0 : _a.status;
          };
        })());
        insert(_el$57, () => {
          var _a;
          return (_a = activeMatch()) == null ? void 0 : _a.id;
        });
        insert(_el$60, (() => {
          var _c$9 = memo(() => {
            var _a;
            return !!((_a = routerState().pendingMatches) == null ? void 0 : _a.find((d) => {
              var _a2;
              return d.id === ((_a2 = activeMatch()) == null ? void 0 : _a2.id);
            }));
          });
          return () => _c$9() ? "Pending" : routerState().matches.find((d) => {
            var _a;
            return d.id === ((_a = activeMatch()) == null ? void 0 : _a.id);
          }) ? "Active" : "Cached";
        })());
        insert(_el$63, (() => {
          var _c$10 = memo(() => {
            var _a;
            return !!((_a = activeMatch()) == null ? void 0 : _a.updatedAt);
          });
          return () => {
            var _a;
            return _c$10() ? new Date((_a = activeMatch()) == null ? void 0 : _a.updatedAt).toLocaleTimeString() : "N/A";
          };
        })());
        insert(_el$48, (() => {
          var _c$11 = memo(() => !!activeMatchLoaderData());
          return () => _c$11() ? [(() => {
            var _el$66 = _tmpl$10();
            effect(() => className(_el$66, styles().detailsHeader));
            return _el$66;
          })(), (() => {
            var _el$67 = _tmpl$3();
            insert(_el$67, createComponent(Explorer, {
              label: "loaderData",
              value: activeMatchLoaderData,
              defaultExpanded: {}
            }));
            effect(() => className(_el$67, styles().detailsContent));
            return _el$67;
          })()] : null;
        })(), _el$64);
        insert(_el$65, createComponent(Explorer, {
          label: "Match",
          value: activeMatchValue,
          defaultExpanded: {}
        }));
        effect((_p$) => {
          var _a, _b;
          var _v$40 = styles().thirdContainer, _v$41 = styles().detailsHeader, _v$42 = styles().matchDetails, _v$43 = styles().matchStatus((_a = activeMatch()) == null ? void 0 : _a.status, (_b = activeMatch()) == null ? void 0 : _b.isFetching), _v$44 = styles().matchDetailsInfoLabel, _v$45 = styles().matchDetailsInfo, _v$46 = styles().matchDetailsInfoLabel, _v$47 = styles().matchDetailsInfo, _v$48 = styles().matchDetailsInfoLabel, _v$49 = styles().matchDetailsInfo, _v$50 = styles().detailsHeader, _v$51 = styles().detailsContent;
          _v$40 !== _p$.e && className(_el$48, _p$.e = _v$40);
          _v$41 !== _p$.t && className(_el$49, _p$.t = _v$41);
          _v$42 !== _p$.a && className(_el$51, _p$.a = _v$42);
          _v$43 !== _p$.o && className(_el$52, _p$.o = _v$43);
          _v$44 !== _p$.i && className(_el$54, _p$.i = _v$44);
          _v$45 !== _p$.n && className(_el$56, _p$.n = _v$45);
          _v$46 !== _p$.s && className(_el$58, _p$.s = _v$46);
          _v$47 !== _p$.h && className(_el$60, _p$.h = _v$47);
          _v$48 !== _p$.r && className(_el$61, _p$.r = _v$48);
          _v$49 !== _p$.d && className(_el$63, _p$.d = _v$49);
          _v$50 !== _p$.l && className(_el$64, _p$.l = _v$50);
          _v$51 !== _p$.u && className(_el$65, _p$.u = _v$51);
          return _p$;
        }, {
          e: void 0,
          t: void 0,
          a: void 0,
          o: void 0,
          i: void 0,
          n: void 0,
          s: void 0,
          h: void 0,
          r: void 0,
          d: void 0,
          l: void 0,
          u: void 0
        });
        return _el$48;
      })() : null;
    })(), null);
    insert(_el$13, (() => {
      var _c$7 = memo(() => !!hasSearch());
      return () => _c$7() ? (() => {
        var _el$68 = _tmpl$11(), _el$69 = _el$68.firstChild, _el$70 = _el$69.nextSibling;
        insert(_el$70, createComponent(Explorer, {
          value: locationSearchValue,
          get defaultExpanded() {
            return Object.keys(routerState().location.search).reduce((obj, next) => {
              obj[next] = {};
              return obj;
            }, {});
          }
        }));
        effect((_p$) => {
          var _v$52 = styles().fourthContainer, _v$53 = styles().detailsHeader, _v$54 = styles().detailsContent;
          _v$52 !== _p$.e && className(_el$68, _p$.e = _v$52);
          _v$53 !== _p$.t && className(_el$69, _p$.t = _v$53);
          _v$54 !== _p$.a && className(_el$70, _p$.a = _v$54);
          return _p$;
        }, {
          e: void 0,
          t: void 0,
          a: void 0
        });
        return _el$68;
      })() : null;
    })(), null);
    effect((_p$) => {
      var _v$9 = styles().panelCloseBtn, _v$10 = styles().panelCloseBtnIcon, _v$11 = styles().firstContainer, _v$12 = styles().row, _v$13 = styles().routerExplorerContainer, _v$14 = styles().routerExplorer, _v$15 = styles().secondContainer, _v$16 = styles().matchesContainer, _v$17 = styles().detailsHeader, _v$18 = styles().detailsContent, _v$19 = styles().detailsHeader, _v$20 = styles().routeMatchesToggle, _v$21 = !showMatches(), _v$22 = clsx(styles().routeMatchesToggleBtn(!showMatches(), true)), _v$23 = showMatches(), _v$24 = clsx(styles().routeMatchesToggleBtn(!!showMatches(), false)), _v$25 = styles().detailsHeaderInfo, _v$26 = clsx(styles().routesContainer);
      _v$9 !== _p$.e && className(_el$14, _p$.e = _v$9);
      _v$10 !== _p$.t && setAttribute(_el$15, "class", _p$.t = _v$10);
      _v$11 !== _p$.a && className(_el$16, _p$.a = _v$11);
      _v$12 !== _p$.o && className(_el$17, _p$.o = _v$12);
      _v$13 !== _p$.i && className(_el$18, _p$.i = _v$13);
      _v$14 !== _p$.n && className(_el$19, _p$.n = _v$14);
      _v$15 !== _p$.s && className(_el$20, _p$.s = _v$15);
      _v$16 !== _p$.h && className(_el$21, _p$.h = _v$16);
      _v$17 !== _p$.r && className(_el$22, _p$.r = _v$17);
      _v$18 !== _p$.d && className(_el$24, _p$.d = _v$18);
      _v$19 !== _p$.l && className(_el$26, _p$.l = _v$19);
      _v$20 !== _p$.u && className(_el$27, _p$.u = _v$20);
      _v$21 !== _p$.c && (_el$28.disabled = _p$.c = _v$21);
      _v$22 !== _p$.w && className(_el$28, _p$.w = _v$22);
      _v$23 !== _p$.m && (_el$29.disabled = _p$.m = _v$23);
      _v$24 !== _p$.f && className(_el$29, _p$.f = _v$24);
      _v$25 !== _p$.y && className(_el$30, _p$.y = _v$25);
      _v$26 !== _p$.g && className(_el$31, _p$.g = _v$26);
      return _p$;
    }, {
      e: void 0,
      t: void 0,
      a: void 0,
      o: void 0,
      i: void 0,
      n: void 0,
      s: void 0,
      h: void 0,
      r: void 0,
      d: void 0,
      l: void 0,
      u: void 0,
      c: void 0,
      w: void 0,
      m: void 0,
      f: void 0,
      y: void 0,
      g: void 0
    });
    return _el$13;
  })();
};
delegateEvents(["click", "mousedown"]);
export {
  BaseTanStackRouterDevtoolsPanel,
  BaseTanStackRouterDevtoolsPanel as default
};
//# sourceMappingURL=BaseTanStackRouterDevtoolsPanel.js.map
