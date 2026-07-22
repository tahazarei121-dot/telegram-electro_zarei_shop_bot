"""سرویس مدیریت کاربران شامل ثبت‌نام و ویرایش پروفایل."""

from typing import List, Optional

from config import settings
from database.repositories.user_repository import UserRepository
from models.user import User
from services.logging_service import ActivityLogService


class UserService:
    """منطق کسب‌وکار مربوط به کاربران."""

    def __init__(self, user_repository: UserRepository, log_service: ActivityLogService) -> None:
        self._user_repository = user_repository
        self._log_service = log_service

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        return await self._user_repository.get_by_telegram_id(telegram_id)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self._user_repository.get_by_id(user_id)

    async def is_registered(self, telegram_id: int) -> bool:
        user = await self.get_user_by_telegram_id(telegram_id)
        return user is not None

    async def register_user(self, telegram_id: int, full_name: str,
                             phone_number: str, username: Optional[str]) -> User:
        existing = await self.get_user_by_telegram_id(telegram_id)
        if existing:
            return existing

        is_admin = telegram_id in settings.admin_ids
        user = await self._user_repository.create(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            is_admin=is_admin,
        )
        await self._user_repository.update_phone(user.id, phone_number)
        user.phone_number = phone_number
        await self._log_service.log(user.id, "USER_REGISTERED", f"کاربر جدید ثبت‌نام کرد: {full_name}")
        return user

    async def update_profile(self, user_id: int, full_name: Optional[str] = None,
                              phone_number: Optional[str] = None) -> None:
        if full_name:
            await self._user_repository.update_full_name(user_id, full_name)
        if phone_number:
            await self._user_repository.update_phone(user_id, phone_number)
        await self._log_service.log(user_id, "PROFILE_UPDATED", "اطلاعات پروفایل بروزرسانی شد.")

    async def block_user(self, user_id: int) -> None:
        await self._user_repository.set_blocked(user_id, True)
        await self._log_service.log(user_id, "USER_BLOCKED", "کاربر توسط ادمین مسدود شد.")

    async def unblock_user(self, user_id: int) -> None:
        await self._user_repository.set_blocked(user_id, False)
        await self._log_service.log(user_id, "USER_UNBLOCKED", "کاربر توسط ادمین رفع مسدودیت شد.")

    async def get_all_users(self) -> List[User]:
        return await self._user_repository.get_all()

    async def get_all_active_telegram_ids(self) -> List[int]:
        return await self._user_repository.get_all_active_telegram_ids()

    async def count_users(self) -> int:
        return await self._user_repository.count_all()

    async def count_new_users_since(self, since_datetime: str) -> int:
        return await self._user_repository.count_new_since(since_datetime)

    def is_admin(self, telegram_id: int) -> bool:
        return telegram_id in settings.admin_ids
