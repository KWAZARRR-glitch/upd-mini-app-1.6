import telebot
import json
import time
import os
from threading import Thread
from datetime import datetime

# ⚠️ ЗАМЕНИТЕ НА ВАШ ТОКЕН ОТ @BotFather ⚠️
BOT_TOKEN = "8390334481:AAGM-WTxKe88otShhQYK-YaSlWXKqcLg0fQ"

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище игр
user_games = {}

class ClickerGame:
    def init(self, user_id):
        self.user_id = user_id
        self.score = 0
        self.click_power = 1
        self.auto_click_power = 0
        self.bonus_multiplier = 1
        self.bonus_time = 0
        self.total_clicks = 0
        self.prestige_level = 0
        self.prestige_bonus = 1.0  # 1.0 = 100%, 1.1 = 110% и т.д.
        self.last_auto_click = time.time()
        self.created_at = datetime.now().strftime("%d.%m.%Y %H:%M")
        
    def click(self):
        """Обработка клика с учетом престиж-бонуса"""
        points = self.click_power * self.bonus_multiplier * self.prestige_bonus
        self.score += points
        self.total_clicks += 1
        return int(points)
        
    def buy_upgrade(self, upgrade_type, index):
        """Покупка улучшений"""
        upgrades = {
            'click': [
                {'cost': 10, 'power': 1, 'name': 'Ручка для кликов'},
                {'cost': 100, 'power': 5, 'name': 'Волшебная мышка'},
                {'cost': 1000, 'power': 25, 'name': 'Квантовый кликер'}
            ],
            'auto': [
                {'cost': 50, 'power': 1, 'name': 'Маленький бот'},
                {'cost': 500, 'power': 5, 'name': 'Ферма кликов'},
                {'cost': 5000, 'power': 25, 'name': 'ИИ Кликер 9000'}
            ],
            'bonus': [
                {'cost': 200, 'multiplier': 2, 'duration': 30, 'name': 'Энергия x2'},
                {'cost': 1000, 'multiplier': 3, 'duration': 20, 'name': 'Безумие x3'},
                {'cost': 5000, 'multiplier': 5, 'duration': 15, 'name': 'БОГ x5'}
            ]
        }
        
        upgrade = upgrades[upgrade_type][index]
        
        if self.score >= upgrade['cost']:
            self.score -= upgrade['cost']
            
            if upgrade_type == 'click':
                self.click_power += upgrade['power']
            elif upgrade_type == 'auto':
                self.auto_click_power += upgrade['power']
            elif upgrade_type == 'bonus':
                self.activate_bonus(upgrade['multiplier'], upgrade['duration'])
                
            return True, upgrade['name']
        return False, upgrade['name']
    
    def activate_bonus(self, multiplier, duration):
        """Активация бонуса"""
        self.bonus_multiplier = multiplier
        self.bonus_time = duration
        
        def bonus_timer():
            remaining = duration
            while remaining > 0:
                time.sleep(1)
                remaining -= 1
                self.bonus_time = remaining
            self.bonus_multiplier = 1
            
        Thread(target=bonus_timer, daemon=True).start()
    
    def can_prestige(self):
        """Проверка возможности престижа"""
        requirement = self.get_prestige_requirement()
        return self.score >= requirement
    
    def get_prestige_requirement(self):
        """Расчет требования для престижа"""
        base_requirement = 1000000  # 1M очков для первого престижа
        return base_requirement * (2 ** self.prestige_level)  # Удваивается каждый раз
    
    def get_prestige_progress(self):
        """Прогресс до следующего престижа"""
        requirement = self.get_prestige_requirement()
        progress = (self.score / requirement) * 100
        return min(progress, 100)
    
    def prestige(self):
        """Выполнение престижа"""
        if self.can_prestige():
            requirement = self.get_prestige_requirement()
            old_level = self.prestige_level
            
            # Увеличиваем уровень престижа
            self.prestige_level += 1
            # Увеличиваем бонус (+10% за уровень)
            self.prestige_bonus = 1.0 + (self.prestige_level * 0.10)
            
            # Сохраняем престиж-статистику перед сбросом
            total_earned = self.score
            
            # Сбрасываем прогресс (но сохраняем престиж уровень и бонус)
            self.score = 0
            self.click_power = 1
            self.auto_click_power = 0
            self.bonus_multiplier = 1
            self.total_clicks = 0
            self.bonus_time = 0
            
            return True, old_level, total_earned, requirement
        return False, self.prestige_level, self.score, self.get_prestige_requirement()

    def to_dict(self):
        """Для сохранения в файл"""
        return self.dict.copy()
    
    @classmethod
    def from_dict(cls, data):
        """Для загрузки из файла"""
        game = cls(data['user_id'])
        for key, value in data.items():
            setattr(game, key, value)
        return game

