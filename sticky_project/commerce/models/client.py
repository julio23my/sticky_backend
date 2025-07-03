from sticky_project.main.models.base import BaseModel
from django.db import models

class Client(BaseModel):
    """
    Representa un cliente al que se le venden productos.
    """
    name = models.CharField(max_length=200, verbose_name="Nombre del Cliente")
    last_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Apellido del Cliente")
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Identificación")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    address = models.TextField(blank=True, null=True, verbose_name="Dirección")

    class Meta:
        app_name = 'commerce'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.name} {self.last_name if self.last_name else ''}".strip()
