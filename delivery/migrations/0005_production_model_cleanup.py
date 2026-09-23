from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("delivery", "0004_alter_item_picture"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="username",
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name="customer",
            name="password",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="customer",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name="customer",
            name="mobile",
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name="customer",
            name="address",
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name="restaurant",
            name="name",
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name="restaurant",
            name="picture",
            field=models.URLField(
                default="https://cwdaust.com.au/wpress/wp-content/uploads/2015/04/placeholder-restaurant.png",
                max_length=500,
            ),
        ),
        migrations.AlterField(
            model_name="restaurant",
            name="rating",
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name="item",
            name="name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="item",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name="cart",
            name="customer",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cart",
                to="delivery.customer",
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="items",
            field=models.ManyToManyField(blank=True, related_name="carts", to="delivery.item"),
        ),
    ]
