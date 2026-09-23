import logging
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Cart, Customer, Item, Order, Restaurant

logger = logging.getLogger(__name__)
GST_RATE = Decimal("0.18")


def index(request):
    return render(request, "index.html")


def open_signin(request):
    return render(request, "signin.html")


def open_signup(request):
    return render(request, "signup.html")


def signup(request):
    if request.method != "POST":
        return render(request, "signup.html")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    address = request.POST.get("address", "").strip()

    if not all([username, password, email, mobile, address]):
        return render(request, "signup.html", {"error": "All fields are required."})

    if Customer.objects.filter(username=username).exists():
        return render(request, "signup.html", {"error": "Username already exists."})

    Customer.objects.create(
        username=username,
        password=make_password(password),
        email=email,
        mobile=mobile,
        address=address,
    )
    return redirect("open_signin")


def signin(request):
    if request.method != "POST":
        return render(request, "signin.html")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    customer = Customer.objects.filter(username=username).first()

    if not customer or not check_password(password, customer.password):
        return render(request, "fail.html")

    request.session["username"] = customer.username
    request.session.set_expiry(60 * 60 * 24 * 7)

    if customer.username.lower() == "admin":
        return redirect("admin_dashboard")

    return redirect("customer_home", username=customer.username)


def _is_admin(request):
    return request.session.get("username", "").lower() == "admin"


def admin_dashboard(request):
    if not _is_admin(request):
        return redirect("open_signin")

    context = {
        "total_orders": Order.objects.filter(status="paid").count(),
        "active_users": Customer.objects.exclude(username__iexact="admin").count(),
        "daily_revenue": (
            Order.objects.filter(status="paid")
            .values_list("total_price", flat=True)
        ),
    }
    context["daily_revenue"] = sum(context["daily_revenue"], Decimal("0.00"))
    return render(request, "admin_home.html", context)


def open_add_restaurant(request):
    if not _is_admin(request):
        return redirect("open_signin")
    return render(request, "add_restaurant.html")


@require_POST
def add_restaurant(request):
    if not _is_admin(request):
        return redirect("open_signin")

    name = request.POST.get("name", "").strip()
    if Restaurant.objects.filter(name=name).exists():
        return HttpResponse("Duplicate restaurant.", status=409)

    Restaurant.objects.create(
        name=name,
        picture=request.POST.get("picture", "").strip(),
        cuisine=request.POST.get("cuisine", "").strip(),
        rating=request.POST.get("rating") or 0,
    )
    return redirect("open_show_restaurant")


def open_show_restaurant(request):
    if not _is_admin(request):
        return redirect("open_signin")
    return render(
        request,
        "show_restaurants.html",
        {"restaurantList": Restaurant.objects.all()},
    )


def open_update_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(request, "update_restaurant.html", {"restaurant": restaurant})


@require_POST
def update_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    restaurant.name = request.POST.get("name", "").strip()
    restaurant.picture = request.POST.get("picture", "").strip()
    restaurant.cuisine = request.POST.get("cuisine", "").strip()
    restaurant.rating = request.POST.get("rating") or 0
    restaurant.save()
    return redirect("open_show_restaurant")


@require_POST
def delete_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    get_object_or_404(Restaurant, id=restaurant_id).delete()
    return redirect("open_show_restaurant")


def open_update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(
        request,
        "update_menu.html",
        {"itemList": restaurant.menu_items.all(), "restaurant": restaurant},
    )


@require_POST
def update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    name = request.POST.get("name", "").strip()

    if Item.objects.filter(name=name, restaurant=restaurant).exists():
        return HttpResponse("Duplicate item in this restaurant.", status=409)

    Item.objects.create(
        restaurant=restaurant,
        name=name,
        description=request.POST.get("description", "").strip(),
        price=request.POST.get("price") or 0,
        vegeterian=request.POST.get("is_veg") == "on",
        picture=request.POST.get("picture", "").strip(),
    )
    return redirect("open_update_menu", restaurant_id=restaurant_id)


