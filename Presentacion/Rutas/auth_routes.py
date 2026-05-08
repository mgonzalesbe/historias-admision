import re
import secrets
import logging
import time

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from Aplicacion.Servicios.AuthService import AuthService
from Aplicacion.Servicios.HistoriaService import HistoriaService
from Aplicacion.Servicios.NotificationService import NotificationService, NotificationConfigError
from Aplicacion.Servicios.TokenService import TokenService
from Aplicacion.Servicios.SolanaBlockchainService import (
    SolanaBlockchainService,
    BlockchainConfigError,
    BlockchainWriteError,
)
from Persistencia.Repositorios.PasswordMetricRepository import PasswordMetricRepository
from Persistencia.Repositorios.PasswordResetTokenRepository import PasswordResetTokenRepository
from Presentacion.sesion_cache import redirect_al_panel_si_hay_sesion

auth_bp = Blueprint('auth', __name__)
_logger = logging.getLogger(__name__)
historia_service = HistoriaService()
auth_service = AuthService()
token_service = TokenService()
password_metric_repo = PasswordMetricRepository()
password_reset_repo = PasswordResetTokenRepository()
notification_service = NotificationService()


def _register_context(token, **kwargs):
    context = {
        "token": token,
        "nombre": kwargs.get("nombre", ""),
        "username": kwargs.get("username", ""),
        "notification_method": kwargs.get("notification_method", "email"),
        "notification_target": kwargs.get("notification_target", ""),
        "password_input": kwargs.get("password_input", ""),
        "error": kwargs.get("error"),
        "success": kwargs.get("success"),
        "tx_signature": kwargs.get("tx_signature"),
        "notification_info": kwargs.get("notification_info", []),
    }
    return context


def _password_strength_label(password: str) -> str:
    if _password_policy_error(password) is None:
        return "Fuerte"

    has_length = len(password) >= 8
    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"[0-9]", password))
    has_special = bool(re.search(r"[^A-Za-z0-9]", password))
    score = sum([has_length, has_upper, has_lower, has_digit, has_special])
    if len(password) >= 12:
        score += 1
    if score >= 5:
        return "Fuerte"
    if score >= 3:
        return "Regular"
    return "Fragil"


def _password_policy_error(password: str) -> str | None:
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


def _email_is_valid(email: str) -> bool:
    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            email or "",
        )
    )


def _password_page_context(**kwargs):
    return {
        "identifier": kwargs.get("identifier", ""),
        "error": kwargs.get("error"),
        "success": kwargs.get("success"),
    }


@auth_bp.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'GET':
        ya = redirect_al_panel_si_hay_sesion()
        if ya is not None:
            return ya
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usuario = auth_service.login(username, password)
        if usuario and usuario.role == 'admin':
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre_completo
            session['usuario_role'] = usuario.role
            return redirect(url_for('admin.dashboard'), code=303)
        return render_template('auth/login_admin.html', error='Credenciales inválidas')
    return render_template('auth/login_admin.html')

@auth_bp.route('/login/admission', methods=['GET', 'POST'])
def login_admission():
    if request.method == 'GET':
        ya = redirect_al_panel_si_hay_sesion()
        if ya is not None:
            return ya
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        usuario = auth_service.login(username, password)
        if usuario and usuario.role == 'admission':
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre_completo
            session['usuario_role'] = usuario.role
            return redirect(url_for('admission.dashboard'), code=303)
        return render_template('auth/login_admission.html', error='Credenciales inválidas')
    return render_template('auth/login_admission.html')