# Система сохранения
class GameStorage:
    def init(self, filename='telegram_clicker_data.json'):
        self.filename = filename
        self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, game_data in data.items():
                        user_games[int(user_id)] = ClickerGame.from_dict(game_data)
                print(f"✅ Загружено {len(user_games)} игр")
            except Exception as e:
                print(f"❌ Ошибка загрузки: {e}")
    
    def save_data(self):
        try:
            data = {}
            for user_id, game in user_games.items():
                data[str(user_id)] = game.to_dict()
            
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")

storage = GameStorage()

# Авто-кликер
def auto_click_loop():
    while True:
        current_time = time.time()
        for user_id, game in user_games.items():
            if game.auto_click_power > 0 and current_time - game.last_auto_click >= 1:
                points = game.auto_click_power * game.bonus_multiplier * game.prestige_bonus
                game.score += points
                game.last_auto_click = current_time
        time.sleep(1)

# Авто-сохранение
def auto_save_loop():
    while True:
        storage.save_data()
        time.sleep(30)

Thread(target=auto_click_loop, daemon=True).start()
Thread(target=auto_save_loop, daemon=True).start()

# ===== ТЕЛЕГРАМ КОМАНДЫ =====

@bot.message_handler(commands=['start'])
def start_game(message):
    user_id = message.from_user.id
    username = message.from_user.first_name
    
    if user_id not in user_games:
        user_games[user_id] = ClickerGame(user_id)
        bot.send_message(message.chat.id, 
                        f"🎮 Привет, {username}! Добро пожаловать в *Ква Кликер*!\n\n"
                        f"🌟 *Новая функция:* Система престижа!\n"
                        f"Зарабатывай 1M очков и получай +10% к доходу!",
                        parse_mode='Markdown')
    else:
        game = user_games[user_id]
        if game.prestige_level > 0:
            bot.send_message(message.chat.id,
                           f"🔄 Возвращаемся к игре, {username}!\n"
                           f"⭐ Уровень престижа: {game.prestige_level}\n"
                           f"💫 Бонус: +{int((game.prestige_bonus - 1) * 100)}% к доходу",
                           parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"🔄 Возвращаемся к игре, {username}!")
    
    show_main_menu(message)
   def show_main_menu(message):
    user_id = message.from_user.id
    if user_id not in user_games:
        user_games[user_id] = ClickerGame(user_id)
    
    game = user_games[user_id]
    
    menu_text = f"""
🎮 *МЕГА КЛИКЕР БОТ* 🎮

💎 *Очков:* {format_number(game.score)}
💪 *Сила клика:* {game.click_power}
🤖 *Авто-кликов/сек:* {game.auto_click_power}
🎯 *Множитель:* x{game.bonus_multiplier}
👆 *Всего кликов:* {format_number(game.total_clicks)}

*Выберите действие:*
    """
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton('👆 КЛИКНУТЬ!', callback_data='click'),
        telebot.types.InlineKeyboardButton('🛠 УЛУЧШЕНИЯ', callback_data='upgrades')
    )
    # ↓↓↓ ДОБАВЬТЕ ЭТУ СТРОЧКУ ↓↓↓
    markup.row(
        telebot.types.InlineKeyboardButton('🌟 ПРЕСТИЖ', callback_data='prestige'),
        telebot.types.InlineKeyboardButton('📊 СТАТИСТИКА', callback_data='stats')
    )
    # ↑↑↑ ДОБАВЬТЕ ЭТУ СТРОЧКУ ↑↑↑
    
    try:
        bot.edit_message_text(
            menu_text,
            message.chat.id,
            message.message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            menu_text,
            parse_mode='Markdown',
            reply_markup=markup
        )
        @bot.message_handler(commands=['testprestige'])
def test_prestige(message):
    user_id = message.from_user.id
    if user_id not in user_games:
        user_games[user_id] = ClickerGame(user_id)
    
    game = user_games[user_id]
    # Даем много очков для теста
    game.score = 1500000
    show_prestige_menu(message, game)

