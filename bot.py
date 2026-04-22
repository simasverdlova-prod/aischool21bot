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
            "`Название https://ссылка.ком`\n\n"
            "Пример:\n"
            "`DeepSeek https://chat.deepseek.com`",
            parse_mode="Markdown"
        )
        return
    
    # Сообщаем о начале проверки
    status_msg = await update.message.reply_text(
        f"🔍 Проверяю {len(networks)} нейросетей...\n"
        "⏳ Это займёт 10–30 секунд"
    )
    
    # Проверяем каждую нейросеть
    results = []
    for name, url in networks:
        result = check_neural_network(url, name)
        results.append(result)
    
    # Формируем ответ в виде списка (без таблицы)
    response = "📊 *РЕЗУЛЬТАТЫ ПРОВЕРКИ:*\n\n"
    
    for i, r in enumerate(results, 1):
        # Номер и название
        if i == 1:
            response += f"1️⃣ *{r['name']}*\n"
        elif i == 2:
            response += f"2️⃣ *{r['name']}*\n"
        elif i == 3:
            response += f"3️⃣ *{r['name']}*\n"
        elif i == 4:
            response += f"4️⃣ *{r['name']}*\n"
        elif i == 5:
            response += f"5️⃣ *{r['name']}*\n"
        else:
            response += f"{i}️⃣ *{r['name']}*\n"
        
        response += f"   🔗 {r['url']}\n"
        response += f"   🌐 Доступ в РФ: {r['russia_access']}\n"
        response += f"   🆓 Бесплатный демо: {r['free_demo']}\n"
        response += f"   📝 Регистрация: {r['registration']}\n\n"
    
    # Добавляем итоги
    response += "━━━━━━━━━━━━━━━━━━━━━━\n"
    response += f"💡 *Итого:* {len(results)} нейросетей проверено\n"
    
    # Считаем статистику
    russia_ok = sum(1 for r in results if "✅ Да" in r['russia_access'])
    free_ok = sum(1 for r in results if "✅ Есть" in r['free_demo'])
    
    response += f"🌐 Работают в РФ: {russia_ok} из {len(results)}\n"
    response += f"🆓 Есть бесплатный доступ: {free_ok} из {len(results)}"
    
    # Отправляем результат
    await status_msg.edit_text(response, parse_mode="Markdown")

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
