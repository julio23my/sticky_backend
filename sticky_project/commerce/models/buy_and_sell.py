from sticky_project.commerce.models import Provider, Product, Client
from sticky_project.main.models.base import BaseModel
from django.db import models

class Buy(BaseModel):
    """
    Representa una compra de productos a un proveedor.
    """
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='buys', verbose_name="Proveedor") # Renombrado related_name
    total_buy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total de la Compra")
    description = models.TextField(blank=True, null=True, verbose_name="Observaciones")

    class Meta:
        app_name = 'commerce'

        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-created_at'] # Usar created_at de BaseModel o cambiar a un campo específico de fecha de compra
                                    # Si BaseModel no tiene created_at, deberías añadir fecha_compra aquí:
                                    # fecha_compra = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Compra")
                                    # Y luego ordering = ['-fecha_compra']

    def __str__(self):
        # Asumiendo que BaseModel tiene un campo 'created_at'
        return f"Compra #{self.pk} a {self.provider.name} el {self.created_at.strftime('%Y-%m-%d')}"


class BuyDetail(BaseModel):
    """
    Detalle de los productos incluidos en una compra.
    """
    buy = models.ForeignKey(Buy, on_delete=models.CASCADE, related_name='details', verbose_name="Compra") # Renombrado related_name
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    buy_unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Compra Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal")

    class Meta:
        app_name = 'commerce'
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compra"
        unique_together = ('buy', 'product')

    def save(self, *args, **kwargs):
        # Solo calcular el subtotal, la lógica de stock y total de la compra irá en signals
        self.subtotal = self.quantity * self.buy_unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} de {self.product.name} en Compra #{self.buy.pk}"



class Sell(BaseModel):
    """
    Representa una venta de productos a un cliente.
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sells', verbose_name="Cliente") # Renombrado related_name
    total_sell = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total de la Venta")
    description = models.TextField(blank=True, null=True, verbose_name="Observaciones") # Renombrado de observaciones a description

    class Meta:
        app_name = 'commerce'
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at'] # Usar created_at de BaseModel o cambiar a un campo específico de fecha de venta
                                    # Si BaseModel no tiene created_at, deberías añadir fecha_venta aquí:
                                    # fecha_venta = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Venta")
                                    # Y luego ordering = ['-fecha_venta']

    def __str__(self):
        # Asumiendo que BaseModel tiene un campo 'created_at'
        return f"Venta #{self.pk} a {self.client.name} el {self.created_at.strftime('%Y-%m-%d')}"


class SellDetail(BaseModel): # Renombrado de DetalleVenta a SellDetail
    """
    Detalle de los productos incluidos en una venta.
    """
    sell = models.ForeignKey(Sell, on_delete=models.CASCADE, related_name='details', verbose_name="Venta") # Renombrado related_name
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Producto")
    quantity = models.PositiveIntegerField(verbose_name="Cantidad")
    unit_sell_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal")

    class Meta:
        app_name = 'commerce'
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
        unique_together = ('sell', 'product')

    def save(self, *args, **kwargs):
        # Solo calcular el subtotal, la lógica de stock y total de la venta irá en signals
        self.subtotal = self.quantity * self.unit_sell_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} de {self.product.name} en Venta #{self.sell.pk}"

class Bill(BaseModel):
    """
    Representa una factura generada a partir de una venta.
    """
    sell = models.OneToOneField(Sell, on_delete=models.CASCADE, related_name='bill', verbose_name="Venta Asociada") # Renombrado de venta a sell, factura a bill
    bill_number = models.CharField(max_length=50, unique=True, verbose_name="Número de Factura")
    total_bill = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Facturado")
    iva = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="IVA Aplicado")
    subtotal_without_iva = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Subtotal sin IVA")
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pendiente'), ('paid', 'Pagada'), ('cancelled', 'Anulada')], # Renombrados choices
        default='pending',
        verbose_name="Estado de la Factura"
    )

    class Meta:
        app_name = 'commerce'
        verbose_name = "Bill"
        verbose_name_plural = "Bills"
        ordering = ['-created_at'] # Usar created_at de BaseModel o cambiar a un campo específico de fecha de emisión
                                    # Si BaseModel no tiene created_at, deberías añadir fecha_emision aquí:
                                    # fecha_emision = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Emisión")
                                    # Y luego ordering = ['-fecha_emision']

    def save(self, *args, **kwargs):
        # La lógica de cálculo del IVA y subtotal_without_iva se podría mover a un signal pre_save
        # o mantenerse aquí si es simple y depende solo de la venta.
        self.subtotal_without_iva = self.sell.total_sell / (1 + (self.iva / 100)) if self.iva > 0 else self.sell.total_sell
        self.total_bill = self.sell.total_sell
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Factura #{self.bill_number} para Venta #{self.sell.pk}"
