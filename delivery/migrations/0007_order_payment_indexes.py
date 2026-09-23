from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("delivery", "0006_order_and_hash_passwords"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="razorpay_order_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("paid", "Paid"),
                    ("pending", "Pending"),
                    ("failed", "Failed"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
    ]
