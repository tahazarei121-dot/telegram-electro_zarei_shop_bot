"""تست‌های واحد (Integration) برای ProductService با استفاده از پایگاه داده SQLite در حافظه."""

import sys
from pathlib import Path

import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import DatabaseManager
from database.repositories.category_repository import CategoryRepository
from database.repositories.log_repository import LogRepository
from database.repositories.product_repository import ProductRepository
from services.category_service import CategoryService
from services.logging_service import ActivityLogService
from services.product_service import ProductService


@pytest_asyncio.fixture
async def db_manager():
    manager = DatabaseManager(Path(":memory:"))
    await manager.connect()
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def product_service(db_manager):
    log_repo = LogRepository(db_manager)
    log_service = ActivityLogService(log_repo)
    category_repo = CategoryRepository(db_manager)
    category_service = CategoryService(category_repo, log_service)
    product_repo = ProductRepository(db_manager)
    service = ProductService(product_repo, log_service)

    _, _, category = await category_service.create_category("لوازم الکترونیکی", "دسته تست", admin_id=1)
    return service, category.id


@pytest.mark.asyncio
async def test_create_product_success(product_service):
    service, category_id = product_service
    success, message, product = await service.create_product(
        category_id=category_id, name="هدفون بی‌سیم", description="توضیح تستی",
        price=500000, stock=10, admin_id=1,
    )
    assert success is True
    assert product is not None
    assert product.name == "هدفون بی‌سیم"
    assert product.stock == 10


@pytest.mark.asyncio
async def test_update_stock(product_service):
    service, category_id = product_service
    _, _, product = await service.create_product(
        category_id=category_id, name="ماوس", description="", price=100000, stock=5, admin_id=1,
    )
    success, message = await service.update_stock(product.id, 20, admin_id=1)
    assert success is True

    refreshed = await service.get_product(product.id)
    assert refreshed.stock == 20


@pytest.mark.asyncio
async def test_search_products(product_service):
    service, category_id = product_service
    await service.create_product(
        category_id=category_id, name="کیبورد مکانیکی", description="", price=800000, stock=3, admin_id=1,
    )
    results, total = await service.search_products("کیبورد")
    assert total == 1
    assert results[0].name == "کیبورد مکانیکی"