def show_prestige_menu(message, game):
    requirement = game.get_prestige_requirement()
    progress = game.get_prestige_progress()
    can_prestige = game.can_prestige()
    
    prestige_text = f"""
🌟 *СИСТЕМА ПРЕСТИЖА* 🌟

*Текущий уровень:* {game.prestige_level}
*Бонус дохода:* +{int((game.prestige_bonus - 1) * 100)}%

*Следующий престиж:*
Требуется: {format_number(requirement)} очков
Ваш прогресс: {progress:.1f}%
Ваши очки: {format_number(game.score)}

💡 *Престиж сбрасывает прогресс, но дает +10% к доходу навсегда!*

{'🚀 *ВЫ МОЖЕТЕ ВЫПОЛНИТЬ ПРЕСТИЖ!*' if can_prestige else '❌ *Недостаточно очков для престижа*'}
    """
    
    markup = telebot.types.InlineKeyboardMarkup()
    if can_prestige:
        markup.add(telebot.types.InlineKeyboardButton(
            '🚀 ВЫПОЛНИТЬ ПРЕСТИЖ!', 
            callback_data='do_prestige'
        ))
    markup.add(telebot.types.InlineKeyboardButton('🔙 НАЗАД', callback_data='main_menu'))
    
    bot.edit_message_text(
        prestige_text,
        message.chat.id,
        message.message_id,
        parse_mode='Markdown',
        reply_markup=markup
    )

def show_stats_menu(message, game):
    total_multiplier = game.bonus_multiplier * game.prestige_bonus
    prestige_bonus_percent = int((game.prestige_bonus - 1) * 100)
    
    stats_text = f"""
📊 *ВАША СТАТИСТИКА* 📊

💎 *Всего очков:* {format_number(game.score)}
💪 *Сила клика:* {game.click_power}
🤖 *Авто-кликов:* {game.auto_click_power}/сек
🎯 *Множитель:* x{total_multiplier:.1f}
⭐ *Уровень престижа:* {game.prestige_level}
💫 *Престиж бонус:* +{prestige_bonus_percent}%
👆 *Всего кликов:* {format_number(game.total_clicks)}

⏰ *Бонус время:* {game.bonus_time}сек
📅 *Играет с:* {game.created_at}
    """
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('🔙 НАЗАД', callback_data='main_menu'))
    
    bot.edit_message_text(
        stats_text,
        message.chat.id,
        message.message_id,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    
    if user_id not in user_games:
        user_games[user_id] = ClickerGame(user_id)
    
    game = user_games[user_id]
    
    if call.data == 'click':
        points = game.click()
        bot.answer_callback_query(call.id, f"💎 +{points} очков!")
        show_main_menu(call.message)
        
    elif call.data == 'upgrades':
        show_upgrades_menu(call.message, game)
        
    elif call.data == 'prestige':
        show_prestige_menu(call.message, game)
        
    elif call.data == 'stats':
        show_stats_menu(call.message, game)
        
    elif call.data == 'main_menu':
        show_main_menu(call.message)
        
    elif call.data == 'do_prestige':
        success, old_level, total_earned, requirement = game.prestige()
        if success:
            bot.answer_callback_query(
                call.id, 
                f"🌟 Престиж {game.prestige_level} достигнут! +10% к доходу"
            )
            # Отправляем поздравительное сообщение
            bot.send_message(
                call.message.chat.id,
                f"🎉 *ПОЗДРАВЛЯЕМ С ПРЕСТИЖЕМ!* 🎉\n\n"
                f"⭐ Новый уровень: {game.prestige_level}\n"
                f"💫 Бонус дохода: +{int((game.prestige_bonus - 1) * 100)}%\n"
                f"💎 Заработано для престижа: {format_number(total_earned)}\n"
                f"🎯 Следующая цель: {format_number(requirement)} очков\n\n"
                f"_Ваш прогресс сброшен, но бонус остаётся навсегда!_",
                parse_mode='Markdown'
            )
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно очков для престижа!")
        show_main_menu(call.message)
        
    elif call.data.startswith('buy_'):
        parts = call.data.split('_')
        upgrade_type = parts[1]
        index = int(parts[2])
        
        success, name = game.buy_upgrade(upgrade_type, index)
        if success:
            bot.answer_callback_query(call.id, f"✅ Куплено: {name}!")
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно очков!")
        
        if upgrade_type == 'bonus':
            show_main_menu(call.message)
        else:
            show_upgrades_menu(call.message, game)

def show_upgrades_menu(message, game):
    """Магазин улучшений (оставьте ваш существующий код)"""
    # ... ваш существующий код магазина улучшений

def format_number(num):
    """Форматирование чисел"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    if num >= 1000:
        return f"{num/1000:.1f}K"
    return str(int(num))

# Запуск бота
if name == "main":
    print("🎮 Telegram Кликер Бот с престижем запущен!")
    print("📍 Ищите бота в Telegram")
    print("🌟 Система престижа активна!")
    bot.polling(none_stop=True)