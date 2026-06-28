from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from Aplicacion.Servicios.HistoriaService import HistoriaService
from Aplicacion.Servicios.PacienteService import PacienteService
from Aplicacion.Servicios.AuthService import AuthService
from datetime import datetime
import re

admission_bp = Blueprint('admission', __name__, url_prefix='/admission')
historia_service = HistoriaService()
paciente_service = PacienteService()
auth_service = AuthService()


def _password_policy_error(password: str):
    if len(password) < 8:
        return "La contraseña debe tener mínimo 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return "La contraseña debe incluir al menos una mayúscula."
    if not re.search(r"[a-z]", password):
        return "La contraseña debe incluir al menos una minúscula."
    if not re.search(r"[0-9]", password):
        return "La contraseña debe incluir al menos un número."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "La contraseña debe incluir al menos un carácter especial."
    return None

@admission_bp.before_request
def check_admission():
    if session.get('usuario_role') not in ['admin', 'admission']:
        return redirect(url_for('auth.login_admission'))

@admission_bp.route('/dashboard')
def dashboard():
    usuario_nombre = session.get('usuario_nombre')
    historias = historia_service.get_all_historias()
    total_historias = len(historias)
    pendientes = len([h for h in historias if h['estado'] == 'Pendiente'])
    recibidas = len([h for h in historias if h['estado'] == 'Recibido'])

    cantidades = {
        'total_historias': total_historias,
        'pendientes': pendientes,
        'recibidas': recibidas
    }

    if total_historias > 0:
        porcentaje_recibidas = round((recibidas / total_historias) * 100, 1)
        porcentaje_pendientes = round((pendientes / total_historias) * 100, 1)
    else:
        porcentaje_recibidas = 0
        porcentaje_pendientes = 0

    especialidades_totales = {}
    for historia in historias:
        especialidad = (historia.get('especialidad') or 'Sin especialidad').strip()
        if not especialidad or especialidad.upper() == 'N/A':
            especialidad = 'Sin especialidad'
        especialidades_totales[especialidad] = especialidades_totales.get(especialidad, 0) + 1

    top_especialidades = sorted(
        especialidades_totales.items(),
        key=lambda item: item[1],
        reverse=True
    )[:5]

    max_especialidad = top_especialidades[0][1] if top_especialidades else 0
    top_especialidades_chart = []
    for nombre, total in top_especialidades:
        porcentaje_barra = round((total / max_especialidad) * 100, 1) if max_especialidad > 0 else 0
        top_especialidades_chart.append({
            'nombre': nombre,
            'total': total,
            'porcentaje_barra': porcentaje_barra
        })

    return render_template('admission/dashboard.html', 
                           usuario_nombre=usuario_nombre,
                           cantidades=cantidades,
                           porcentaje_recibidas=porcentaje_recibidas,
                           porcentaje_pendientes=porcentaje_pendientes,
                           top_especialidades_chart=top_especialidades_chart,
                           active_nav='dashboard')


@admission_bp.route('/cambiar-password', methods=['GET', 'POST'])
def cambiar_password():
    usuario_id = session.get('usuario_id')
    usuario = auth_service.get_user_by_id(usuario_id) if usuario_id else None
    if not usuario:
        return redirect(url_for('auth.login_admission'))

    if request.method == 'POST':
        current_password = request.form.get('current_password') or ''
        new_password = request.form.get('new_password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not current_password or not new_password or not confirm_password:
            flash('Completa todos los campos de contraseña.', 'danger')
            return render_template('admission/change_password.html', active_nav='seguridad')

        if not auth_service.verify_password(usuario, current_password):
            flash('La contraseña actual no es correcta.', 'danger')
            return render_template('admission/change_password.html', active_nav='seguridad')

        if current_password == new_password:
            flash('La nueva contraseña debe ser diferente a la actual.', 'warning')
            return render_template('admission/change_password.html', active_nav='seguridad')

        policy_error = _password_policy_error(new_password)
        if policy_error:
            flash(policy_error, 'danger')
            return render_template('admission/change_password.html', active_nav='seguridad')

        if new_password != confirm_password:
            flash('La confirmación no coincide con la nueva contraseña.', 'danger')
            return render_template('admission/change_password.html', active_nav='seguridad')

        auth_service.change_password(usuario_id, new_password)
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('admission.cambiar_password'))

    return render_template('admission/change_password.html', active_nav='seguridad')