@auth_bp.route('/registro/<token>', methods=['GET', 'POST'])
def register_with_token(token):
    if not token_service.validate_token(token):
        return render_template('auth/token_invalid.html', message='El enlace ha expirado o ya fue utilizado.')

    if request.method == 'POST':
        start_ts = time.perf_counter()
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        nombre_completo = (request.form.get('nombre_completo') or '').strip()
        notification_target = (request.form.get('notification_target') or '').strip()
        generation_time_ms_raw = (request.form.get('generation_time_ms') or '0').strip()

        if not username or not nombre_completo or not password:
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            print(
                f"[INFO] auth.register_with_token finished user_id={user_id} elapsed_ms={elapsed_ms} warnings=0",
                flush=True,
            )
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error='Completa todos los campos requeridos.',
                ),
            )

        if not notification_target or not _email_is_valid(notification_target):
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error='Debes ingresar un correo electrónico válido para el envío.',
                ),
            )
        policy_error = _password_policy_error(password)
        if policy_error:
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error=policy_error,
                ),
            )

        try:
            generation_time_ms = max(int(generation_time_ms_raw), 0)
        except ValueError:
            generation_time_ms = 0

        existing = auth_service.usuario_repo.get_by_username(username)
        if existing:
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error='El nombre de usuario ya existe.',
                ),
            )

        try:
            blockchain_service = SolanaBlockchainService()
            email_to_store = notification_target
            user_id, tx_signature, _, _ = auth_service.create_user_with_blockchain(
                username=username,
                password=password,
                nombre_completo=nombre_completo,
                role='admission',
                blockchain_service=blockchain_service,
                email=email_to_store,
            )
            if user_id is None:
                raise ValueError("No se pudo crear el usuario correctamente (IdUsuario nulo).")
            password_metric_repo.create(
                usuario_id=user_id,
                password_length=len(password),
                generation_time_ms=generation_time_ms,
                strength_label=_password_strength_label(password),
            )
            token_service.use_token(token)
            _logger.info(
                "auth.register_with_token: usuario creado user_id=%s username=%s mail_domain=%s",
                user_id,
                username,
                notification_target.split("@")[-1].lower() if "@" in notification_target else "",
            )
            print(
                f"[INFO] auth.register_with_token created_db user_id={user_id} username={username}",
                flush=True,
            )

            notification_info = []
            try:
                notification_service.send_email_credentials(notification_target, username, password)
                notification_info.append("Credenciales enviadas por correo.")
            except NotificationConfigError as exc:
                _logger.warning(
                    "auth.register_with_token: correo config user_id=%s: %s",
                    user_id,
                    exc,
                )
                elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
                print(
                    f"[INFO] auth.register_with_token finished user_id={user_id} elapsed_ms={elapsed_ms} warnings=1",
                    flush=True,
                )
                return render_template(
                    'auth/register_token.html',
                    **_register_context(
                        token,
                        nombre=nombre_completo,
                        username=username,
                        notification_method='email',
                        notification_target=notification_target,
                        password_input=password,
                        error=f'Usuario creado, pero no se pudo enviar el correo: {exc}',
                    ),
                )
            except Exception as exc:
                _logger.exception(
                    "auth.register_with_token: error correo user_id=%s errno=%s",
                    user_id,
                    getattr(exc, "errno", None),
                )
                elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
                print(
                    f"[INFO] auth.register_with_token finished user_id={user_id} elapsed_ms={elapsed_ms} warnings=1",
                    flush=True,
                )
                return render_template(
                    'auth/register_token.html',
                    **_register_context(
                        token,
                        nombre=nombre_completo,
                        username=username,
                        notification_method='email',
                        notification_target=notification_target,
                        password_input=password,
                        error=f'Usuario creado, pero no se pudo enviar el correo: {exc}',
                    ),
                )

            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    success='Usuario creado y contraseña registrada en Solana correctamente.',
                    tx_signature=tx_signature,
                    notification_info=notification_info,
                ),
            )
            
        except BlockchainConfigError as exc:
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            print(
                f"[INFO] auth.register_with_token finished username={username} elapsed_ms={elapsed_ms} error=BlockchainConfigError",
                flush=True,
            )
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error=str(exc),
                ),
            )
        except BlockchainWriteError as exc:
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            print(
                f"[INFO] auth.register_with_token finished username={username} elapsed_ms={elapsed_ms} error=BlockchainWriteError",
                flush=True,
            )
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error=str(exc),
                ),
            )
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
            print(
                f"[INFO] auth.register_with_token finished username={username} elapsed_ms={elapsed_ms} error=Exception",
                flush=True,
            )
            return render_template(
                'auth/register_token.html',
                **_register_context(
                    token,
                    nombre=nombre_completo,
                    username=username,
                    notification_method='email',
                    notification_target=notification_target,
                    password_input=password,
                    error=f'Error inesperado durante el registro: {exc}',
                ),
            )

    return render_template('auth/register_token.html', **_register_context(token))

