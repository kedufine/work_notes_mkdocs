/* ===========================================================================
 * FAQ — 자주묻는 질문 페이지를 "메뉴 열 + 접이식 문답 목록"으로 묶고, 페이지 안 검색을 붙인다.
 *
 * - 대상: 제목에 `{ .kb-faq }` 표지가 붙은 페이지(h1.kb-faq)만.
 * - 원본의 `!!! question` 상자(div.admonition.question)를 <details class="kb-qa"> 로 바꾼다.
 *   스크립트가 실패하면 원래의 펼친 상자로 남으므로 내용은 잃지 않는다.
 * - h2(메뉴)마다 <section class="kb-faq-group"> 으로 묶고, 메뉴 경로 문단과 질문 수를
 *   왼쪽 열에 둔다. h2 는 그대로 옮기므로 우측 목차와 #앵커 링크는 바뀌지 않는다.
 * - 검색: 질문과 답변을 함께 거른다. 낱말을 띄어 쓰면 모두 들어간 질문만 남긴다.
 *   일치한 글자는 CSS Custom Highlight API 로 칠한다(DOM 을 고치지 않음, 미지원 브라우저는 강조만 생략).
 * - 모양은 extra.css 9절 "자주묻는 질문".
 * - Material 의 instant loading(document$) 으로 페이지가 바뀔 때마다 다시 적용한다.
 * ========================================================================= */
