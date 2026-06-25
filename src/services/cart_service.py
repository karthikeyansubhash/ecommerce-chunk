"""Shopping cart and checkout orchestration for ecommerce-lite."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class CartError(Exception):
    """Raised for invalid cart or checkout operations."""


class CartStatus(Enum):
    ACTIVE = "active"
    CHECKED_OUT = "checked_out"
    ABANDONED = "abandoned"


@dataclass
class CartItem:
    sku: str
    unit_price_cents: int
    quantity: int = 1

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


@dataclass
class Cart:
    cart_id: str
    customer_id: str
    items: dict[str, CartItem] = field(default_factory=dict)
    status: CartStatus = CartStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    coupon_code: Optional[str] = None

    @property
    def subtotal_cents(self) -> int:
        return sum(item.line_total_cents for item in self.items.values())

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.values())


class CartService:
    """Manages cart lifecycle: add/remove items, apply coupons, checkout."""

    def __init__(self, tax_rate: float = 0.08):
        if not 0.0 <= tax_rate <= 1.0:
            raise CartError("tax_rate must be between 0 and 1")
        self.tax_rate = tax_rate
        self.carts: dict[str, Cart] = {}
        self._coupons: dict[str, float] = {}

    def create_cart(self, cart_id: str, customer_id: str) -> Cart:
        if cart_id in self.carts:
            raise CartError(f"Cart already exists: {cart_id}")
        cart = Cart(cart_id=cart_id, customer_id=customer_id)
        self.carts[cart_id] = cart
        return cart

    def register_coupon(self, code: str, discount_pct: float) -> None:
        if not 0.0 < discount_pct <= 1.0:
            raise CartError("discount_pct must be between 0 (exclusive) and 1")
        self._coupons[code] = discount_pct

    def add_item(self, cart_id: str, sku: str, unit_price_cents: int, quantity: int = 1) -> Cart:
        if quantity <= 0:
            raise CartError("quantity must be positive")
        if unit_price_cents < 0:
            raise CartError("unit_price_cents cannot be negative")

        cart = self._get_active_cart(cart_id)
        if sku in cart.items:
            cart.items[sku].quantity += quantity
        else:
            cart.items[sku] = CartItem(sku=sku, unit_price_cents=unit_price_cents, quantity=quantity)
        return cart

    def remove_item(self, cart_id: str, sku: str, quantity: Optional[int] = None) -> Cart:
        cart = self._get_active_cart(cart_id)
        if sku not in cart.items:
            raise CartError(f"SKU not in cart: {sku}")

        if quantity is None or quantity >= cart.items[sku].quantity:
            del cart.items[sku]
        else:
            cart.items[sku].quantity -= quantity
        return cart

    def apply_coupon(self, cart_id: str, code: str) -> Cart:
        cart = self._get_active_cart(cart_id)
        if code not in self._coupons:
            raise CartError(f"Invalid coupon code: {code}")
        cart.coupon_code = code
        return cart

    def calculate_total_cents(self, cart_id: str) -> dict[str, int]:
        """Returns a breakdown: subtotal, discount, tax, and final total."""
        cart = self.carts.get(cart_id)
        if cart is None:
            raise CartError(f"No such cart: {cart_id}")

        subtotal = cart.subtotal_cents
        discount_pct = self._coupons.get(cart.coupon_code, 0.0) if cart.coupon_code else 0.0
        discount = round(subtotal * discount_pct)
        taxable_amount = subtotal - discount
        tax = round(taxable_amount * self.tax_rate)
        total = taxable_amount + tax

        return {
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "tax_cents": tax,
            "total_cents": total,
        }

    def checkout(self, cart_id: str) -> dict[str, int]:
        """Finalize the cart: lock it from further edits and return the
        final price breakdown for order creation."""
        cart = self._get_active_cart(cart_id)
        if cart.item_count == 0:
            raise CartError("Cannot checkout an empty cart")

        breakdown = self.calculate_total_cents(cart_id)
        cart.status = CartStatus.CHECKED_OUT
        return breakdown

    def abandon_cart(self, cart_id: str) -> Cart:
        cart = self._get_active_cart(cart_id)
        cart.status = CartStatus.ABANDONED
        return cart

    def _get_active_cart(self, cart_id: str) -> Cart:
        cart = self.carts.get(cart_id)
        if cart is None:
            raise CartError(f"No such cart: {cart_id}")
        if cart.status != CartStatus.ACTIVE:
            raise CartError(f"Cart is not active (status: {cart.status.value})")
        return cart
