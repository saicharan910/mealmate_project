from django.db import models
from django.db.models import Sum


class Customer(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(max_length=254)
    mobile = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.username


class Restaurant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    picture = models.URLField(
        max_length=500,
        default="https://cwdaust.com.au/wpress/wp-content/uploads/2015/04/placeholder-restaurant.png",
    )
    cuisine = models.CharField(max_length=200)
    rating = models.FloatField(default=0)

    def __str__(self):
        return self.name


class Item(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="menu_items",
    )
    name = models.CharField(max_length=100)
    picture = models.URLField(
        max_length=1000,
        default="https://cdn-icons-png.flaticon.com/512/1147/1147856.png",
    )
    description = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    vegeterian = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class Cart(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    items = models.ManyToManyField(Item, related_name="carts", blank=True)

    def total_price(self):
        return self.items.aggregate(total=Sum("price"))["total"] or 0

    def __str__(self):
        return f"{self.customer.username} - ₹{self.total_price()}"
