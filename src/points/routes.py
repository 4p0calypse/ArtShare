from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from .model import PointsTransaction
from ..services.sirope_service import SiropeService
from ..utils.helpers import format_points, sync_user_points
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('points', __name__)
sirope = SiropeService()

class BuyPointsForm(FlaskForm):
    amount = FloatField('Cantidad en Euros', validators=[
        DataRequired(),
        NumberRange(min=1, message='La cantidad mínima es 1€')
    ])
    submit = SubmitField('Comprar Puntos')

class WithdrawPointsForm(FlaskForm):
    points = IntegerField('Cantidad de Puntos a Retirar', validators=[
        DataRequired(),
        NumberRange(min=1000, message='La cantidad mínima es 1000 puntos')
    ])
    submit = SubmitField('Solicitar Retiro')

@bp.route('/balance')
@login_required
def balance():
    transactions = sirope.find_all(
        PointsTransaction,
        lambda tx: tx.user_id == current_user.id
    )
    # Ordenar por fecha más reciente primero
    transactions = sorted(transactions, key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), reverse=True)
    
    return render_template('points/balance.html',
                         points=current_user.points,
                         transactions=transactions,
                         sirope=sirope)

@bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawPointsForm()
    form.points.validators[1].min = current_app.config['MIN_WITHDRAWAL_POINTS']
    form.points.validators[1].max = current_user.points
    form.points.validators[1].message = f'La cantidad debe estar entre {format_points(current_app.config["MIN_WITHDRAWAL_POINTS"])} y {format_points(current_user.points)} puntos'

    if request.method == 'POST':
        logger.info(f"Datos del formulario: {request.form}")
        if not form.validate():
            logger.error(f"Errores de validación: {form.errors}")
            if 'csrf_token' in form.errors:
                logger.error("Error de validación CSRF")
                flash('Error de seguridad. Por favor, recarga la página e intenta de nuevo.')
            else:
                flash('Por favor, corrige los errores en el formulario.')
            return render_template('points/withdraw.html',
                                form=form,
                                points=current_user.points,
                                min_points=current_app.config['MIN_WITHDRAWAL_POINTS'],
                                conversion_rate=current_app.config['POINTS_TO_CURRENCY_RATE'])

    if form.validate_on_submit():
        try:
            points = form.points.data
            if not current_user.can_withdraw():
                flash('No tienes suficientes puntos para retirar. Mínimo 1000 puntos.')
                return redirect(url_for('points.balance'))
            
            if points > current_user.points:
                flash('No tienes suficientes puntos.')
                return redirect(url_for('points.withdraw'))
            
            # Obtener una instancia fresca del usuario
            from ..auth.user_model import User
            user = sirope.find_by_id(current_user.id, User)
            if not user:
                raise Exception("No se pudo encontrar el usuario")
            
            # Crear transacción de retiro
            tx = PointsTransaction.create_withdrawal_transaction(user.id, points)
            tx_id = sirope.save(tx)
            if not tx_id:
                raise Exception("Error al guardar la transacción")
            
            try:
                # Actualizar puntos del usuario
                user.remove_points(points)
                saved_user = sirope.save(user)
                if not saved_user:
                    raise Exception("Error al actualizar los puntos del usuario")
                
                # Actualizar current_user para reflejar los cambios
                current_user.points = user.points
                
                flash(f'Has solicitado el retiro de {format_points(points)} puntos. Te contactaremos pronto.')
                return redirect(url_for('points.balance'))
            except Exception as e:
                # Si algo falla, intentar revertir la transacción
                try:
                    sirope.force_delete(tx_id)
                except:
                    logger.error("No se pudo revertir la transacción")
                raise e
                
        except ValueError as ve:
            logger.error(f"Error de validación: {str(ve)}")
            flash('Por favor, introduce una cantidad válida.')
            return redirect(url_for('points.withdraw'))
        except Exception as e:
            logger.error(f"Error al procesar el retiro: {str(e)}")
            flash('Error al procesar el retiro. Por favor, inténtalo de nuevo.')
            return redirect(url_for('points.withdraw'))
    
    return render_template('points/withdraw.html',
                         form=form,
                         points=current_user.points,
                         min_points=current_app.config['MIN_WITHDRAWAL_POINTS'],
                         conversion_rate=current_app.config['POINTS_TO_CURRENCY_RATE'])

@bp.route('/transactions')
@login_required
def transactions():
    transactions = sirope.find_all(
        PointsTransaction,
        lambda tx: tx.user_id == current_user.id
    )
    # Ordenar por fecha más reciente primero
    transactions = sorted(transactions, key=lambda x: x.created_at if hasattr(x, 'created_at') else datetime.now(), reverse=True)
    
    return render_template('points/transactions.html',
                         transactions=transactions,
                         sirope=sirope)

@bp.route('/transaction/<transaction_id>')
@login_required
def transaction_detail(transaction_id):
    transaction = sirope.find_by_id(transaction_id, PointsTransaction)
    if transaction is None:
        flash('Transacción no encontrada.')
        return redirect(url_for('points.transactions'))
    
    if transaction.user_id != current_user.id:
        flash('No tienes permiso para ver esta transacción.')
        return redirect(url_for('points.transactions'))
    
    return render_template('points/transaction_detail.html',
                         transaction=transaction)

@bp.route('/buy', methods=['GET', 'POST'])
@login_required
def buy():
    form = BuyPointsForm()
    if form.validate_on_submit():
        try:
            amount = form.amount.data
            
            # Calcular puntos (1€ = 100 puntos)
            points = int(amount * 100)  # Asegurarnos de que los puntos sean enteros
            
            # Obtener una instancia fresca del usuario
            from ..auth.user_model import User
            user = sirope.find_by_id(current_user.id, User)
            if not user:
                raise Exception("No se pudo encontrar el usuario")
            
            # Sincronizar puntos antes de la transacción
            if not sync_user_points(user, sirope):
                logger.warning(f"No se pudieron sincronizar los puntos para {user.username}")
            
            # Crear transacción de compra
            tx = PointsTransaction(
                user_id=user.id,
                points=points,
                type='purchase',
                description=f'Compra de {format_points(points)} puntos por {amount}€',
                created_at=datetime.utcnow()
            )
            
            # Guardar la transacción
            saved_tx = sirope.save(tx)
            if not saved_tx:
                raise Exception("Error al guardar la transacción")
            
            try:
                # Actualizar puntos del usuario
                user.add_points(points)
                saved_user = sirope.save(user)
                if not saved_user:
                    raise Exception("Error al actualizar los puntos del usuario")
                
                # Sincronizar puntos después de la transacción
                if not sync_user_points(user, sirope):
                    logger.warning(f"No se pudieron sincronizar los puntos para {user.username}")
                
                # Actualizar current_user para reflejar los cambios
                current_user.points = user.points
                
                flash(f'¡Has comprado {format_points(points)} puntos exitosamente!')
                return redirect(url_for('points.balance'))
            except Exception as e:
                # Si algo falla, intentar revertir la transacción
                try:
                    sirope.force_delete(saved_tx)
                except:
                    logger.error("No se pudo revertir la transacción")
                raise e
            
        except Exception as e:
            logger.error(f"Error al procesar la compra: {str(e)}")
            flash('Error al procesar la compra. Por favor, inténtalo de nuevo.')
            return redirect(url_for('points.buy'))
    
    return render_template('points/buy.html',
                         form=form,
                         points=current_user.points) 