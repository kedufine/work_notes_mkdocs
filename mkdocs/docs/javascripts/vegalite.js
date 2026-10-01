/* ===========================================================================
 * Vega-Lite Charts — ```vegalite 블록을 Vega-Embed 로 렌더링한다.
 *
 * - superfences 가 <vegachart class="vegalite"> 로 내보낸 블록을 처리한다.
 * - Material for MkDocs 의 instant loading(document$) 및 다크 모드 전환을 지원한다.
 * - vega, vega-lite, vega-embed 가 로드되기 전이면 로드를 대기/보장한다.
 * ========================================================================= */
(() => {
  const VEGA_URL = "https://cdn.jsdelivr.net/npm/vega@5";
  const VEGALITE_URL = "https://cdn.jsdelivr.net/npm/vega-lite@5";
  const VEGAEMBED_URL = "https://cdn.jsdelivr.net/npm/vega-embed@6";

  let loadPromise = null;

  const loadScript = (src) =>
    new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${src}"]`);
      if (existing) {
        if (existing.dataset.loaded === "true" || window.vegaEmbed) return resolve();
        existing.addEventListener("load", resolve);
        existing.addEventListener("error", reject);
        return;
      }
      const script = document.createElement("script");
      script.src = src;
      script.onload = () => {
        script.dataset.loaded = "true";
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });

  const ensureVegaLibraries = async () => {
    if (window.vegaEmbed && window.vega && window.vegaLite) return window.vegaEmbed;
    if (loadPromise) return loadPromise;

    loadPromise = (async () => {
      if (!window.vega) await loadScript(VEGA_URL);
      if (!window.vegaLite) await loadScript(VEGALITE_URL);
      if (!window.vegaEmbed) await loadScript(VEGAEMBED_URL);
      return window.vegaEmbed;
    })();

    return loadPromise;
  };

  const getTheme = () => {
    const isDark = document.body.getAttribute("data-md-color-scheme") === "slate";
    return isDark ? "dark" : "default";
  };

  const renderChart = async (container, vegaEmbed) => {
    if (!container.dataset.source) {
      container.dataset.source = container.textContent.trim();
    }
    const raw = container.dataset.source;
    if (!raw) return;

    let spec;
    try {
      spec = JSON.parse(raw);
    } catch (err) {
      console.error("[Vega-Lite] JSON 파싱 오류:", err);
      container.innerHTML = `<pre style="color: #e53935; background: var(--md-code-bg-color); padding: 1rem; border-radius: 4px;">Vega-Lite JSON 오류: ${err.message}</pre>`;
      return;
    }

    if (!("width" in spec)) {
      spec.width = "container";
    }

    // 범례(Legend)는 하단 가로 방향(orient: bottom, direction: horizontal)을 기본값으로 적용
    if (!spec.config) spec.config = {};
    if (!spec.config.legend) spec.config.legend = {};
    if (!spec.config.legend.orient) spec.config.legend.orient = "bottom";
    if (!spec.config.legend.direction) spec.config.legend.direction = "horizontal";

    const theme = getTheme();
    container.innerHTML = "";
    const chartDiv = document.createElement("div");
    chartDiv.style.width = "100%";
    container.appendChild(chartDiv);

    try {
      await vegaEmbed(chartDiv, spec, {
        actions: false,
        theme: theme,
        renderer: "svg",
      });
      container.classList.add("vegalite--ready");
    } catch (err) {
      console.error("[Vega-Lite] 렌더링 오류:", err);
      chartDiv.innerHTML = `<pre style="color: #e53935; background: var(--md-code-bg-color); padding: 1rem; border-radius: 4px;">Vega-Lite 렌더링 실패: ${err.message}</pre>`;
    }
  };

  const renderAll = async () => {
    const targets = document.querySelectorAll("vegachart, .vegalite");
    if (!targets.length) return;

    try {
      const vegaEmbed = await ensureVegaLibraries();
      targets.forEach((el) => renderChart(el, vegaEmbed));
    } catch (err) {
      console.error("[Vega-Lite] 라이브러리 로드 실패:", err);
    }
  };

  // 다크/라이트 모드 변경 시 테마 재적용
  new MutationObserver(renderAll).observe(document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });

  // Material for MkDocs instant loading 및 초기 로드 대응
  const attach = () => {
    if (window.document$) {
      window.document$.subscribe(renderAll);
    } else {
      renderAll();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach);
  } else {
    attach();
  }
})();