def view_menu(request, restaurant_id, username):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(
        request,
        "customer_menu.html",
        {
            "itemList": restaurant.menu_items.all(),
            "restaurant": restaurant,
            "username": username,
        },
    )


@require_POST
def add_to_cart(request, item_id, username):
    item = get_object_or_404(Item, id=item_id)
    customer = get_object_or_404(Customer, username=username)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart.items.add(item)
    return redirect("view_menu", restaurant_id=item.restaurant_id, username=username)


@require_POST
def remove_from_cart(request, username, item_id):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    if cart:
        cart.items.remove(get_object_or_404(Item, id=item_id))

    return redirect("show_cart", username=username)


def show_cart(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.select_related("restaurant").all() if cart else []
    total_price = cart.total_price() if cart else Decimal("0.00")

    return render(
        request,
        "cart.html",
        {"itemList": items, "total_price": total_price, "username": username},
    )


def checkout(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()

    if not cart or not cart.items.exists():
        return render(
            request,
            "checkout.html",
            {"error": "Your cart is empty.", "username": username},
        )

    subtotal = cart.total_price()
    total_price = (subtotal * (Decimal("1") + GST_RATE)).quantize(Decimal("0.01"))
    amount_paise = int(total_price * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        order = client.order.create(
            data={
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,
            }
        )
    except Exception:
        logger.exception("Razorpay order creation failed")
        return render(
            request,
            "checkout.html",
            {
                "username": username,
                "cart_items": cart.items.all(),
                "total_price": total_price,
                "error": "Unable to create the payment order. Please try again.",
            },
        )

    return render(
        request,
        "checkout.html",
        {
            "username": username,
            "cart_items": cart.items.all(),
            "subtotal": subtotal,
            "gst": subtotal * GST_RATE,
            "total_price": total_price,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "order_id": order["id"],
            "amount_paise": amount_paise,
        },
    )


@require_POST
def payment_view(request):
    payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")
    username = request.POST.get("username") or request.session.get("username")

    if not all([payment_id, razorpay_order_id, signature, username]):
        return HttpResponse("Payment verification data is incomplete.", status=400)

    customer = get_object_or_404(Customer, username=username)
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        logger.warning("Invalid Razorpay signature for customer %s", customer.pk)
        return HttpResponse("Payment verification failed.", status=400)
    except Exception:
        logger.exception("Unexpected Razorpay verification error")
        return HttpResponse("Payment verification failed.", status=400)

    cart = Cart.objects.filter(customer=customer).first()
    if not cart or not cart.items.exists():
        return redirect("orders", username=username)

    items = list(cart.items.all())
    subtotal = cart.total_price()
    total_price = (subtotal * (Decimal("1") + GST_RATE)).quantize(Decimal("0.01"))

    order = Order.objects.create(
        customer=customer,
        total_price=total_price,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=payment_id,
        status="paid",
    )
    order.items.set(items)
    cart.items.clear()

    return redirect("orders", username=username)


def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    order = customer.orders.prefetch_related("items").order_by("-created_at").first()

    return render(
        request,
        "orders.html",
        {
            "username": username,
            "customer": customer,
            "order": order,
            "cart_items": order.items.all() if order else [],
            "total_price": order.total_price if order else Decimal("0.00"),
        },
    )


def profile(request, username):
    customer = get_object_or_404(Customer, username=username)
    return render(
        request,
        "profile.html",
        {"username": username, "customer": customer},
    )


def profile_default(request):
    username = request.session.get("username")
    if username:
        return redirect("profile", username=username)
    return redirect("open_signin")


def customer_home(request, username):
    if request.session.get("username") != username:
        return redirect("open_signin")

    return render(
        request,
        "customer_home.html",
        {"restaurantList": Restaurant.objects.all(), "username": username},
    )


@require_POST
def save_profile(request):
    username = request.session.get("username")
    if not username:
        return redirect("open_signin")

    customer = get_object_or_404(Customer, username=username)
    customer.mobile = request.POST.get("mobile", "").strip()
    customer.address = request.POST.get("address", "").strip()
    customer.save(update_fields=["mobile", "address"])

    return redirect("profile", username=username)
