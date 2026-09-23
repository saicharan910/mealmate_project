from django.db import migrations, models
import django.db.models.deletion


def hash_existing_passwords(apps, schema_editor):
    from django.contrib.auth.hashers import identify_hasher, make_password

    Customer = apps.get_model("delivery", "Customer")

    for customer in Customer.objects.all().iterator():
        try:
            identify_hasher(customer.password)
        except ValueError:
            customer.password = make_password(customer.password)
            customer.save(update_fields=["password"])


class Migration(migrations.Migration):

    dependencies = [
        ("delivery", "0005_production_model_cleanup"),
    ]

    operations = [
        migrations.RunPython(hash_existing_passwords, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("razorpay_order_id", models.CharField(blank=True, max_length=100)),
                ("razorpay_payment_id", models.CharField(blank=True, max_length=100)),
                ("status", models.CharField(
                    choices=[("paid", "Paid"), ("pending", "Pending"), ("failed", "Failed")],
                    default="pending",
                    max_length=20,
                )),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="orders",
                    to="delivery.customer",
                )),
                ("items", models.ManyToManyField(related_name="orders", to="delivery.item")),
            ],
        ),
    ]
