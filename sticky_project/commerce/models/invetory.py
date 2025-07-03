from sticky_project.main.models.base import BaseModel
from django.db import models

class Category(BaseModel):
    """
    Representa una categoría para organizar los productos.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Provider(BaseModel):
    """
    Representa un proveedor de productos.
    """
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre del Proveedor")
    contact = models.CharField(max_length=100, blank=True, null=True, verbose_name="Información de Contacto")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    address = models.TextField(blank=True, null=True, verbose_name="Dirección")

    class Meta:
        app_name = 'commerce'

        verbose_name = "Provider"
        verbose_name_plural = "Providers"

    def __str__(self):
        return self.name # Corregido de self.nombre a self.name

