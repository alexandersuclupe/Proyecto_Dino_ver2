# Generated by Django 5.2.3 on 2025-06-15 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_delete_evaluacion_remove_usuario_puesto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='criterio',
            name='estado',
            field=models.CharField(choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], default='Activo', max_length=10),
        ),
        migrations.AddField(
            model_name='criterio',
            name='peso',
            field=models.PositiveIntegerField(default=0, help_text='Porcentaje que aporta este criterio', verbose_name='Peso (%)'),
        ),
        migrations.AlterField(
            model_name='criterio',
            name='puestos',
            field=models.ManyToManyField(related_name='criterios', to='core.puesto'),
        ),
    ]