(() => {
  const HIGHLIGHT_NAME = "kb-faq-hit";

  const normalize = (text) => text.toLowerCase().replace(/\s+/g, " ").trim();

  // div.admonition.question → details.kb-qa
  const toDetails = (box) => {
    const details = document.createElement("details");
    details.className = "kb-qa";
    const summary = document.createElement("summary");
    const question = document.createElement("span");
    question.className = "kb-qa__q";
    const title = box.querySelector(":scope > .admonition-title");
    if (title) while (title.firstChild) question.appendChild(title.firstChild);
    summary.appendChild(question);

    const answer = document.createElement("div");
    answer.className = "kb-qa__a";
    Array.from(box.children).forEach((child) => {
      if (child !== title) answer.appendChild(child);
    });

    details.append(summary, answer);
    box.replaceWith(details);
    return details;
  };

  // h2 마다 메뉴 열 + 문답 목록으로 묶는다
  const group = (article) => {
    Array.from(article.querySelectorAll(":scope > h2")).forEach((heading) => {
      const section = document.createElement("section");
      section.className = "kb-faq-group";
      const head = document.createElement("div");
      head.className = "kb-faq-group__head";
      const items = document.createElement("div");
      items.className = "kb-faq-group__items";

      let node = heading.nextSibling;
      while (node && !(node.nodeType === Node.ELEMENT_NODE && /^(H1|H2|HR)$/.test(node.tagName))) {
        const next = node.nextSibling;
        items.appendChild(node);
        node = next;
      }

      heading.parentNode.insertBefore(section, heading);
      head.appendChild(heading);

      // 메뉴 경로 문단(":material-sitemap-outline: A → B")은 메뉴 열로 옮긴다
      const path = items.querySelector(":scope > p");
      if (path && path.querySelector(".twemoji")) {
        path.classList.add("kb-faq-group__path");
        path.querySelector(".twemoji").remove();
        head.appendChild(path);
      }

      const count = document.createElement("p");
      count.className = "kb-faq-group__count";
      head.appendChild(count);

      section.append(head, items);
    });
  };

  const buildToolbar = (total) => {
    const bar = document.createElement("div");
    bar.className = "kb-faq-toolbar";
    bar.setAttribute("role", "search");
    bar.innerHTML = `
      <div class="kb-faq-toolbar__row">
        <input class="kb-faq-toolbar__input" type="search" autocomplete="off"
               placeholder="질문이나 답변에서 찾기 (예: 결재직위명)"
               aria-label="이 페이지의 질문과 답변에서 찾기">
        <button class="kb-faq-toolbar__toggle" type="button">모두 펼치기</button>
      </div>
      <p class="kb-faq-toolbar__status" aria-live="polite">질문 ${total}개</p>`;
    return bar;
  };

  const highlight = (items, terms) => {
    if (!window.CSS || !CSS.highlights || typeof Highlight === "undefined") return;
    CSS.highlights.delete(HIGHLIGHT_NAME);
    if (!terms.length) return;
    const ranges = [];
    items.forEach((item) => {
      const walker = document.createTreeWalker(item, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const text = node.textContent.toLowerCase();
        terms.forEach((term) => {
          let from = text.indexOf(term);
          while (from !== -1) {
            const range = new Range();
            range.setStart(node, from);
            range.setEnd(node, from + term.length);
            ranges.push(range);
            from = text.indexOf(term, from + term.length);
          }
        });
      }
    });
    if (ranges.length) CSS.highlights.set(HIGHLIGHT_NAME, new Highlight(...ranges));
  };

  const build = () => {
    if (window.CSS && CSS.highlights) CSS.highlights.delete(HIGHLIGHT_NAME);
    const marker = document.querySelector(".md-content h1.kb-faq");
    if (!marker) return;
    const article = marker.closest(".md-typeset");
    if (!article || article.classList.contains("kb-faq-page")) return;
    article.classList.add("kb-faq-page");

    const items = Array.from(article.querySelectorAll(":scope > .admonition.question")).map(toDetails);
    if (!items.length) return;
    group(article);

    const sections = Array.from(article.querySelectorAll(".kb-faq-group"));
    const index = items.map((item) => ({ item, text: normalize(item.textContent) }));
    const toolbar = buildToolbar(items.length);
    if (sections.length) article.insertBefore(toolbar, sections[0]);

    const input = toolbar.querySelector(".kb-faq-toolbar__input");
    const toggle = toolbar.querySelector(".kb-faq-toolbar__toggle");
    const status = toolbar.querySelector(".kb-faq-toolbar__status");
    const empty = document.createElement("p");
    empty.className = "kb-faq-empty";
    empty.hidden = true;
    toolbar.after(empty);

    const updateCounts = () => {
      sections.forEach((section) => {
        const visible = section.querySelectorAll(".kb-qa:not([hidden])").length;
        section.hidden = visible === 0;
        section.querySelector(".kb-faq-group__count").textContent = `${visible}개`;
      });
    };

    const updateToggle = () => {
      const visible = items.filter((item) => !item.hidden);
      const allOpen = visible.length > 0 && visible.every((item) => item.open);
      toggle.textContent = allOpen ? "모두 접기" : "모두 펼치기";
    };

    const apply = () => {
      const query = normalize(input.value);
      const terms = query ? query.split(" ") : [];
      let shown = 0;
      index.forEach(({ item, text }) => {
        const match = terms.every((term) => text.includes(term));
        item.hidden = !match;
        if (match) shown += 1;
        // 검색 중에는 맞는 질문의 답변을 펼쳐 보이고, 검색어를 지우면 다시 접는다
        item.open = terms.length > 0 && match;
      });
      updateCounts();
      highlight(items.filter((item) => !item.hidden), terms);
      if (!terms.length) {
        status.textContent = `질문 ${items.length}개`;
        empty.hidden = true;
      } else if (shown) {
        status.textContent = `"${input.value.trim()}" 찾은 질문 ${shown}개 / 전체 ${items.length}개`;
        empty.hidden = true;
      } else {
        status.textContent = `"${input.value.trim()}" 찾은 질문 없음`;
        empty.textContent =
          "이 분야에는 맞는 질문이 없습니다. 다른 낱말로 찾거나, 상단 검색창에서 모든 분야를 찾아보세요.";
        empty.hidden = false;
      }
      updateToggle();
    };

    input.addEventListener("input", apply);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && input.value) {
        input.value = "";
        apply();
      }
    });
    toggle.addEventListener("click", () => {
      const visible = items.filter((item) => !item.hidden);
      const open = !visible.every((item) => item.open);
      visible.forEach((item) => {
        item.open = open;
      });
      updateToggle();
    });
    items.forEach((item) => item.addEventListener("toggle", updateToggle));

    updateCounts();
  };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(build);
  } else {
    document.addEventListener("DOMContentLoaded", build);
  }
})();
