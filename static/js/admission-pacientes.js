(function () {
  "use strict";

  const state = {
    modo: "ver",
    seleccionadoId: null,
    resultados: [],
  };

  const el = {
    alert: document.getElementById("pacienteAlert"),
    tipoBusqueda: document.getElementById("tipoBusqueda"),
    terminoBusqueda: document.getElementById("terminoBusqueda"),
    btnBuscar: document.getElementById("btnBuscar"),
    resultadosBody: document.getElementById("resultadosBody"),
    form: document.getElementById("formPaciente"),
    pacienteId: document.getElementById("pacienteId"),
    nombreCompleto: document.getElementById("nombreCompleto"),
    numeroHistoria: document.getElementById("numeroHistoria"),
    fechaNacimiento: document.getElementById("fechaNacimiento"),
    dni: document.getElementById("dni"),
    direccion: document.getElementById("direccion"),
    nombrePadre: document.getElementById("nombrePadre"),
    nombreMadre: document.getElementById("nombreMadre"),
    btnNuevo: document.getElementById("btnNuevo"),
    btnEditar: document.getElementById("btnEditar"),
    btnGrabar: document.getElementById("btnGrabar"),
    btnCancelar: document.getElementById("btnCancelar"),
    btnEliminar: document.getElementById("btnEliminar"),
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

  function showAlert(message, type) {
    el.alert.textContent = message;
    el.alert.className = "alert alert-" + type;
    el.alert.classList.remove("d-none");
  }

  function hideAlert() {
    el.alert.classList.add("d-none");
  }

  function fechaIsoADisplay(iso) {
    if (!iso) return "";
    const partes = iso.split("-");
    if (partes.length !== 3) return iso;
    return partes[2] + "/" + partes[1] + "/" + partes[0];
  }

  function fechaDisplayAIso(texto) {
    if (!texto) return "";
    const partes = texto.split("/");
    if (partes.length !== 3) return "";
    return partes[2] + "-" + partes[1].padStart(2, "0") + "-" + partes[0].padStart(2, "0");
  }

  function setFormEnabled(enabled) {
    campos.forEach(function (campo) {
      campo.disabled = !enabled;
    });
  }

  function actualizarBotones() {
    const haySeleccion = Boolean(state.seleccionadoId);
    const editando = state.modo === "nuevo" || state.modo === "editar";

    el.btnNuevo.disabled = editando;
    el.btnEditar.disabled = editando || !haySeleccion;
    el.btnGrabar.disabled = !editando;
    el.btnCancelar.disabled = !editando;
    el.btnEliminar.disabled = editando || !haySeleccion;
  }

  function limpiarFormulario() {
    el.pacienteId.value = "";
    el.nombreCompleto.value = "";
    el.numeroHistoria.value = "";
    el.fechaNacimiento.value = "";
    el.dni.value = "";
    el.direccion.value = "";
    el.nombrePadre.value = "";
    el.nombreMadre.value = "";
    state.seleccionadoId = null;
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

  function renderResultados(lista) {
    state.resultados = lista;
    if (!lista.length) {
      el.resultadosBody.innerHTML =
        '<tr class="text-muted"><td colspan="5" class="text-center py-4">No se encontraron pacientes</td></tr>';
      return;
    }

    el.resultadosBody.innerHTML = lista
      .map(function (p) {
        const selected = p.id === state.seleccionadoId ? " selected" : "";
        return (
          '<tr data-id="' +
          p.id +
          '"' +
          selected +
          ">" +
          "<td>" +
          escapeHtml(p.numero_historia_clinica) +
          "</td>" +
          "<td>" +
          escapeHtml(p.nombre_completo) +
          "</td>" +
          "<td>" +
          escapeHtml(p.dni || "-") +
          "</td>" +
          "<td>" +
          escapeHtml(p.fecha_nacimiento || "-") +
          "</td>" +
          '<td class="text-end"><button type="button" class="btn btn-sm btn-outline-primary btn-ver" data-id="' +
          p.id +
          '">Ver</button></td>' +
          "</tr>"
        );
      })
      .join("");
  }

  function escapeHtml(texto) {
    return String(texto)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function buscar() {
    hideAlert();
    const termino = el.terminoBusqueda.value.trim();
    if (termino.length < 2) {
      showAlert("Ingrese al menos 2 caracteres para buscar.", "warning");
      return;
    }

    const tipo = el.tipoBusqueda.value;
    const url =
      "/admission/pacientes/buscar?termino=" +
      encodeURIComponent(termino) +
      "&tipo=" +
      encodeURIComponent(tipo);

    try {
      const resp = await fetch(url);
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        showAlert(data.message || "Error al buscar pacientes.", "danger");
        return;
      }
      renderResultados(data.pacientes || []);
    } catch (err) {
      showAlert("No se pudo conectar con el servidor.", "danger");
    }
  }

  async function cargarPaciente(id) {
    hideAlert();
    try {
      const resp = await fetch("/admission/pacientes/" + id);
      const data = await resp.json();
      if (!resp.ok || data.status !== "success" || !data.paciente) {
        showAlert(data.message || "No se encontró el paciente.", "danger");
        return;
      }
      state.modo = "ver";
      cargarEnFormulario(data.paciente);
      setFormEnabled(false);
      actualizarBotones();
      renderResultados(state.resultados);
    } catch (err) {
      showAlert("Error al cargar el paciente.", "danger");
    }
  }

  async function grabar() {
    hideAlert();
    const payload = payloadFormulario();
    if (!payload.nombre_completo || !payload.numero_historia_clinica) {
      showAlert("Apellidos/nombres e historia clínica son obligatorios.", "warning");
      return;
    }

    const esNuevo = state.modo === "nuevo";
    const url = esNuevo
      ? "/admission/pacientes/guardar"
      : "/admission/pacientes/guardar/" + state.seleccionadoId;
    const method = esNuevo ? "POST" : "PUT";

    try {
      const resp = await fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        showAlert(data.message || "No se pudo guardar.", "danger");
        return;
      }

      state.modo = "ver";
      cargarEnFormulario(data.paciente);
      setFormEnabled(false);
      actualizarBotones();
      showAlert(esNuevo ? "Paciente registrado correctamente." : "Paciente actualizado.", "success");
      if (el.terminoBusqueda.value.trim().length >= 2) {
        buscar();
      }
    } catch (err) {
      showAlert("Error al guardar el paciente.", "danger");
    }
  }

  async function eliminarPaciente() {
    if (!state.seleccionadoId) return;
    if (!window.confirm("¿Eliminar este paciente del registro?")) return;

    hideAlert();
    try {
      const resp = await fetch("/admission/pacientes/eliminar/" + state.seleccionadoId, {
        method: "DELETE",
      });
      const data = await resp.json();
      if (!resp.ok || data.status !== "success") {
        showAlert(data.message || "No se pudo eliminar.", "danger");
        return;
      }
      limpiarFormulario();
      state.modo = "ver";
      setFormEnabled(false);
      actualizarBotones();
      showAlert("Paciente eliminado.", "success");
      if (el.terminoBusqueda.value.trim().length >= 2) {
        buscar();
      } else {
        renderResultados([]);
      }
    } catch (err) {
      showAlert("Error al eliminar.", "danger");
    }
  }

  el.btnBuscar.addEventListener("click", buscar);
  el.terminoBusqueda.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      buscar();
    }
  });

  el.resultadosBody.addEventListener("click", function (ev) {
    const row = ev.target.closest("tr[data-id]");
    if (!row) return;
    const id = row.getAttribute("data-id");
    if (id) cargarPaciente(id);
  });

  el.btnNuevo.addEventListener("click", function () {
    hideAlert();
    limpiarFormulario();
    state.modo = "nuevo";
    setFormEnabled(true);
    actualizarBotones();
    el.nombreCompleto.focus();
  });

  el.btnEditar.addEventListener("click", function () {
    if (!state.seleccionadoId) return;
    state.modo = "editar";
    setFormEnabled(true);
    actualizarBotones();
  });

  el.btnGrabar.addEventListener("click", grabar);

  el.btnCancelar.addEventListener("click", function () {
    hideAlert();
    if (state.modo === "nuevo") {
      limpiarFormulario();
    } else if (state.seleccionadoId) {
      cargarPaciente(state.seleccionadoId);
      return;
    }
    state.modo = "ver";
    setFormEnabled(false);
    actualizarBotones();
  });

  el.btnEliminar.addEventListener("click", eliminarPaciente);

  setFormEnabled(false);
  actualizarBotones();
})();
