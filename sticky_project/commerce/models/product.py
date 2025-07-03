from django.db import models
from django.utils import timezone

from sticky_project.commerce.models.invetory import Category, Provider
# Asumiendo que esta es tu clase base con campos de fecha_creacion y fecha_actualizacion
from sticky_project.main.models.base import BaseModel

class Product(BaseModel):
    """
    Representa un producto en el inventario.
    """
    name = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario")
    stock = models.IntegerField(default=0, verbose_name="Cantidad en Stock")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="Categoría") # Renombrado related_name
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplied_products', verbose_name="Proveedor") # Renombrado related_name

    class Meta:
        app_name = 'commerce'

        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ('name', 'provider') # Corregido de 'nombre', 'proveedor' a 'name', 'provider'

    def __str__(self):
        return self.name # Corregido de self.nombre a self.name


