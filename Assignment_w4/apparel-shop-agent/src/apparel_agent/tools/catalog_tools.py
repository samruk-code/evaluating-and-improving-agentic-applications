from __future__ import annotations

from apparel_agent.data.repository import ApparelRepository


def search_catalog(repo: ApparelRepository, query: str, filters: dict | None = None) -> dict:
    return repo.search_catalog(query=query, filters=filters)


def get_product_details(repo: ApparelRepository, product_id: str) -> dict:
    return repo.get_product_details(product_id=product_id)