@admission_bp.route('/fechas')
def fechas():
    registros = historia_service.get_registros_agrupados_por_dia()

    today_str = datetime.now().strftime('%d-%m-%Y')
    especialidades = historia_service.get_especialidades()
    medicos = historia_service.get_medicos()
    especialidades_by_id = {esp.id: esp.nombre for esp in especialidades}
    medicos_dropdown = [
        {
            'id': med.id,
            'nombre': med.nombre,
            'especialidad': especialidades_by_id.get(med.especialidad_id, 'Sin especialidad')
        }
        for med in medicos
    ]
    return render_template(
        'admission/fechas.html',
        registros=registros,
        today_url=f"/admission/historias/{today_str}",
        especialidades=especialidades,
        medicos=medicos_dropdown,
        active_nav='fechas',
    )

@admission_bp.route('/historias/<fecha>')
def historias_por_fecha(fecha):
    # El parámetro fecha puede venir con '/' o '-'
    fecha_clean = fecha.replace('-', '/')
    try:
        fecha_dt = datetime.strptime(fecha_clean, '%d/%m/%Y').date()
        historias = historia_service.get_historias_por_fecha(fecha_dt)
    except Exception as e:
        print(f"Error parsing date {fecha}: {e}")
        historias = []
    
    especialidades = historia_service.get_especialidades()
    medicos = historia_service.get_medicos()
    especialidades_by_id = {esp.id: esp.nombre for esp in especialidades}
    medicos_dropdown = [
        {
            'id': med.id,
            'nombre': med.nombre,
            'especialidad': especialidades_by_id.get(med.especialidad_id, 'Sin especialidad')
        }
        for med in medicos
    ]
    responsables = historia_service.get_responsables_triaje()
    return render_template('admission/historias_fecha.html',
                           historias=historias,
                           fecha=fecha,
                           especialidades=especialidades,
                           medicos=medicos_dropdown,
                           responsables=responsables,
                           active_nav='fechas')

@admission_bp.route('/historias_json/<fecha>')
def historias_json_por_fecha(fecha):
    fecha_clean = fecha.replace('-', '/')
    try:
        fecha_dt = datetime.strptime(fecha_clean, '%d/%m/%Y').date()
        historias = historia_service.get_historias_por_fecha(fecha_dt)
        return jsonify({"status": "success", "historias": historias})
    except Exception as e:
        print(f"Error parsing date {fecha}: {e}")
        return jsonify({"status": "error", "historias": []}), 400

@admission_bp.route('/guardar', methods=['POST'])
def guardar():
    data = request.json or {}
    usuario_id = session.get('usuario_id')
    historias = data.get('historias', [])
    actualizaciones = data.get('actualizaciones', [])
    fecha_objetivo = (data.get('fecha_objetivo') or '').strip()
    fecha_registro = None

    if not usuario_id:
        return jsonify({
            "status": "error",
            "message": "Tu sesión no es válida. Inicia sesión nuevamente."
        }), 401

    if fecha_objetivo:
        try:
            fecha_solo = datetime.strptime(fecha_objetivo, '%d/%m/%Y').date()
            fecha_registro = datetime.combine(fecha_solo, datetime.now().time())
        except Exception:
            return jsonify({"status": "error", "message": "Fecha objetivo inválida"}), 400

    if not historias and not actualizaciones:
        return jsonify({"status": "error", "message": "No hay registros para guardar"}), 400

    if fecha_registro:
        fecha_dia_nuevas = fecha_registro.date()
    else:
        fecha_dia_nuevas = datetime.now().date()

    ok_dup, msg_dup = historia_service.validar_duplicados_numero_historia_mismo_dia(
        fecha_dia_nuevas, historias, actualizaciones
    )
    if not ok_dup:
        return jsonify({"status": "error", "message": msg_dup}), 400

    try:
        for item in historias:
            numero_historia = (item.get('numero_historia') or '').strip()
            medico_id = item.get('medico_id')
            turno = item.get('turno')
            responsable_nombre = (item.get('responsable_triaje') or '').strip()
            estado = (item.get('estado') or 'Pendiente').strip()

            if not numero_historia or not medico_id or not turno or not responsable_nombre:
                return jsonify({"status": "error", "message": "Todos los campos son obligatorios"}), 400

            if estado not in ['Pendiente', 'Recibido']:
                return jsonify({"status": "error", "message": "Estado inválido"}), 400

            responsable_triaje_id = historia_service.get_or_create_responsable_id(responsable_nombre)
            historia_service.registrar_historia(
                numero_historia=numero_historia,
                medico_id=int(medico_id),
                turno=turno,
                responsable_triaje_id=responsable_triaje_id,
                usuario_registro_id=usuario_id,
                fecha_registro=fecha_registro,
                estado=estado
            )

        for item in actualizaciones:
            historia_id = item.get('id')
            numero_historia = (item.get('numero_historia') or '').strip()
            medico_id = item.get('medico_id')
            turno = item.get('turno')
            responsable_nombre = (item.get('responsable_triaje') or '').strip()
            estado = item.get('estado')

            if not historia_id or not numero_historia or not medico_id or not turno or not responsable_nombre or not estado:
                return jsonify({"status": "error", "message": "Datos incompletos para actualizar"}), 400

            responsable_triaje_id = historia_service.get_or_create_responsable_id(responsable_nombre)
            updated = historia_service.actualizar_historia(
                historia_id=int(historia_id),
                numero_historia=numero_historia,
                medico_id=int(medico_id),
                turno=turno,
                responsable_triaje_id=responsable_triaje_id,
                estado=estado
            )
            if not updated:
                return jsonify({"status": "error", "message": f"No se pudo actualizar la historia {historia_id}"}), 400
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        print(f"Error guardando historias: {exc}")
        return jsonify({"status": "error", "message": "Ocurrió un error al guardar las historias"}), 500

    return jsonify({"status": "success", "redirect_url": url_for('admission.fechas')})

