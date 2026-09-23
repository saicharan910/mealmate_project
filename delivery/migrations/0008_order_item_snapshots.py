from django.db import migrations, models
import django.db.models.deletion


def create_order_items(apps, schema_editor):
    Order = apps.get_model("delivery", "Order")
    OrderItem = apps.get_model("delivery", "OrderItem")

    for order in Order.objects.prefetch_related("items").iterator():
        for item in order.items.all():
            OrderItem.objects.create(
                order=order,
                item=item,
                item_name=item.name,
                unit_price=item.price,
                quantity=1,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("delivery", "0007_order_payment_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "item_name",
                    models.CharField(max_length=100),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(default=1),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="delivery.item",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="delivery.order",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            create_order_items,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="order",
            name="items",
        ),
    ]
