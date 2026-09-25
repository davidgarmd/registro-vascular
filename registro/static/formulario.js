// Muestra u oculta los campos según sus condiciones (atributo data-si).
// Los campos ocultos se desactivan para que no se envíen; el servidor
// aplica las mismas reglas al validar.
(function () {
  const form = document.querySelector("form.formulario");
  if (!form) return;
  const campos = Array.from(form.querySelectorAll(".campo[data-nombre]"));

  function valores(nombre) {
    const inputs = form.querySelectorAll(`[name="${CSS.escape(nombre)}"]`);
    const out = [];
    inputs.forEach((el) => {
      if (el.disabled) return;
      if (el.type === "radio" || el.type === "checkbox") {
        if (el.checked) out.push(el.value);
      } else if (el.value !== "") {
        out.push(el.value);
      }
    });
    return out;
  }

  function cumple(cond) {
    const v = valores(cond.campo);
    if (v.length === 0) return false;
    if (cond.valores && !v.some((x) => cond.valores.includes(x))) return false;
    if (cond.excepto && v.every((x) => cond.excepto.includes(x))) return false;
    return true;
  }

  function actualizar() {
    // En orden: una condición solo depende de campos anteriores.
    campos.forEach((div) => {
      const si = div.dataset.si;
      if (!si) return;
      let conds = JSON.parse(si);
      if (!Array.isArray(conds)) conds = [conds];
      const ver = conds.every(cumple);
      div.hidden = !ver;
      div.querySelectorAll("input, select, textarea").forEach((el) => (el.disabled = !ver));
    });
  }

  // "Ninguno/Ninguna" excluye al resto de opciones en las casillas múltiples.
  form.addEventListener("change", (e) => {
    const el = e.target;
    if (el.type === "checkbox" && el.checked) {
      const grupo = form.querySelectorAll(`input[type=checkbox][name="${CSS.escape(el.name)}"]`);
      const exclusivo = (v) => /^(Ninguno|Ninguna|No aplica)$/.test(v);
      grupo.forEach((otro) => {
        if (otro !== el && (exclusivo(el.value) || exclusivo(otro.value))) otro.checked = false;
      });
    }
    actualizar();
  });
  form.addEventListener("input", actualizar);

  // Permite desmarcar un radio pulsándolo de nuevo (campos no obligatorios).
  form.querySelectorAll("input[type=radio]").forEach((r) => {
    r.addEventListener("mousedown", () => (r.dataset.estaba = r.checked ? "1" : ""));
    r.addEventListener("click", () => {
      if (r.dataset.estaba) { r.checked = false; actualizar(); }
    });
  });

  actualizar();
})();