@admission_bp.route('/cambiar_estado', methods=['POST'])
def cambiar_estado():
    data = request.json or {}
    historia_id = data.get('historia_id')
    nuevo_estado = data.get('estado')
    if not historia_id or not nuevo_estado:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400
    result = historia_service.cambiar_estado(historia_id, nuevo_estado)
    return jsonify({"status": "success" if result else "error"})

@admission_bp.route('/eliminar_historia', methods=['POST'])
def eliminar_historia():
    data = request.json or {}
    historia_id = data.get('historia_id')
    if not historia_id:
        return jsonify({"status": "error", "message": "Id de historia requerido"}), 400

    result = historia_service.eliminar_historia(int(historia_id))
    return jsonify({"status": "success" if result else "error"})


@admission_bp.route('/pacientes')
def pacientes():
    try:
        total = paciente_service.contar()
    except Exception:
        total = 0
    return render_template(
        'admission/pacientes.html',
        total_pacientes=total,
        active_nav='historias_clinicas',
    )


@admission_bp.route('/pacientes/buscar')
def pacientes_buscar():
    termino = (request.args.get('termino') or '').strip()
    tipo = (request.args.get('tipo') or 'nombre').strip().lower()
    if len(termino) < 2:
        return jsonify({
            "status": "error",
            "message": "Ingrese al menos 2 caracteres.",
            "pacientes": [],
        }), 400
    try:
        resultados = paciente_service.buscar(termino, tipo=tipo)
        return jsonify({"status": "success", "pacientes": resultados})
    except Exception as exc:
        print(f"Error buscando pacientes: {exc}")
        return jsonify({
            "status": "error",
            "message": "Error al buscar pacientes.",
            "pacientes": [],
        }), 500


@admission_bp.route('/pacientes/<int:paciente_id>')
def pacientes_obtener(paciente_id):
    paciente = paciente_service.obtener(paciente_id)
    if not paciente:
        return jsonify({"status": "error", "message": "Paciente no encontrado."}), 404
    return jsonify({"status": "success", "paciente": paciente})


@admission_bp.route('/pacientes/guardar', methods=['POST'])
def pacientes_crear():
    data = request.json or {}
    try:
        paciente = paciente_service.crear(data)
        return jsonify({"status": "success", "paciente": paciente})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        print(f"Error creando paciente: {exc}")
        return jsonify({"status": "error", "message": "No se pudo crear el paciente."}), 500


@admission_bp.route('/pacientes/guardar/<int:paciente_id>', methods=['PUT'])
def pacientes_actualizar(paciente_id):
    data = request.json or {}
    try:
        paciente = paciente_service.actualizar(paciente_id, data)
        if not paciente:
            return jsonify({"status": "error", "message": "Paciente no encontrado."}), 404
        return jsonify({"status": "success", "paciente": paciente})
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        print(f"Error actualizando paciente: {exc}")
        return jsonify({"status": "error", "message": "No se pudo actualizar el paciente."}), 500


@admission_bp.route('/pacientes/eliminar/<int:paciente_id>', methods=['DELETE'])
def pacientes_eliminar(paciente_id):
    try:
        ok = paciente_service.eliminar(paciente_id)
        if not ok:
            return jsonify({"status": "error", "message": "Paciente no encontrado."}), 404
        return jsonify({"status": "success"})
    except Exception as exc:
        print(f"Error eliminando paciente: {exc}")
        return jsonify({"status": "error", "message": "No se pudo eliminar el paciente."}), 500
