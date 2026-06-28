(function () {
  "use strict";

  const PLACEHOLDERS = {
    nombre: "Apellidos y nombres del paciente...",
    dni: "Número de DNI (mín. 2 dígitos)...",
    historia: "Número de historia clínica...",
  };

  const TIPO_LABELS = {
    nombre: "por nombre",
    dni: "por DNI",
    historia: "por historia clínica",
  };

  const state = {
    modo: "idle",
    tipoBusqueda: "nombre",
    seleccionadoId: null,
    resultados: [],
    dirty: false,
    buscando: false,
    debounceTimer: null,
  };

  const el = {
    terminoBusqueda: document.getElementById("terminoBusqueda"),
    btnBuscar: document.getElementById("btnBuscar"),
    btnLimpiar: document.getElementById("btnLimpiarBusqueda"),
    resultadosLista: document.getElementById("resultadosLista"),
    resultadosContador: document.getElementById("resultadosContador"),
    resultadosTipo: document.getElementById("resultadosTipo"),
    detalleVacio: document.getElementById("detalleVacio"),
    detalleContenido: document.getElementById("detalleContenido"),
    modoBadge: document.getElementById("modoBadge"),
    profileAvatar: document.getElementById("profileAvatar"),
    profileName: document.getElementById("profileName"),
    profileMeta: document.getElementById("profileMeta"),
    toastWrap: document.getElementById("toastWrap"),
    pacienteId: document.getElementById("pacienteId"),
    nombreCompleto: document.getElementById("nombreCompleto"),
    numeroHistoria: document.getElementById("numeroHistoria"),
    fechaNacimiento: document.getElementById("fechaNacimiento"),
    dni: document.getElementById("dni"),
    direccion: document.getElementById("direccion"),
    nombrePadre: document.getElementById("nombrePadre"),
    nombreMadre: document.getElementById("nombreMadre"),
    btnEditar: document.getElementById("btnEditar"),
    btnGrabar: document.getElementById("btnGrabar"),
    btnCancelar: document.getElementById("btnCancelar"),
    btnEliminar: document.getElementById("btnEliminar"),
    btnNuevoTop: document.getElementById("btnNuevoTop"),
    btnNuevoEmpty: document.getElementById("btnNuevoEmpty"),
    modalEliminar: document.getElementById("modalEliminar"),
    modalEliminarNombre: document.getElementById("modalEliminarNombre"),
    btnConfirmarEliminar: document.getElementById("btnConfirmarEliminar"),
    typeBtns: document.querySelectorAll(".hc-type-btn"),
  };

  const campos = [
    el.nombreCompleto,
    el.numeroHistoria,
    el.fechaNacimiento,
    el.dni,
    el.direccion,
    el.nombrePadre,
    el.nombreMadre,
  ];

  const modalEliminar = el.modalEliminar
    ? new bootstrap.Modal(el.modalEliminar)
    : null;

  function escapeHtml(texto) {
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function iniciales(nombre) {
    const partes = (nombre || "").trim().split(/\s+/).filter(Boolean);
    if (!partes.length) return "?";
    if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
    return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
  }

  function fechaIsoADisplay(iso) {
    if (!iso) return "";
    const p = iso.split("-");
    if (p.length !== 3) return iso;
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  function fechaDisplayAIso(texto) {
    if (!texto) return "";
    const p = texto.split("/");
    if (p.length !== 3) return "";
    return p[2] + "-" + p[1].padStart(2, "0") + "-" + p[0].padStart(2, "0");
  }

  function toast(message, type) {
    const icons = { success: "bi-check-circle-fill", warning: "bi-exclamation-triangle-fill", danger: "bi-x-circle-fill" };
    const node = document.createElement("div");
    node.className = "hc-toast hc-toast--" + (type || "success");
    node.innerHTML =
      '<i class="bi ' + (icons[type] || icons.success) + ' hc-toast-icon"></i>' +
      '<span class="hc-toast-text">' + escapeHtml(message) + "</span>";
    el.toastWrap.appendChild(node);
    setTimeout(function () {
      node.style.opacity = "0";
      node.style.transition = "opacity 0.2s";
      setTimeout(function () { node.remove(); }, 220);
    }, 4200);
  }

  function setDirty(value) {
    state.dirty = value;
  }

  function setFormEnabled(enabled) {
    campos.forEach(function (c) { c.disabled = !enabled; });
  }

  function limpiarValidacion() {
    campos.forEach(function (c) { c.classList.remove("is-invalid"); });
  }

  function validarFormulario() {
    limpiarValidacion();
    let ok = true;
    if (!el.nombreCompleto.value.trim()) {
      el.nombreCompleto.classList.add("is-invalid");
      ok = false;
    }
    if (!el.numeroHistoria.value.trim()) {
      el.numeroHistoria.classList.add("is-invalid");
      ok = false;
    }
    return ok;
  }

  function actualizarModoUI() {
    const editando = state.modo === "nuevo" || state.modo === "editar";
    const hayPaciente = Boolean(state.seleccionadoId) || state.modo === "nuevo";

    el.detalleVacio.classList.toggle("d-none", hayPaciente);
    el.detalleContenido.classList.toggle("d-none", !hayPaciente);

    el.modoBadge.classList.remove("d-none", "hc-mode-badge--view", "hc-mode-badge--edit", "hc-mode-badge--new");
    if (state.modo === "nuevo") {
      el.modoBadge.textContent = "Nuevo registro";
      el.modoBadge.classList.add("hc-mode-badge--new");
    } else if (state.modo === "editar") {
      el.modoBadge.textContent = "Editando";
      el.modoBadge.classList.add("hc-mode-badge--edit");
    } else if (state.seleccionadoId) {
      el.modoBadge.textContent = "Consulta";
      el.modoBadge.classList.add("hc-mode-badge--view");
    } else {
      el.modoBadge.classList.add("d-none");
    }

    el.btnEditar.disabled = editando || !state.seleccionadoId;
    el.btnGrabar.disabled = !editando;
    el.btnCancelar.disabled = !editando;
    el.btnEliminar.disabled = editando || !state.seleccionadoId;
  }

  function actualizarProfileHeader(paciente) {
    const nombre = paciente ? paciente.nombre_completo : "";
    const hc = paciente ? paciente.numero_historia_clinica : "";
    const dni = paciente && paciente.dni ? paciente.dni : "Sin DNI";
    el.profileAvatar.textContent = iniciales(nombre);
    el.profileName.textContent = nombre || "Nuevo paciente";
    el.profileMeta.textContent = paciente
      ? "HC " + hc + " · DNI " + dni
      : "Complete los datos del registro";
  }

  function limpiarFormulario() {
    el.pacienteId.value = "";
    campos.forEach(function (c) { c.value = ""; });
    state.seleccionadoId = null;
    setDirty(false);
    limpiarValidacion();
    actualizarProfileHeader(null);
  }

  function cargarEnFormulario(paciente) {
    el.pacienteId.value = paciente.id || "";
    el.nombreCompleto.value = paciente.nombre_completo || "";
    el.numeroHistoria.value = paciente.numero_historia_clinica || "";
    el.fechaNacimiento.value = fechaDisplayAIso(paciente.fecha_nacimiento || "");
    el.dni.value = paciente.dni || "";
    el.direccion.value = paciente.direccion || "";
    el.nombrePadre.value = paciente.nombre_padre || "";
    el.nombreMadre.value = paciente.nombre_madre || "";
    state.seleccionadoId = paciente.id || null;
    setDirty(false);
    limpiarValidacion();
    actualizarProfileHeader(paciente);
  }

  function payloadFormulario() {
    return {
      nombre_completo: el.nombreCompleto.value.trim(),
      numero_historia_clinica: el.numeroHistoria.value.trim(),
      fecha_nacimiento: fechaIsoADisplay(el.fechaNacimiento.value),
      dni: el.dni.value.trim(),
      direccion: el.direccion.value.trim(),
      nombre_padre: el.nombrePadre.value.trim(),
      nombre_madre: el.nombreMadre.value.trim(),
    };
  }

  function renderLoading() {
    el.resultadosLista.innerHTML =
      '<div class="hc-loading"><div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>Buscando...</div>';
  }

  function renderEmpty(mensaje, icono) {
    el.resultadosLista.innerHTML =
      '<div class="hc-empty-state"><i class="bi ' + (icono || "bi-inbox") + '"></i><p>' +
      escapeHtml(mensaje) + "</p></div>";
  }

  function renderResultados(lista) {
    state.resultados = lista;
    el.resultadosContador.textContent = lista.length
      ? lista.length + (lista.length === 1 ? " resultado" : " resultados")
      : "Sin coincidencias";
    el.resultadosTipo.textContent = lista.length ? " " + TIPO_LABELS[state.tipoBusqueda] : "";

    if (!lista.length) {
      renderEmpty("No se encontraron pacientes con ese criterio", "bi-search");
      return;
    }

    el.resultadosLista.innerHTML = lista
      .map(function (p) {
        const sel = p.id === state.seleccionadoId ? " selected" : "";
        const sub = [
          p.dni ? "DNI " + p.dni : null,
          p.fecha_nacimiento || null,
        ].filter(Boolean).join(" · ") || "Sin datos adicionales";
        return (
          '<div class="hc-result-item' + sel + '" data-id="' + p.id + '" role="option" aria-selected="' +
          (p.id === state.seleccionadoId) + '">' +
          '<div class="hc-result-avatar">' + escapeHtml(iniciales(p.nombre_completo)) + "</div>" +
          '<div><p class="hc-result-name">' + escapeHtml(p.nombre_completo) + "</p>" +
          '<p class="hc-result-sub">' + escapeHtml(sub) + "</p></div>" +
          '<span class="hc-result-badge">HC ' + escapeHtml(p.numero_historia_clinica) + "</span>" +
          "</div>"
        );
      })
      .join("");
  }

  function toggleClearBtn() {
    el.btnLimpiar.classList.toggle("d-none", !el.terminoBusqueda.value.trim());
  }

  async function buscar() {
    const termino = el.terminoBusqueda.value.trim();
    if (termino.length < 2) {
      el.resultadosContador.textContent = "Escriba al menos 2 caracteres";
      el.resultadosTipo.textContent = "";
      renderEmpty("Los resultados aparecerán aquí", "bi-inbox");
      return;
    }

    if (state.buscando) return;
    state.buscando = true;
    renderLoading();

    const url =
      "/admission/pacientes/buscar?termino=" +
      encodeURIComponent(termino) +
      "&tipo=" +
      encodeURIComponent(state.tipoBusqueda);

    try {
      const resp = await fetch(url);
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        toast(data.message || "Error al buscar.", "danger");
        renderEmpty("Error en la búsqueda", "bi-exclamation-circle");
        return;
      }
      renderResultados(data.pacientes || []);
      if ((data.pacientes || []).length === 1) {
        cargarPaciente(data.pacientes[0].id, false);
      }
    } catch (err) {
      toast("No se pudo conectar con el servidor.", "danger");
      renderEmpty("Error de conexión", "bi-wifi-off");
    } finally {
      state.buscando = false;
    }
  }

  function programarBusqueda() {
    clearTimeout(state.debounceTimer);
    toggleClearBtn();
    const termino = el.terminoBusqueda.value.trim();
    if (termino.length < 2) {
      el.resultadosContador.textContent = "Escriba al menos 2 caracteres";
      el.resultadosTipo.textContent = "";
      return;
    }
    state.debounceTimer = setTimeout(buscar, 450);
  }

  async function cargarPaciente(id, scrollDetail) {
    try {
      const resp = await fetch("/admission/pacientes/" + id);
      const data = await resp.json();
      if (!resp.ok || data.status !== "success" || !data.paciente) {
        toast(data.message || "Paciente no encontrado.", "danger");
        return;
      }
      state.modo = "ver";
      cargarEnFormulario(data.paciente);
      setFormEnabled(false);
      actualizarModoUI();
      renderResultados(state.resultados);
      if (scrollDetail && window.matchMedia("(max-width: 991px)").matches) {
        el.detalleContenido.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (err) {
      toast("Error al cargar el paciente.", "danger");
    }
  }

  function iniciarNuevo() {
    if (state.dirty && !confirm("Hay cambios sin guardar. ¿Desea descartarlos?")) return;
    limpiarFormulario();
    state.modo = "nuevo";
    setFormEnabled(true);
    actualizarModoUI();
    actualizarProfileHeader(null);
    el.nombreCompleto.focus();
  }

  async function grabar() {
    if (!validarFormulario()) {
      toast("Complete los campos obligatorios.", "warning");
      return;
    }

    const payload = payloadFormulario();
    const esNuevo = state.modo === "nuevo";
    const url = esNuevo
      ? "/admission/pacientes/guardar"
      : "/admission/pacientes/guardar/" + state.seleccionadoId;

    el.btnGrabar.disabled = true;
    try {
      const resp = await fetch(url, {
        method: esNuevo ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        toast(data.message || "No se pudo guardar.", "danger");
        return;
      }
      state.modo = "ver";
      cargarEnFormulario(data.paciente);
      setFormEnabled(false);
      actualizarModoUI();
      toast(esNuevo ? "Paciente registrado correctamente." : "Cambios guardados.", "success");
      if (el.terminoBusqueda.value.trim().length >= 2) {
        await buscar();
      }
    } catch (err) {
      toast("Error al guardar.", "danger");
    } finally {
      el.btnGrabar.disabled = false;
      actualizarModoUI();
    }
  }

  function solicitarEliminar() {
    if (!state.seleccionadoId) return;
    el.modalEliminarNombre.textContent = el.nombreCompleto.value.trim() || "este paciente";
    modalEliminar.show();
  }

  async function confirmarEliminar() {
    if (!state.seleccionadoId) return;
    modalEliminar.hide();
    try {
      const resp = await fetch("/admission/pacientes/eliminar/" + state.seleccionadoId, {
        method: "DELETE",
      });
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        toast(data.message || "No se pudo eliminar.", "danger");
        return;
      }
      limpiarFormulario();
      state.modo = "idle";
      setFormEnabled(false);
      actualizarModoUI();
      toast("Paciente eliminado del registro.", "success");
      if (el.terminoBusqueda.value.trim().length >= 2) {
        await buscar();
      } else {
        renderEmpty("Los resultados aparecerán aquí", "bi-inbox");
      }
    } catch (err) {
      toast("Error al eliminar.", "danger");
    }
  }

  function cancelarEdicion() {
    if (state.dirty && !confirm("¿Descartar los cambios?")) return;
    if (state.modo === "nuevo") {
      limpiarFormulario();
      state.modo = "idle";
      setFormEnabled(false);
      actualizarModoUI();
      return;
    }
    if (state.seleccionadoId) {
      cargarPaciente(state.seleccionadoId, false);
      return;
    }
    state.modo = "idle";
    setFormEnabled(false);
    actualizarModoUI();
  }

  function cambiarTipo(tipo) {
    state.tipoBusqueda = tipo;
    el.typeBtns.forEach(function (btn) {
      const active = btn.getAttribute("data-tipo") === tipo;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    el.terminoBusqueda.placeholder = PLACEHOLDERS[tipo] || PLACEHOLDERS.nombre;
    if (el.terminoBusqueda.value.trim().length >= 2) {
      buscar();
    }
  }

  function limpiarBusqueda() {
    el.terminoBusqueda.value = "";
    toggleClearBtn();
    el.resultadosContador.textContent = "Escriba al menos 2 caracteres";
    el.resultadosTipo.textContent = "";
    renderEmpty("Los resultados aparecerán aquí", "bi-inbox");
    el.terminoBusqueda.focus();
  }

  el.typeBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      cambiarTipo(btn.getAttribute("data-tipo"));
    });
  });

  el.btnBuscar.addEventListener("click", buscar);
  el.terminoBusqueda.addEventListener("input", programarBusqueda);
  el.terminoBusqueda.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      clearTimeout(state.debounceTimer);
      buscar();
    }
  });
  el.btnLimpiar.addEventListener("click", limpiarBusqueda);

  el.resultadosLista.addEventListener("click", function (ev) {
    const item = ev.target.closest(".hc-result-item[data-id]");
    if (!item) return;
    const id = item.getAttribute("data-id");
    if (state.dirty && state.modo !== "ver") {
      if (!confirm("Hay cambios sin guardar. ¿Continuar?")) return;
    }
    if (id) cargarPaciente(id, true);
  });

  el.btnNuevoTop.addEventListener("click", iniciarNuevo);
  el.btnNuevoEmpty.addEventListener("click", iniciarNuevo);

  el.btnEditar.addEventListener("click", function () {
    if (!state.seleccionadoId) return;
    state.modo = "editar";
    setFormEnabled(true);
    actualizarModoUI();
    el.nombreCompleto.focus();
  });

  el.btnGrabar.addEventListener("click", grabar);
  el.btnCancelar.addEventListener("click", cancelarEdicion);
  el.btnEliminar.addEventListener("click", solicitarEliminar);
  el.btnConfirmarEliminar.addEventListener("click", confirmarEliminar);

  campos.forEach(function (campo) {
    campo.addEventListener("input", function () {
      if (!campo.disabled) setDirty(true);
      campo.classList.remove("is-invalid");
    });
  });

  el.terminoBusqueda.focus();
  actualizarModoUI();
})();
