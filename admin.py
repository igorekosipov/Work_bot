from aiogram import Router, types, F
from datetime import datetime, timedelta
from database import (get_pending_checks, update_check_status, get_check_by_id,
                      update_subscription, get_user, is_admin)
from keyboards.admin_panel import get_admin_panel_keyboard
from keyboards.subscription import get_admin_check_keyboard
from keyboards.main_menu import get_main_menu

router = Router()


@router.message(lambda m: m.text == "🔧 Админ-панель")
async def admin_panel(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора.")
        return

    await message.answer("🔧 Админ-панель:", reply_markup=get_admin_panel_keyboard())


@router.message(lambda m: m.text == "📋 Непроверенные чеки")
async def show_pending_checks(message: types.Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав администратора.")
        return

    checks = await get_pending_checks()
    if not checks:
        await message.answer("Нет ожидающих проверки чеков.")
        return

    for check in checks:
        check_id = check[0]
        user_id = check[1]
        file_id = check[2]
        amount = check[3]
        plan = check[4]

        user = await get_user(user_id)
        if user:
            user_info = f"{user['first_name']}"
            if user['username']:
                user_info += f" (@{user['username']})"
        else:
            user_info = str(user_id)

        caption = f"Чек #{check_id}\nОт: {user_info}\nСумма: {amount}₽\nТариф: {plan}"

        try:
            await message.answer_photo(
                file_id,
                caption=caption,
                reply_markup=get_admin_check_keyboard(check_id)
            )
        except:
            await message.answer(f"{caption}\n(Фото не найдено)")


@router.callback_query(F.data.startswith("admin_confirm:"))
async def confirm_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет прав администратора", show_alert=True)
        return

    check_id = int(callback.data.split(":")[1])
    check = await get_check_by_id(check_id)

    if not check:
        await callback.answer("Чек не найден.")
        return

    user_id = check[1]
    plan = check[4]

    # Определяем количество дней подписки
    if plan == "monthly":
        days_to_add = 30
    elif plan == "half_year":
        days_to_add = 180
    else:
        days_to_add = 30

    # Получаем текущую дату окончания подписки пользователя
    user = await get_user(user_id)
    now = datetime.now()

    if user and user["subscription_end"]:
        try:
            current_end = datetime.fromisoformat(user["subscription_end"])
            # Если подписка ещё активна - добавляем дни к концу подписки
            if current_end > now:
                new_end = current_end + timedelta(days=days_to_add)
            else:
                # Если подписка истекла - начинаем с текущей даты
                new_end = now + timedelta(days=days_to_add)
        except:
            new_end = now + timedelta(days=days_to_add)
    else:
        # Если подписки нет - начинаем с текущей даты
        new_end = now + timedelta(days=days_to_add)

    # Сохраняем новую дату
    await update_subscription(user_id, new_end.isoformat())

    # Обновляем статус чека
    await update_check_status(check_id, "confirmed")

    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            user_id,
            f"✅ Ваша подписка подтверждена!\n"
            f"Действует до: {new_end.strftime('%d.%m.%Y')}\n"
            f"Добавлено дней: {days_to_add}"
        )
    except:
        pass

    # Обновляем сообщение с чеком
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n✅ ПОДТВЕРЖДЕНО\nПодписка до: {new_end.strftime('%d.%m.%Y')}"
        )
    except:
        pass

    await callback.answer("✅ Подписка подтверждена")


@router.callback_query(F.data.startswith("admin_decline:"))
async def decline_payment(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет прав администратора", show_alert=True)
        return

    check_id = int(callback.data.split(":")[1])
    check = await get_check_by_id(check_id)

    if not check:
        await callback.answer("Чек не найден.")
        return

    user_id = check[1]

    # Обновляем статус чека
    await update_check_status(check_id, "declined")

    # Уведомляем пользователя
    try:
        await callback.bot.send_message(
            user_id,
            "❌ Ваш платёж не подтверждён. Свяжитесь с поддержкой."
        )
    except:
        pass

    # Обновляем сообщение с чеком
    try:
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ ОТКЛОНЕНО"
        )
    except:
        pass

    await callback.answer("❌ Платёж отклонён")


@router.message(lambda m: m.text == "🔙 Главное меню")
async def back_to_menu(message: types.Message):
    await message.answer("Главное меню", reply_markup=get_main_menu(await is_admin(message.from_user.id)))