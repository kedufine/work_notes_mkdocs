/* ===========================================================================
 * Pretty Mermaid — ```mermaid 블록을 beautiful-mermaid 로 렌더링한다.
 *
 * - 원문은 superfences 가 <div class="pretty-mermaid"> 로 내보낸다(mkdocs.yml).
 *   Material 기본 렌더러는 pre.mermaid 만 처리하므로 서로 겹치지 않는다.
 * - 색은 사이트 디자인 토큰(--kb-*)에서 읽는다. XY 차트가 hex 값으로 계열 색을
 *   계산하므로 CSS 변수 대신 계산된 hex 를 넘기고, 라이트/다크 전환 시 다시 그린다.
 * - beautiful-mermaid 가 지원하지 않는 유형(gantt, pie, mindmap 등)이나 파싱 오류는
 *   Material 과 같은 mermaid@11 로 대신 그린다.
 * - 작성 규칙: .agents/skills/mkdocs-writing-guide/SKILL.md 5.3절
 * ========================================================================= */
(() => {
  const RENDERER_URL = "https://cdn.jsdelivr.net/npm/beautiful-mermaid@1.1.3/+esm";
  const FALLBACK_URL = "https://unpkg.com/mermaid@11/dist/mermaid.min.js";
  const FONT = "Pretendard Variable";
  const SUPPORTED =
    /^(graph|flowchart|sequenceDiagram|stateDiagram(-v2)?|classDiagram|erDiagram|xychart-beta)\b/;

  // 넓은 도표를 본문 폭에 맞출 때 허용하는 최소 축소 비율.
  // 이보다 더 줄여야 하면 글자가 읽기 어려우므로 가로 스크롤로 전환한다.
  const MIN_SCALE = 0.75;

  // SVG 가 Shadow DOM 안에 들어가므로 크기 규칙도 함께 넣는다.
  // --natural-width 는 SVG 원래 폭(px)이며 render() 에서 지정한다.
  const SHADOW_CSS = `
    :host { display: block; overflow-x: auto; }
    svg {
      display: block;
      margin: 0 auto;
      width: 100%;
      height: auto;
      max-width: var(--natural-width);
      min-width: calc(var(--natural-width) * ${MIN_SCALE});
    }
  `;

  let rendererPromise;
  let fallbackPromise;
  let fallbackSeq = 0;

  const loadRenderer = () => (rendererPromise ??= import(RENDERER_URL));

  const loadFallback = () =>
    (fallbackPromise ??= new Promise((resolve, reject) => {
      if (window.mermaid && !(window.mermaid instanceof Element)) return resolve(window.mermaid);
      const script = document.createElement("script");
      script.src = FALLBACK_URL;
      script.onload = () => resolve(window.mermaid);
      script.onerror = reject;
      document.head.append(script);
    }));

  // 현재 색 구성표의 토큰을 hex 로 읽는다.
  const readTokens = () => {
    const style = getComputedStyle(document.body);
    const token = (name) => style.getPropertyValue(name).trim();
    return {
      bg: token("--kb-bg"),
      fg: token("--kb-text-strong"),
      text: token("--kb-text"),
      muted: token("--kb-text-muted"),
      surface: token("--kb-bg-subtle"),
      border: token("--kb-border-strong"),
      series: token("--kb-sem-note"),
      dark: document.body.getAttribute("data-md-color-scheme") === "slate",
    };
  };

  // 첫 줄의 %% 주석과 %%{init}%% 지시문을 건너뛰고 도표 유형을 판별한다.
  const diagramHeader = (source) =>
    source
      .split("\n")
      .map((line) => line.trim())
      .find((line) => line && !line.startsWith("%%")) ?? "";

  const renderPretty = async (source, tokens) => {
    const { renderMermaidSVG } = await loadRenderer();
    const isChart = diagramHeader(source).startsWith("xychart");
    const svg = renderMermaidSVG(source, {
      bg: tokens.bg,
      fg: tokens.fg,
      line: tokens.muted,
      // 흐름도의 화살촉은 본문색, XY 차트의 계열 색은 의미색(파랑)을 쓴다.
      accent: isChart ? tokens.series : tokens.text,
      muted: tokens.muted,
      surface: tokens.surface,
      border: tokens.border,
      font: FONT,
      transparent: true,
      padding: 24,
      nodeSpacing: 32,
      layerSpacing: 48,
    });
    // 폰트는 사이트가 이미 로드한 Pretendard 를 쓰므로 Google Fonts @import 를 제거한다.
    return svg.replace(/@import url\([^)]*\);/g, "");
  };

  const renderFallback = async (source, tokens) => {
    const mermaid = await loadFallback();
    // base 테마는 themeVariables 로 색을 모두 지정할 수 있어 사이트 토큰을 그대로 쓴다.
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      fontFamily: FONT,
      themeVariables: {
        darkMode: tokens.dark,
        fontFamily: FONT,
        background: tokens.bg,
        primaryColor: tokens.surface,
        primaryTextColor: tokens.fg,
        primaryBorderColor: tokens.border,
        secondaryColor: tokens.surface,
        tertiaryColor: tokens.bg,
        lineColor: tokens.muted,
        textColor: tokens.text,
        pie1: tokens.series,
        pie2: tokens.text,
        pie3: tokens.muted,
        pieOpacity: "1",
        pieStrokeColor: tokens.bg,
        pieOuterStrokeColor: tokens.border,
        pieTitleTextColor: tokens.fg,
        pieSectionTextColor: tokens.bg,
        pieLegendTextColor: tokens.text,
      },
    });
    const { svg } = await mermaid.render(`__pretty_mermaid_${fallbackSeq++}`, source);
    return svg;
  };

  const renderError = (source, error) => {
    const pre = document.createElement("pre");
    pre.textContent = `Mermaid 렌더링 실패: ${error.message}\n\n${source}`;
    return pre.outerHTML;
  };

  const render = async (host, tokens) => {
    // 최초 렌더링 때 원문을 보관해 두고, 색 구성표가 바뀌면 원문에서 다시 그린다.
    host.dataset.source ??= host.textContent.trim();
    const source = host.dataset.source;

    let markup;
    try {
      markup = SUPPORTED.test(diagramHeader(source))
        ? await renderPretty(source, tokens)
        : await renderFallback(source, tokens);
    } catch (prettyError) {
      try {
        markup = await renderFallback(source, tokens);
      } catch {
        markup = renderError(source, prettyError);
      }
    }

    const root = host.shadowRoot ?? host.attachShadow({ mode: "open" });
    root.innerHTML = `<style>${SHADOW_CSS}</style>${markup}`;
    const svg = root.querySelector("svg");
    const naturalWidth = svg?.viewBox.baseVal?.width || svg?.width.baseVal.value;
    if (naturalWidth) host.style.setProperty("--natural-width", `${naturalWidth}px`);
    host.classList.add("pretty-mermaid--ready");
  };

  const renderAll = () => {
    const hosts = document.querySelectorAll(".pretty-mermaid");
    if (!hosts.length) return;
    const tokens = readTokens();
    hosts.forEach((host) => render(host, tokens));
  };

  // 라이트/다크 전환 시 다시 그린다.
  new MutationObserver(renderAll).observe(document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });

  // navigation.instant 로 페이지가 바뀔 때마다 document$ 가 새 문서를 알린다.
  if (window.document$) window.document$.subscribe(renderAll);
  else document.addEventListener("DOMContentLoaded", renderAll);
})();
