import logging
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Cart, Customer, Item, Order, OrderItem, Restaurant

logger = logging.getLogger(__name__)

GST_RATE = Decimal("0.18")


# ==============================================================================
# Helper Methods
# ==============================================================================

def _get_session_customer(request):
    username = request.session.get("username")
    if not username:
        return None
    return Customer.objects.filter(username__iexact=username).first()


def _is_admin(request):
    username = request.session.get("username", "")
    return username.lower() == "admin"


# ==============================================================================
# Authentication & Landing Views
# ==============================================================================

def index(request):
    session_customer = _get_session_customer(request)
    if session_customer:
        if _is_admin(request):
            return redirect("admin_dashboard")
        return redirect("customer_home", username=session_customer.username)
    return render(request, "index.html")


def open_signin(request):
    session_customer = _get_session_customer(request)
    if session_customer:
        if _is_admin(request):
            return redirect("admin_dashboard")
        return redirect("customer_home", username=session_customer.username)
    return render(request, "signin.html")


def open_signup(request):
    session_customer = _get_session_customer(request)
    if session_customer:
        if _is_admin(request):
            return redirect("admin_dashboard")
        return redirect("customer_home", username=session_customer.username)
    return render(request, "signup.html")


def signup(request):
    if request.method != "POST":
        return redirect("open_signup")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    email = request.POST.get("email", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    address = request.POST.get("address", "").strip()

    if not all([username, password, email, mobile, address]):
        return render(
            request,
            "signup.html",
            {"error": "All fields are required."},
        )

    if Customer.objects.filter(username__iexact=username).exists():
        return render(
            request,
            "signup.html",
            {"error": "Username already exists."},
        )

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
        return redirect("open_signin")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    customer = Customer.objects.filter(username__iexact=username).first()

    if not customer or not check_password(password, customer.password):
        return render(request, "fail.html")

    request.session["username"] = customer.username
    request.session.set_expiry(60 * 60 * 24 * 7)

    if customer.username.lower() == "admin":
        return redirect("admin_dashboard")

    return redirect("customer_home", username=customer.username)


def signout(request):
    request.session.flush()
    return redirect("open_signin")


# ==============================================================================
# Admin & Restaurant Management
# ==============================================================================

def admin_dashboard(request):
    if not _is_admin(request):
        return redirect("open_signin")

    paid_orders = Order.objects.filter(status="paid")

    context = {
        "total_orders": paid_orders.count(),
        "active_users": Customer.objects.exclude(username__iexact="admin").count(),
        "daily_revenue": sum(
            paid_orders.values_list("total_price", flat=True),
            Decimal("0.00"),
        ),
    }
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
    if not name:
        return HttpResponse("Restaurant name is required.", status=400)

    if Restaurant.objects.filter(name__iexact=name).exists():
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
    return render(
        request,
        "update_restaurant.html",
        {"restaurant": restaurant},
    )


@require_POST
def update_restaurant(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    name = request.POST.get("name", "").strip()

    if not name:
        return HttpResponse("Restaurant name is required.", status=400)

    if (
        Restaurant.objects.filter(name__iexact=name)
        .exclude(id=restaurant.id)
        .exists()
    ):
        return HttpResponse("Duplicate restaurant.", status=409)

    restaurant.name = name
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


# ==============================================================================
# Menu Management
# ==============================================================================

def open_update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(
        request,
        "update_menu.html",
        {
            "itemList": restaurant.menu_items.all(),
            "restaurant": restaurant,
        },
    )


@require_POST
def update_menu(request, restaurant_id):
    if not _is_admin(request):
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    picture = request.POST.get("picture", "").strip()
    price = request.POST.get("price", "").strip()

    if not name or not description or not price:
        return HttpResponse("Name, description and price are required.", status=400)

    if Item.objects.filter(name__iexact=name, restaurant=restaurant).exists():
        return HttpResponse("Duplicate item in this restaurant.", status=409)

    try:
        price_value = Decimal(price)
        if price_value < 0:
            raise ValueError
    except (ValueError, TypeError, ArithmeticError):
        return HttpResponse("Invalid item price.", status=400)

    Item.objects.create(
        restaurant=restaurant,
        name=name,
        description=description,
        price=price_value,
        vegeterian=(
            request.POST.get("vegeterian") == "on"
            or request.POST.get("is_veg") == "on"
        ),
        picture=picture,
    )

    return redirect("open_update_menu", restaurant_id=restaurant_id)


# ==============================================================================
# Customer Views & Cart
# ==============================================================================

def customer_home(request, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    return render(
        request,
        "customer_home.html",
        {
            "restaurantList": Restaurant.objects.all(),
            "username": session_customer.username,
        },
    )


def view_menu(request, restaurant_id, username):
    session_customer = _get_session_customer(request)
    if not session_customer:
        return redirect("open_signin")

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    return render(
        request,
        "customer_menu.html",
        {
            "itemList": restaurant.menu_items.all(),
            "restaurant": restaurant,
            "username": session_customer.username,
        },
    )


@require_POST
def add_to_cart(request, item_id, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    item = get_object_or_404(Item, id=item_id)
    cart, _ = Cart.objects.get_or_create(customer=session_customer)
    cart.items.add(item)

    return redirect("view_menu", restaurant_id=item.restaurant_id, username=session_customer.username)


@require_POST
def remove_from_cart(request, username, item_id):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    cart = Cart.objects.filter(customer=session_customer).first()
    if cart:
        item = get_object_or_404(Item, id=item_id)
        cart.items.remove(item)

    return redirect("show_cart", username=session_customer.username)


def show_cart(request, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    cart = Cart.objects.filter(customer=session_customer).first()
    items = cart.items.select_related("restaurant").all() if cart else []
    total_price = cart.total_price() if cart else Decimal("0.00")

    return render(
        request,
        "cart.html",
        {
            "itemList": items,
            "total_price": total_price,
            "username": session_customer.username,
        },
    )


# ==============================================================================
# Checkout & Razorpay Payment Flow
# ==============================================================================

def checkout(request, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    cart = Cart.objects.filter(customer=session_customer).first()
    if not cart or not cart.items.exists():
        return render(
            request,
            "checkout.html",
            {
                "error": "Your cart is empty.",
                "username": session_customer.username,
            },
        )

    items = list(cart.items.select_related("restaurant").all())
    subtotal = sum((item.price for item in items), Decimal("0.00"))
    gst = (subtotal * GST_RATE).quantize(Decimal("0.01"))
    total_price = (subtotal + gst).quantize(Decimal("0.01"))
    amount_paise = int(total_price * 100)

    pending_order = Order.objects.create(
        customer=session_customer,
        total_price=total_price,
        status="pending",
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=pending_order,
                item=item,
                item_name=item.name,
                unit_price=item.price,
                quantity=1,
            )
            for item in items
        ]
    )

    razorpay_key = getattr(settings, "RAZORPAY_KEY_ID", "")
    razorpay_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")

    if not razorpay_key or not razorpay_secret:
        logger.error("Razorpay API credentials are not set in settings.")
        pending_order.status = "failed"
        pending_order.save(update_fields=["status"])
        return render(
            request,
            "checkout.html",
            {
                "username": session_customer.username,
                "cart_items": items,
                "subtotal": subtotal,
                "gst": gst,
                "total_price": total_price,
                "error": "Payment service is currently unavailable. Please verify payment credentials.",
            },
        )

    client = razorpay.Client(auth=(razorpay_key, razorpay_secret))

    try:
        razorpay_order = client.order.create(
            data={
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,
                "notes": {
                    "mealmate_order_id": str(pending_order.pk),
                    "customer_id": str(session_customer.pk),
                },
            }
        )
    except Exception:
        logger.exception("Razorpay order creation failed for local order %s", pending_order.pk)
        pending_order.status = "failed"
        pending_order.save(update_fields=["status"])
        return render(
            request,
            "checkout.html",
            {
                "username": session_customer.username,
                "cart_items": items,
                "subtotal": subtotal,
                "gst": gst,
                "total_price": total_price,
                "error": "Unable to initiate payment with Razorpay. Please try again.",
            },
        )

    pending_order.razorpay_order_id = razorpay_order["id"]
    pending_order.save(update_fields=["razorpay_order_id"])

    return render(
        request,
        "checkout.html",
        {
            "username": session_customer.username,
            "customer_email": session_customer.email,
            "customer_mobile": session_customer.mobile,
            "cart_items": items,
            "subtotal": subtotal,
            "gst": gst,
            "total_price": total_price,
            "razorpay_key_id": razorpay_key,
            "order_id": razorpay_order["id"],
            "amount_paise": amount_paise,
        },
    )


@require_POST
def payment_view(request):
    payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    signature = request.POST.get("razorpay_signature")

    customer = _get_session_customer(request)
    if not customer:
        return HttpResponse("Authentication required.", status=401)

    if not all([payment_id, razorpay_order_id, signature]):
        return HttpResponse("Payment verification data is incomplete.", status=400)

    local_order = (
        Order.objects.prefetch_related("items")
        .filter(razorpay_order_id=razorpay_order_id, customer=customer)
        .first()
    )

    if not local_order:
        logger.warning("Razorpay order %s was not found for customer %s", razorpay_order_id, customer.pk)
        return HttpResponse("Payment order could not be found.", status=400)

    if local_order.status == "paid":
        return redirect("orders", username=customer.username)

    if local_order.status != "pending":
        return HttpResponse("This payment order is no longer active.", status=409)

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
        logger.warning("Invalid Razorpay signature for local order %s", local_order.pk)
        return HttpResponse("Payment verification failed.", status=400)
    except Exception:
        logger.exception("Unexpected Razorpay signature error for local order %s", local_order.pk)
        return HttpResponse("Payment verification failed.", status=400)

    try:
        razorpay_order = client.order.fetch(razorpay_order_id)
    except Exception:
        logger.exception("Unable to fetch Razorpay order %s", razorpay_order_id)
        return HttpResponse("Unable to verify payment amount.", status=400)

    expected_amount_paise = int(local_order.total_price * 100)
    received_amount_paise = int(razorpay_order.get("amount", 0))
    received_currency = razorpay_order.get("currency")

    if received_amount_paise != expected_amount_paise or received_currency != "INR":
        local_order.status = "failed"
        local_order.save(update_fields=["status"])
        logger.error(
            "Payment mismatch for order %s: expected=%s received=%s currency=%s",
            local_order.pk,
            expected_amount_paise,
            received_amount_paise,
            received_currency,
        )
        return HttpResponse("Payment amount verification failed.", status=400)

    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(pk=local_order.pk)
        if locked_order.status == "paid":
            return redirect("orders", username=customer.username)

        locked_order.razorpay_payment_id = payment_id
        locked_order.status = "paid"
        locked_order.save(update_fields=["razorpay_payment_id", "status"])

        cart = Cart.objects.filter(customer=customer).first()
        if cart:
            order_items = list(locked_order.items.select_related("item").all())
            if order_items:
                cart.items.remove(*(order_item.item for order_item in order_items))

    return redirect("orders", username=customer.username)


# ==============================================================================
# Orders & Profile Views
# ==============================================================================

def orders(request, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    order = (
        session_customer.orders.prefetch_related("items")
        .order_by("-created_at")
        .first()
    )

    return render(
        request,
        "orders.html",
        {
            "username": session_customer.username,
            "customer": session_customer,
            "order": order,
            "order_items": order.items.all() if order else [],
            "total_price": order.total_price if order else Decimal("0.00"),
        },
    )


def profile(request, username):
    session_customer = _get_session_customer(request)
    if not session_customer or session_customer.username.lower() != username.lower():
        return redirect("open_signin")

    return render(
        request,
        "profile.html",
        {
            "username": session_customer.username,
            "customer": session_customer,
        },
    )


def profile_default(request):
    session_customer = _get_session_customer(request)
    if session_customer:
        return redirect("profile", username=session_customer.username)
    return redirect("open_signin")


@require_POST
def save_profile(request):
    session_customer = _get_session_customer(request)
    if not session_customer:
        return redirect("open_signin")

    session_customer.mobile = request.POST.get("mobile", "").strip()
    session_customer.address = request.POST.get("address", "").strip()
    session_customer.save(update_fields=["mobile", "address"])

    return redirect("profile", username=session_customer.username)
