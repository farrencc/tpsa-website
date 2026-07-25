import { replayAnimation } from "./lib/observe.js";

/* Team: the triquetra's three loops and the list beneath it both select a
   group; cards open a detail modal. Group colour comes from --group, set per
   [data-group] in css/team.css. */
export function initTeam() {
  const section = document.getElementById("team");
  if (!section) return;
  const loops = [...section.querySelectorAll(".triq__loop")];
  const picks = [...section.querySelectorAll(".team__pick")];
  const grids = [...section.querySelectorAll(".team__grid")];
  const intakes = [...section.querySelectorAll(".intake--sep")];

  const select = (id) => {
    loops.forEach((l) => {
      const on = l.dataset.group === id;
      l.classList.toggle("is-active", on);
      l.setAttribute("aria-selected", String(on));
    });
    picks.forEach((p) => {
      const on = p.dataset.group === id;
      p.classList.toggle("is-active", on);
      p.setAttribute("aria-pressed", String(on));
    });
    grids.forEach((g) => {
      const on = g.dataset.group === id;
      g.classList.toggle("is-active", on);
      if (on) replayAnimation(g, "is-active"); // restart the card stagger
    });
    intakes.forEach((i) => i.classList.toggle("is-active", i.dataset.group === id));
  };

  loops.forEach((l) => {
    l.addEventListener("click", () => select(l.dataset.group));
    l.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(l.dataset.group); }
    });
  });
  picks.forEach((p) => p.addEventListener("click", () => select(p.dataset.group)));

  initModal(section);
}

function initModal(section) {
  let modal = null;
  const email = "problemsolving@tpsa.ie";

  const close = () => {
    modal?.remove();
    modal = null;
    document.body.style.overflow = "";
  };

  const open = (card) => {
    const group = card.closest("[data-group]").dataset.group;
    const name = card.querySelector("h3").textContent;
    const role = card.querySelector(".tm__role").textContent;
    const bio = card.dataset.bio;
    const photo = card.querySelector("img").getAttribute("src");
    const first = name.split(" ")[0];

    modal = document.createElement("div");
    modal.className = "tmodal";
    modal.innerHTML = `
      <div class="tmodal__card" role="dialog" aria-modal="true" data-group="${group}">
        <button class="tmodal__close" aria-label="Close">✕</button>
        <div class="tmodal__photo"><img alt=""></div>
        <div class="tmodal__info">
          <h3></h3>
          <div class="tmodal__role"></div>
          <p></p>
          <a class="btn btn--primary"></a>
        </div>
      </div>`;
    // set text via the DOM rather than the template, so names and bios cannot
    // be interpreted as markup
    const card2 = modal.querySelector(".tmodal__card");
    card2.setAttribute("aria-label", name);
    modal.querySelector(".tmodal__photo img").src = photo;
    modal.querySelector(".tmodal__photo img").alt = name;
    modal.querySelector(".tmodal__info h3").textContent = name;
    modal.querySelector(".tmodal__role").textContent = role;
    modal.querySelector(".tmodal__info p").textContent = bio;
    const mail = modal.querySelector(".tmodal__info .btn");
    mail.textContent = `✉ Email ${first}`;
    mail.href = `mailto:${email}?subject=${encodeURIComponent("For " + name)}`;

    modal.addEventListener("click", close);
    card2.addEventListener("click", (e) => e.stopPropagation());
    modal.querySelector(".tmodal__close").addEventListener("click", close);

    document.body.appendChild(modal);
    document.body.style.overflow = "hidden";
    modal.querySelector(".tmodal__close").focus();
  };

  section.querySelectorAll(".tm").forEach((card) => card.addEventListener("click", () => open(card)));
  window.addEventListener("keydown", (e) => { if (e.key === "Escape" && modal) close(); });
}
