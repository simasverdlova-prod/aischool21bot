import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from anthropic import Anthropic

# Токены и ключи из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Инициализация Claude
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# Функция для проверки нейросети
def check_neural_network(url, name):
    """Проверяет нейросеть по трём критериям"""
    result = {
        "name": name,
        "url": url,
        "russia_access": "❓",
        "free_demo": "❓",
        "registration": "❓"
    }
    
    # 1. Проверяем доступность в РФ
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result["russia_access"] = "✅ Да"
        else:
            result["russia_access"] = f"❌ Ошибка {response.status_code}"
    except:
        result["russia_access"] = "❌ Недоступен или блокировка"
    
    # 2. Ищем информацию на странице
    try:
        text = response.text.lower() if 'response' in locals() else ""
        
        # Проверка демо-доступа
        if any(word in text for word in ["free", "бесплатно", "free trial", "demo", "free plan"]):
            result["free_demo"] = "✅ Есть"
        elif any(word in text for word in ["pricing", "платно", "subscribe", "подписка"]):
            result["free_demo"] = "❌ Только платно"
        else:
            result["free_demo"] = "❓ Нет данных"
        
        # Проверка регистрации
        if any(word in text for word in ["sign up", "register", "login", "войти", "зарегистрироваться"]):
            result["registration"] = "✅ Нужна"
        else:
            result["registration"] = "✅ Не нужна"
    except:
        pass
    
    return result

# Команда /start
async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 *Привет! Я бот для проверки нейросетей*\n\n"
        "Просто отправь мне список нейросетей в формате:\n"
        "`Название https://ссылка.ком`\n\n"
        "*Пример:*\n"
        "`DeepSeek https://chat.deepseek.com`\n"
        "`ChatGPT https://chat.openai.com`\n\n"
        "Я проверю:\n"
        "• Работает ли в РФ без VPN\n"
        "• Есть ли бесплатный демо-доступ\n"
        "• Нужна ли регистрация",
        parse_mode="Markdown"
    )

# Обработка сообщений со списком нейросетей
async def handle_message(update: Update, context):
    text = update.message.text
    
    # Ищем в сообщении строки вида "Название https://..."
    lines = text.split('\n')
    networks = []
    
    for line in lines:
        # Ищем URL в строке
        urls = re.findall(r'https?://[^\s]+', line)
        if urls:
            # Название — всё, что до первого URL
            name_part = line.split(urls[0])[0].strip()
            if not name_part:
                name_part = "Нейросеть"
            networks.append((name_part, urls[0]))
    
    if not networks:
        await update.message.reply_text(
            "❌ Не нашёл ссылок. Отправьте список в формате:\n"
            "`Название https://ссылка.ком`",
            parse_mode="Markdown"
        )
        return
    
    # Сообщаем о начале проверки
    status_msg = await update.message.reply_text(
        f"🔍 Начинаю проверку {len(networks)} нейросетей...\n"
        "⏳ Это может занять 10–30 секунд"
    )
    
    # Проверяем каждую нейросеть
    results = []
    for name, url in networks:
        result = check_neural_network(url, name)
        results.append(result)
    
    # Формируем таблицу с результатами
    table = "📊 *Результаты проверки:*\n\n"
    table += "| Нейросеть | Доступ в РФ | Демо-доступ | Регистрация |\n"
    table += "|-----------|-------------|-------------|-------------|\n"
    
    for r in results:
        table += f"| {r['name']} | {r['russia_access']} | {r['free_demo']} | {r['registration']} |\n"
    
    # Отправляем результат
    await status_msg.edit_text(table, parse_mode="Markdown")

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