@auth_bp.route('/password/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or '').strip()
        if not identifier:
            return render_template(
                'auth/forgot_password.html',
                **_password_page_context(
                    identifier=identifier,
                    error='Ingresa tu usuario o correo electrónico.',
                ),
            )

        if '@' in identifier:
            usuario = auth_service.usuario_repo.get_by_email(identifier)
        else:
            usuario = auth_service.usuario_repo.get_by_username(identifier)

        if not usuario or usuario.role != 'admission':
            return render_template(
                'auth/forgot_password.html',
                **_password_page_context(
                    success='Si el usuario existe, recibirás un enlace de recuperación en tu correo.',
                ),
            )

        if not usuario.email or not _email_is_valid(usuario.email):
            return render_template(
                'auth/forgot_password.html',
                **_password_page_context(
                    identifier=identifier,
                    error='Tu usuario no tiene un correo válido registrado. Contacta al administrador.',
                ),
            )

        try:
            token = secrets.token_urlsafe(36)
            password_reset_repo.invalidate_active_tokens_by_user(usuario.id)
            password_reset_repo.create(usuario.id, token, minutes_valid=30)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            notification_service.send_password_reset_link(usuario.email, usuario.nombre_completo, reset_link)
        except NotificationConfigError as exc:
            return render_template(
                'auth/forgot_password.html',
                **_password_page_context(
                    identifier=identifier,
                    error=f'No se pudo enviar el correo de recuperación: {exc}',
                ),
            )
        except Exception as exc:
            return render_template(
                'auth/forgot_password.html',
                **_password_page_context(
                    identifier=identifier,
                    error=f'No se pudo procesar la recuperación: {exc}',
                ),
            )

        return render_template(
            'auth/forgot_password.html',
            **_password_page_context(
                success='Se envió un enlace de recuperación a tu correo.',
            ),
        )

    return render_template('auth/forgot_password.html', **_password_page_context())


@auth_bp.route('/password/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    token_info = password_reset_repo.get_valid_token(token)
    if not token_info:
        return render_template(
            'auth/reset_password.html',
            **_password_page_context(error='El enlace es inválido o ya expiró.'),
        )

    if request.method == 'POST':
        new_password = request.form.get('new_password') or ''
        confirm_password = request.form.get('confirm_password') or ''
        generation_time_ms_raw = (request.form.get('generation_time_ms') or '0').strip()

        try:
            generation_time_ms = max(int(generation_time_ms_raw), 0)
        except ValueError:
            generation_time_ms = 0

        policy_error = _password_policy_error(new_password)
        if policy_error:
            return render_template(
                'auth/reset_password.html',
                **_password_page_context(error=policy_error),
            )

        if new_password != confirm_password:
            return render_template(
                'auth/reset_password.html',
                **_password_page_context(error='La confirmación de contraseña no coincide.'),
            )

        try:
            auth_service.change_password(token_info["usuario_id"], new_password)
            password_reset_repo.mark_as_used(token)
        except Exception as exc:
            return render_template(
                'auth/reset_password.html',
                **_password_page_context(error=f'No se pudo actualizar la contraseña: {exc}'),
            )

        try:
            password_metric_repo.create(
                usuario_id=token_info["usuario_id"],
                password_length=len(new_password),
                generation_time_ms=generation_time_ms,
                strength_label=_password_strength_label(new_password),
            )
        except Exception:
            _logger.exception(
                "auth.reset_password: no se pudo registrar métrica de contraseña user_id=%s",
                token_info.get("usuario_id"),
            )

        return render_template(
            'auth/reset_password.html',
            **_password_page_context(success='Tu contraseña fue actualizada. Ya puedes iniciar sesión.'),
        )

    return render_template('auth/reset_password.html', **_password_page_context())


@auth_bp.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('index'), code=303)
    response.headers['Clear-Site-Data'] = '"cache"'
    return response
