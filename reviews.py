"""Product review and rating system for ecommerce-lite."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Optional


class ReviewError(Exception):
    """Raised for invalid review operations."""


@dataclass
class Review:
    review_id: str
    product_id: str
    customer_id: str
    rating: int
    title: str = ""
    body: str = ""
    verified_purchase: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    helpful_votes: int = 0
    flagged: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ReviewError("rating must be between 1 and 5")


class ReviewStore:
    """In-memory store for product reviews with basic moderation."""

    def __init__(self):
        self._reviews: dict[str, Review] = {}
        self._by_product: dict[str, list[str]] = {}
        self._customer_product_seen: set[tuple[str, str]] = set()

    def add_review(
        self,
        review_id: str,
        product_id: str,
        customer_id: str,
        rating: int,
        title: str = "",
        body: str = "",
        verified_purchase: bool = False,
    ) -> Review:
        key = (customer_id, product_id)
        if key in self._customer_product_seen:
            raise ReviewError("Customer has already reviewed this product")

        review = Review(
            review_id=review_id,
            product_id=product_id,
            customer_id=customer_id,
            rating=rating,
            title=title,
            body=body,
            verified_purchase=verified_purchase,
        )
        self._reviews[review_id] = review
        self._by_product.setdefault(product_id, []).append(review_id)
        self._customer_product_seen.add(key)
        return review

    def get_reviews_for_product(self, product_id: str, include_flagged: bool = False) -> list[Review]:
        review_ids = self._by_product.get(product_id, [])
        reviews = [self._reviews[rid] for rid in review_ids]
        if not include_flagged:
            reviews = [r for r in reviews if not r.flagged]
        return reviews

    def average_rating(self, product_id: str) -> Optional[float]:
        reviews = self.get_reviews_for_product(product_id)
        if not reviews:
            return None
        return round(mean(r.rating for r in reviews), 2)

    def rating_breakdown(self, product_id: str) -> dict[int, int]:
        breakdown = {i: 0 for i in range(1, 6)}
        for review in self.get_reviews_for_product(product_id):
            breakdown[review.rating] += 1
        return breakdown

    def mark_helpful(self, review_id: str) -> Review:
        review = self._get(review_id)
        review.helpful_votes += 1
        return review

    def flag_review(self, review_id: str, reason: str = "") -> Review:
        review = self._get(review_id)
        review.flagged = True
        return review

    def top_reviews(self, product_id: str, limit: int = 3) -> list[Review]:
        reviews = self.get_reviews_for_product(product_id)
        return sorted(reviews, key=lambda r: r.helpful_votes, reverse=True)[:limit]

    def _get(self, review_id: str) -> Review:
        review = self._reviews.get(review_id)
        if review is None:
            raise ReviewError(f"No such review: {review_id}")
        return review
