"""تست‌های واحد (Integration) برای CartService با استفاده از پایگاه داده SQLite در حافظه."""

import sys
from pathlib import Path

import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import DatabaseManager
from database.repositories.cart_repository import CartRepository
from database.repositories.category_repository import CategoryRepository
from database.repositories.log_repository import LogRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.user_repository import UserRepository
from services.cart_service import CartService
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
async def setup_data(db_manager):
    log_repo = LogRepository(db_manager)
    log_service = ActivityLogService(log_repo)

    category_repo = CategoryRepository(db_manager)
    category_service = CategoryService(category_repo, log_service)
    _, _, category = await category_service.create_category("دسته تست", None, admin_id=1)

    product_repo = ProductRepository(db_manager)
    product_service = ProductService(product_repo, log_service)
    _, _, product = await product_service.create_product(
        category_id=category.id, name="محصول تستی", description="", price=200000, stock=3, admin_id=1,
    )

    user_repo = UserRepository(db_manager)
    user = await user_repo.create(telegram_id=123456, full_name="کاربر تست", username="test_user")

    cart_repo = CartRepository(db_manager)
    cart_service = CartService(cart_repo, product_repo, log_service)

    return cart_service, user.id, product.id


@pytest.mark.asyncio
async def test_add_to_cart_success(setup_data):
    cart_service, user_id, product_id = setup_data
    success, message = await cart_service.add_to_cart(user_id, product_id, quantity=2)
    assert success is True

    items = await cart_service.get_cart(user_id)
    assert len(items) == 1
    assert items[0].quantity == 2


@pytest.mark.asyncio
async def test_add_to_cart_exceeds_stock(setup_data):
    cart_service, user_id, product_id = setup_data
    success, message = await cart_service.add_to_cart(user_id, product_id, quantity=10)
    assert success is False
    assert "موجودی" in message


@pytest.mark.asyncio
async def test_remove_from_cart(setup_data):
    cart_service, user_id, product_id = setup_data
    await cart_service.add_to_cart(user_id, product_id, quantity=1)
    await cart_service.remove_from_cart(user_id, product_id)

    items = await cart_service.get_cart(user_id)
    assert len(items) == 0
