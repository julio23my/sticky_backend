# inventario_app/signals.py
from datetime import timezone

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum

from sticky_project.commerce.models import BuyDetail, Product, Buy, SellDetail, Sell, Bill


# --- Signals para BuyDetail ---
@receiver(post_save, sender=BuyDetail)
def update_product_stock_on_buy_detail_save(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto y el total de la compra cuando se guarda un BuyDetail.
    """
    with transaction.atomic():
        # Recuperar el estado anterior de la cantidad si se está actualizando el detalle
        old_quantity = 0
        if not created:
            try:
                # Obtener la instancia antigua del BuyDetail para comparar cantidades
                # Esto es crucial para un manejo correcto en actualizaciones
                old_buy_detail = sender.objects.get(pk=instance.pk)
                old_quantity = old_buy_detail.quantity
            except sender.DoesNotExist:
                pass # Esto no debería ocurrir si no es una creación

        # Ajustar el stock del producto
        product = instance.product
        stock_change = instance.quantity - old_quantity
        product.stock += stock_change
        product.save(update_fields=['stock', 'updated_at']) # Solo actualizar el campo stock y updated_at

        # Recalcular y actualizar el total de la compra
        # Se usa F() para evitar race conditions si múltiples detalles se actualizan rápidamente
        # o simplemente se hace una suma para mayor claridad.
        # buy = instance.buy
        # buy.total_buy = buy.details.aggregate(total=Sum('subtotal'))['total'] or 0.00
        # buy.save(update_fields=['total_buy', 'updated_at'])

        # Mejor enfoque para el total de la compra: usar una señal separada para Buy.total_buy
        # Esto es más robusto y evita ciclos de guardado si BuyDetail guarda Buy.

@receiver(post_delete, sender=BuyDetail)
def update_product_stock_on_buy_detail_delete(sender, instance, **kwargs):
    """
    Actualiza el stock del producto y el total de la compra cuando se elimina un BuyDetail.
    """
    with transaction.atomic():
        product = instance.product
        product.stock -= instance.quantity
        product.save(update_fields=['stock', 'updated_at'])

        # Recalcular y actualizar el total de la compra
        # buy = instance.buy
        # buy.total_buy = buy.details.aggregate(total=Sum('subtotal'))['total'] or 0.00
        # buy.save(update_fields=['total_buy', 'updated_at'])

        # Mejor enfoque para el total de la compra: usar una señal separada para Buy.total_buy


# Signal para actualizar el total_buy en el modelo Buy
@receiver([post_save, post_delete], sender=BuyDetail)
def update_buy_total(sender, instance, **kwargs):
    """
    Actualiza el total_buy del modelo Buy después de que un BuyDetail se guarda o elimina.
    """
    # Usamos transaction.on_commit para asegurarnos de que el BuyDetail ya esté
    # persistido o eliminado de la base de datos antes de recalcular el total.
    def _update_buy_total():
        buy = instance.buy
        buy_total = buy.details.aggregate(total=Sum('subtotal'))['total'] or 0.00
        if buy.total_buy != buy_total: # Evitar guardar si el valor no ha cambiado
            buy.total_buy = buy_total
            buy.save(update_fields=['total_buy', 'updated_at'])

    transaction.on_commit(_update_buy_total)


# --- Signals para SellDetail ---
@receiver(pre_save, sender=SellDetail)
def check_product_stock_on_sell_detail_save(sender, instance, **kwargs):
    """
    Verifica si hay suficiente stock antes de guardar un SellDetail.
    """
    if instance.pk: # Si se está actualizando un detalle existente
        old_sell_detail = sender.objects.get(pk=instance.pk)
        quantity_change = instance.quantity - old_sell_detail.quantity
    else: # Si es un nuevo detalle
        quantity_change = instance.quantity

    if quantity_change > 0 and instance.product.stock < quantity_change:
        from django.core.exceptions import ValidationError
        raise ValidationError(f"No hay suficiente stock para el producto '{instance.product.name}'. Stock actual: {instance.product.stock}, Cantidad requerida: {quantity_change}")


@receiver(post_save, sender=SellDetail)
def update_product_stock_on_sell_detail_save(sender, instance, created, **kwargs):
    """
    Actualiza el stock del producto y el total de la venta cuando se guarda un SellDetail.
    """
    with transaction.atomic():
        old_quantity = 0
        if not created:
            try:
                old_sell_detail = sender.objects.get(pk=instance.pk)
                old_quantity = old_sell_detail.quantity
            except sender.DoesNotExist:
                pass

        product = instance.product
        stock_change = instance.quantity - old_quantity # Esto ya maneja la reducción si la cantidad aumenta, y el aumento si disminuye
        product.stock -= stock_change # Restar el cambio de stock
        product.save(update_fields=['stock', 'updated_at'])


@receiver(post_delete, sender=SellDetail)
def update_product_stock_on_sell_detail_delete(sender, instance, **kwargs):
    """
    Actualiza el stock del producto y el total de la venta cuando se elimina un SellDetail.
    """
    with transaction.atomic():
        product = instance.product
        product.stock += instance.quantity # Devolver el stock
        product.save(update_fields=['stock', 'updated_at'])


# Signal para actualizar el total_sell en el modelo Sell
@receiver([post_save, post_delete], sender=SellDetail)
def update_sell_total(sender, instance, **kwargs):
    """
    Actualiza el total_sell del modelo Sell después de que un SellDetail se guarda o elimina.
    """
    def _update_sell_total():
        sell = instance.sell
        sell_total = sell.details.aggregate(total=Sum('subtotal'))['total'] or 0.00
        if sell.total_sell != sell_total:
            sell.total_sell = sell_total
            sell.save(update_fields=['total_sell', 'updated_at'])

    transaction.on_commit(_update_sell_total)


# --- Signals para Bill (Factura) ---
@receiver(pre_save, sender=Bill)
def calculate_bill_totals(sender, instance, **kwargs):
    """
    Calcula el subtotal sin IVA y el total de la factura antes de guardar.
    """
    if instance.sell:
        # Asegurarse de que total_sell de la Venta esté actualizado (si es necesario)
        # Aunque con las señales de SellDetail esto ya debería estar cubierto.
        instance.subtotal_without_iva = instance.sell.total_sell / (1 + (instance.iva / 100)) if instance.iva > 0 else instance.sell.total_sell
        instance.total_bill = instance.sell.total_sell

# Opcional: Si quieres que la factura se cree/actualice automáticamente con la venta
@receiver(post_save, sender=Sell)
def create_or_update_bill_from_sell(sender, instance, created, **kwargs):
    """
    Crea o actualiza una factura automáticamente cuando una venta se guarda.
    """
    if created or not hasattr(instance, 'bill'): # Si es una nueva venta o no tiene factura asociada
        bill, created = Bill.objects.get_or_create(sell=instance,
                                                  defaults={
                                                      'bill_number': f"FACT-{instance.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                                                      'iva': 16.00, # Valor por defecto de IVA
                                                      'total_bill': instance.total_sell,
                                                      'subtotal_without_iva': instance.total_sell / (1 + (16.00 / 100)) # Ejemplo
                                                  })
        if not created: # Si ya existía, actualiza los campos importantes
            bill.total_bill = instance.total_sell
            bill.subtotal_without_iva = instance.total_sell / (1 + (bill.iva / 100)) if bill.iva > 0 else instance.total_sell
            bill.save()
