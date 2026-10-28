/* ===========================================================================
 * Changelog — 기능개선 내역(배포 이력) 페이지를 "날짜 열 + 항목 열" 구조로 묶는다.
 *
 * - 대상: 제목에 `{ .kb-changelog }` 표지가 붙은 페이지(h1.kb-changelog)만.
 * - 마크다운이 만드는 HTML 은 h2 뒤에 항목이 형제로 나열되는 평평한 구조라
 *   CSS 만으로는 격자를 만들 수 없다. h2 마다 <section class="kb-release"> 로 묶는다.
 *   h2 는 그대로 옮기므로 우측 목차와 #앵커 링크는 바뀌지 않는다.
 * - 항목 제목 앞의 [메뉴명] 은 <span class="kb-tag"> 로 분리해 고정 폭 열에 둔다.
 *   메뉴명이 없는 항목도 빈 칸을 넣어 제목이 같은 세로선에서 시작하게 한다.
 * - 모양은 extra.css 9절 "기능개선 내역(배포 이력)".
 * - Material 의 instant loading(document$) 으로 페이지가 바뀔 때마다 다시 적용한다.
 * ========================================================================= */
(() => {
  const TAG_PATTERN = /^\s*\[([^\]]+)\]\s*/;
  const DATE_PATTERN = /^(\d{4}년)\s+(.+)$/;
  const ITEM_SELECTOR = ":scope > details, :scope > .admonition";
  const TITLE_SELECTOR = ":scope > summary, :scope > .admonition-title";

  // 제목 앞 [메뉴명] 을 태그로 분리한다. 메뉴명이 없으면 빈 태그를 넣는다
  const splitTag = (title) => {
    if (title.querySelector(".kb-tag")) return;
    const tag = document.createElement("span");
    tag.className = "kb-tag";
    const first = title.firstChild;
    const match = first && first.nodeType === Node.TEXT_NODE && first.textContent.match(TAG_PATTERN);
    if (match) {
      tag.textContent = match[1];
      first.textContent = first.textContent.slice(match[0].length);
    } else {
      tag.classList.add("kb-tag--empty");
      tag.setAttribute("aria-hidden", "true");
    }
    title.insertBefore(tag, title.firstChild);

    // 나머지 글자는 한 칸(격자의 제목 열)에 들어가도록 감싼다
    const text = document.createElement("span");
    text.className = "kb-item-title";
    while (tag.nextSibling) text.appendChild(tag.nextSibling);
    title.appendChild(text);
  };

  // "2026년 10월 27일" → 연도는 화면에서 숨기고(페이지 제목에 있음) 월·일만 크게 보인다
  const splitDate = (heading) => {
    if (heading.querySelector(".kb-release__day")) return;
    const first = heading.firstChild;
    if (!first || first.nodeType !== Node.TEXT_NODE) return;
    const match = first.textContent.trim().match(DATE_PATTERN);
    if (!match) return;
    const year = document.createElement("span");
    year.className = "kb-visually-hidden";
    year.textContent = `${match[1]} `;
    const day = document.createElement("span");
    day.className = "kb-release__day";
    day.textContent = match[2];
    heading.replaceChild(day, first);
    heading.insertBefore(year, day);
  };

  const build = () => {
    const marker = document.querySelector(".md-content h1.kb-changelog");
    if (!marker) return;
    const article = marker.closest(".md-typeset");
    if (!article || article.classList.contains("kb-changelog-page")) return;
    article.classList.add("kb-changelog-page");

    const headings = Array.from(article.querySelectorAll(":scope > h2"));
    headings.forEach((heading) => {
      const section = document.createElement("section");
      section.className = "kb-release";
      const rail = document.createElement("div");
      rail.className = "kb-release__date";
      const items = document.createElement("div");
      items.className = "kb-release__items";

      // 다음 h2 또는 구분선(hr) 전까지가 이 배포일의 항목이다
      let node = heading.nextSibling;
      while (node && !(node.nodeType === Node.ELEMENT_NODE && /^(H1|H2|HR)$/.test(node.tagName))) {
        const next = node.nextSibling;
        items.appendChild(node);
        node = next;
      }

      heading.parentNode.insertBefore(section, heading);
      rail.appendChild(heading);
      splitDate(heading);

      const entries = items.querySelectorAll(ITEM_SELECTOR);
      const count = document.createElement("p");
      count.className = "kb-release__count";
      if (entries.length) {
        count.textContent = `${entries.length}건`;
      } else {
        // 원본의 "없음" 문단은 날짜 열의 문구로 대신한다
        section.classList.add("kb-release--empty");
        count.textContent = "개선 없음";
      }
      rail.appendChild(count);

      entries.forEach((entry) => {
        const title = entry.querySelector(TITLE_SELECTOR);
        if (title) splitTag(title);
      });

      section.appendChild(rail);
      section.appendChild(items);
    });
  };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(build);
  } else {
    document.addEventListener("DOMContentLoaded", build);
  }
})();
