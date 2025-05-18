from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, InlineKeyboardMarkup,
                           InlineKeyboardButton, CallbackQuery,
                           KeyboardButton, ReplyKeyboardRemove)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.formatting import as_marked_list
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from services.load_resume import load_stack, load_about_me
from services.yandex_client import ask_yandex_gpt
from constants import COMMANDS_WITH_DESCRIPTION
from bot_logging import bot_logger

router = Router()


class ChatMode(StatesGroup):
    talking_to_ai = State()


@router.message(Command("start"))
async def start_command(message: Message):
    name = message.from_user.first_name
    ai_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💬 Поговорить с ИИ о резюме",
            callback_data="talk_to_ai")]
    ])
    await message.answer(
        f"*Привет, {name}👋*\nЯ бот Кирилла🤖\n"
        "Ты можешь задать мне любой вопрос по резюме нажав"
        " на 'Поговорить с ИИ о резюме'"
        " — я отвечу как кандидат\n\n"
        f"*Вот что я умею:*\n{COMMANDS_WITH_DESCRIPTION}",
        reply_markup=ai_button,
    )


@router.message(Command("about_kirill"))
async def start_command(message: Message):
    await message.answer(load_about_me())


@router.message(Command("short_stack"))
async def short_stack_command(message: Message):
    stack = load_stack().split(sep="\n")

    content = as_marked_list(
        *stack,
        marker="➡️ ",
    )
    await message.answer(**content.as_kwargs())


@router.message(Command("help"))
async def help_command(message: Message):
    user_message = f"Все команды:\n\n{COMMANDS_WITH_DESCRIPTION}"
    await message.answer(user_message)


@router.callback_query(F.data == "talk_to_ai")
async def talk_to_ai_handler(callback: CallbackQuery, state: FSMContext):
    stop_button = KeyboardButton(text="❌ Остановить разговор с ИИ")
    builder = ReplyKeyboardBuilder()
    builder.row(stop_button)
    stop_keyboard = builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Введите свой вопрос..."
    )
    await callback.message.answer(
        "Напиши свой вопрос, и я постараюсь ответить как кандидат 👨‍💼\n"
        "Если хотите связаться с Кириллом, то напишите ИИ, "
        "что вы заинтересованы в нем😊",
        reply_markup=stop_keyboard
    )
    await state.set_state(ChatMode.talking_to_ai)
    await callback.answer(text="Вы начали разговор с ИИ")


@router.message(F.text == "❌ Остановить разговор с ИИ")
async def stop_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "ИИ режим отключён\n"
        "Ты можешь снова начать, нажав кнопку на /start",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True)
    )


@router.message(ChatMode.talking_to_ai, flags={"chat_action": "typing"})
async def handle_ai_question(message: Message):
    reply = await ask_yandex_gpt(message.text)
    await message.reply(f"`{reply}`", )


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ChatMode.talking_to_ai:
        return

    await message.reply(
        "🤖 Я не понял твоё сообщение."
        " Чтобы начать разговор с ИИ, нажми на кнопку в /start. "
    )
