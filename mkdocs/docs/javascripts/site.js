/* ===========================================================================
 * Site — 모든 페이지에 붙이는 읽기 보조 표시.
 *
 * - 절 번호: "1. 업무 한눈에 보기", "1.1 업무 지도"처럼 번호로 시작하는 h2·h3 과
 *   우측 목차 항목에서 번호를 <span class="kb-num"> 으로 감싸 테라코타로 구별한다.
 *   글자는 바꾸지 않으므로 앵커, 검색, 목차 링크는 그대로다.
 * - 출처 줄: "출처:"로 시작하는 문단에 kb-source 를 붙이고, 머리말을 따로 감싼다.
 *   절 끝의 근거 표기(작성 가이드 4.2.3절)가 본문보다 한 단계 낮게 보인다.
 * - 모양은 extra.css 8절. 스크립트가 실패해도 원래 글자는 그대로 남는다.
 * - Material 의 instant loading(document$) 으로 페이지가 바뀔 때마다 다시 적용한다.
 * ========================================================================= */
(() => {
  // 목차 링크처럼 글자 앞에 줄바꿈 공백이 있는 경우도 있어 앞쪽 공백을 따로 잡는다
  const NUMBER = /^(\s*)(\d+(?:\.\d+)*\.?)\s/;
  const SOURCE = /^(\s*)(출처\s*:)/;

  // 맨 앞 글자 마디에서 패턴의 둘째 묶음을 떼어 className 의 <span> 으로 감싼다.
  // 감쌌으면 true 를 돌려준다. 이미 감싼 요소는 건너뛴다
  const wrapLead = (element, pattern, className) => {
    if (element.querySelector(`:scope > .${className}`)) return false;
    const first = element.firstChild;
    if (!first || first.nodeType !== Node.TEXT_NODE) return false;
    const match = first.textContent.match(pattern);
    if (!match) return false;
    const [, space, lead] = match;
    const span = document.createElement("span");
    span.className = className;
    span.textContent = lead;
    first.textContent = first.textContent.slice(space.length + lead.length);
    element.insertBefore(span, first);
    return true;
  };

  const wrapNumber = (element) => wrapLead(element, NUMBER, "kb-num");

  // "출처:" 머리말을 감싸고 문단에 표지를 붙인다
  const markSource = (paragraph) => {
    if (wrapLead(paragraph, SOURCE, "kb-source__label")) paragraph.classList.add("kb-source");
  };

  const apply = () => {
    document.querySelectorAll(".md-content .md-typeset :is(h2, h3)").forEach(wrapNumber);
    document.querySelectorAll(".md-nav--secondary .md-nav__link > .md-ellipsis").forEach(wrapNumber);
    document.querySelectorAll(".md-content .md-typeset p").forEach(markSource);
  };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(apply);
  } else {
    document.addEventListener("DOMContentLoaded", apply);
  }
})();
