// Muestra u oculta los campos según sus condiciones (atributo data-si).
// Los campos ocultos se desactivan para que no se envíen; el servidor
// aplica las mismas reglas al validar.
(function () {
  const form = document.querySelector("form.formulario");
  if (!form) return;
  const campos = Array.from(form.querySelectorAll(".campo[data-nombre]"));

  function valores(nombre) {
    const inputs = form.querySelectorAll(`[name="${CSS.escape(nombre)}"]`);  // los campos condicionantes nunca son de dispositivos
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

  // Campos calculados (estadios WIfI y GLASS, totales de Villalta y VCSS, código SVP).
  // Misma lógica que formularios.calcular en el servidor.
  const clave = (v) => (v || "").split(" ")[0];
  function codigoSvp(val) {
    const s = val("svp_s"), v = val("svp_v"), seg = val("svp_anatomia"), et = val("svp_etiologia")[0];
    if (!s.length || !v.length) return null;
    let codigo = "S" + s.map((x) => x.slice(1)).join(",") + " V" + v.map((x) => x.slice(1)).join(",");
    if (seg.length && et && seg.every((x) => val("svp_h_" + x).length)) {
      codigo += " P " + seg.map((x) => `${x},${val("svp_h_" + x)[0]},${et}`).join("; ");
    }
    return codigo;
  }
  function calcular() {
    const calculados = {};
    const val = (n) => (n in calculados ? [String(calculados[n])] : valores(n));
    form.querySelectorAll("output[data-calculado]").forEach((out) => {
      const regla = JSON.parse(out.dataset.calculado);
      const campo = out.closest(".campo");
      let resultado = null;
      if (!campo.hidden) {
        if (regla.suma) {
          const claves = regla.suma.map((n) => clave(val(n)[0]));
          if (claves.every((k) => /^\d+$/.test(k))) resultado = claves.reduce((a, k) => a + Number(k), 0);
        } else if (regla.svp) {
          resultado = codigoSvp(val);
        } else {
          const claves = regla.entradas.map((n) => clave(val(n)[0]));
          if (claves.every(Boolean)) {
            if (regla.rangos) {
              const f = regla.forzar;
              if (f && val(f.campo)[0] === f.valor) resultado = f.texto;
              else {
                const fila = regla.rangos.find(([hasta]) => Number(claves[0]) <= hasta);
                resultado = fila ? fila[1] : null;
              }
            } else {
              resultado = regla.tabla[claves.join("|")] || null;
            }
          }
        }
      }
      if (resultado !== null) calculados[campo.dataset.nombre] = resultado;
      out.textContent = resultado !== null ? resultado : "Se calcula al completar los campos anteriores";
      out.classList.toggle("listo", resultado !== null);
    });
  }

  // Texto completo de la opción elegida en las escalas (el desplegable cerrado lo recorta).
  function descripciones() {
    form.querySelectorAll("small.desc-elegida").forEach((el) => {
      const sel = el.previousElementSibling;
      const texto = sel.selectedIndex > 0 ? sel.options[sel.selectedIndex].textContent : "";
      el.textContent = texto.includes(" · ") && texto.length > 40 ? texto : "";
    });
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
    calcular();
    descripciones();
  }

  // Filas de dispositivos (material con medidas).
  form.addEventListener("click", (e) => {
    const anadir = e.target.closest(".anadir-dispositivo");
    if (anadir) {
      const caja = anadir.parentElement.querySelector(".dispositivos");
      caja.appendChild(caja.querySelector("template").content.cloneNode(true));
      caja.lastElementChild.querySelector("select").focus();
      actualizar();
    }
    const quitar = e.target.closest(".quitar-dispositivo");
    if (quitar) quitar.closest(".disp-fila").remove();
  });

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
