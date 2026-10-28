/* ===========================================================================
 * Approval — 인수인계 건의 진행 상태를 결재란으로 보여 준다.
 *
 * - 대상: 머리글이 "상태"인 표 열의 칸 가운데 값이 진행 단계(handover-to-mkdocs 4.6절)인 칸.
 *   지금은 인수인계 허브(handover/index.md)의 요약 표가 해당한다.
 *   "완료", "예정"처럼 진행 단계가 아닌 상태 값은 건드리지 않는다.
 * - 칸의 글자(예: "보강 완료")를 결재란으로 바꾼다. 상태 값은 결재란의 aria-label 과
 *   title(마우스를 올리면 보이는 설명)로 남는다. 스크립트가 실패하면 글자가 그대로 보인다.
 * - 단계 정의는 handover-to-mkdocs 4.6절의 상태 값을 따른다.
 * - 모양은 extra.css 9절 "결재란".
 * - Material 의 instant loading(document$) 으로 페이지가 바뀔 때마다 다시 적용한다.
 * ========================================================================= */
(() => {
  // AGENTS.md "처리 과정"의 1~4단계
  const STAGES = ["변환", "등록", "질문지", "반영"];

  // 상태 → [끝난 단계 수, 마지막 단계가 일부만 끝났는지]
  const STATUS_STAGES = {
    "1차 등록": [2, false],
    "질문지 회신 대기": [3, false],
    "일부 미회신": [4, true],
    "보강 완료": [4, false],
  };

  const create = (className, text) => {
    const element = document.createElement("span");
    element.className = className;
    if (text) element.textContent = text;
    return element;
  };

  const buildSign = ([done, partial]) => {
    const sign = create("kb-sign kb-sign--mini");
    const states = STAGES.map((label, index) => {
      const isDone = index < done;
      const isPartial = partial && index === done - 1;
      const mark = create("kb-sign__mark");
      if (isDone) {
        mark.appendChild(create(isPartial ? "kb-seal kb-seal--partial" : "kb-seal", isPartial ? "일부" : "완료"));
      }
      const cell = create("kb-sign__cell");
      cell.append(create("kb-sign__role", label), mark);
      sign.appendChild(cell);
      return `${label} ${isPartial ? "일부 완료" : isDone ? "완료" : "대기"}`;
    });
    sign.setAttribute("role", "img");
    sign.setAttribute("aria-label", `진행 단계: ${states.join(", ")}`);
    return sign;
  };

  const apply = () => {
    document.querySelectorAll(".md-content .md-typeset table").forEach((table) => {
      const headers = Array.from(table.querySelectorAll("thead th"));
      const column = headers.findIndex((th) => th.textContent.trim() === "상태");
      if (column < 0) return;
      table.querySelectorAll("tbody tr").forEach((row) => {
        const cell = row.children[column];
        if (!cell || cell.querySelector(".kb-sign")) return;
        const status = cell.textContent.trim();
        const stage = STATUS_STAGES[status];
        if (!stage) return;
        const sign = buildSign(stage);
        sign.setAttribute("aria-label", `${status}. ${sign.getAttribute("aria-label")}`);
        sign.title = status;
        cell.replaceChildren(sign);
      });
    });
  };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(apply);
  } else {
    document.addEventListener("DOMContentLoaded", apply);
  }
})();
