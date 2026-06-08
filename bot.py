#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
777 BigWin Auto Bet Bot - Fixed Bet Multiplier on Lose
"""

import requests
import json
import time
import hashlib
import random
import threading
from datetime import datetime
from collections import deque, Counter

# ==================== CONFIG ====================
BOT_TOKEN = "8978079117:AAGyBY4g4uoB4yytKpTB2WCnLo-peQ3T6k8"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

API_BASE = "https://api.bigwinqaz.com/api/webapi/"

GAME_TYPES = {
    "1": {"name": "🎲 Wingo 30s",      "typeId": 30, "wait_sec": 28, "is_trx": False},
    "2": {"name": "⏱️ Wingo 1 Minute", "typeId": 1,  "wait_sec": 58, "is_trx": False},
    "3": {"name": "⚡ TRX Wingo 1 Minute", "typeId": 13, "wait_sec": 58, "is_trx": True},
}
DEFAULT_GAME_TYPE = "1"

BASE_AMOUNT = 10
DEFAULT_BETTING_SEQUENCE = [1, 3, 9, 27, 81, 243, 729, 2187] 

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://777bigwingame.vip",
    "Referer": "https://777bigwingame.vip/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== API CLASS ====================
class LotteryAPI:
    def __init__(self):
        self.headers = HEADERS.copy()
        self.token = ""

    def sign_md5(self, data_dict):
        sign_data = data_dict.copy()
        for k in ['signature','timestamp']:
            if k in sign_data: del sign_data[k]
        sorted_data = dict(sorted(sign_data.items()))
        hash_string = json.dumps(sorted_data, separators=(',', ':')).replace(' ', '')
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def random_key(self):
        xxxx = "xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx"
        return ''.join(random.choice('0123456789abcdef') if c=='x' else random.choice('89a') if c=='y' else c for c in xxxx)

    def login(self, phone, password):
        try:
            clean_phone = phone.replace("95", "") if phone.startswith("95") else phone
            username = f"95{clean_phone}"
            body = {
                "phonetype": -1, "language": 0, "logintype": "mobile",
                "random": "9078efc98754430e92e51da59eb2563c",
                "username": username, "pwd": password, "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}Login", headers=self.headers, json=body, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('msgCode') == 0:
                    tok = data.get('data', {})
                    self.token = f"{tok.get('tokenHeader','')}{tok.get('token','')}"
                    self.headers["Authorization"] = self.token
                    return True, "✅ Login Successful! (777 BigWin)"
                return False, data.get('msg', 'Login Failed')
            return False, f"API Error {resp.status_code}"
        except Exception as e:
            return False, f"Login Error: {e}"

    def get_balance(self):
        try:
            body = {"language":0,"random":"9078efc98754430e92e51da59eb2563c","timestamp":int(time.time())}
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}GetBalance", headers=self.headers, json=body, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    return float(d.get('data',{}).get('amount', 0))
            return 0.0
        except:
            return 0.0

    def get_current_issue(self, type_id):
        try:
            body = {"typeId": type_id, "language":0, "random":"b05034ba4a2642009350ee863f29e2e9", "timestamp":int(time.time())}
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}GetGameIssue", headers=self.headers, json=body, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    return d.get('data',{}).get('issueNumber','')
            return ""
        except:
            return ""

    def place_bet(self, issue, base_amount, bet_count, bet_type, type_id):
        try:
            body = {
                "typeId": type_id, "issuenumber": issue, "language": 0, "gameType": 2,
                "amount": base_amount, "betCount": bet_count, "selectType": bet_type,
                "random": self.random_key(), "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(f"{API_BASE}GameBetting", headers=self.headers, json=body, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('code') == 0 or d.get('msgCode') == 0:
                    total_bet = base_amount * bet_count
                    profit = int(total_bet * 0.96)
                    return True, "Bet placed", profit
                return False, d.get('msg','Bet failed'), 0
            return False, f"API error {resp.status_code}", 0
        except Exception as e:
            return False, f"Bet error: {e}", 0

    def get_recent_results(self, count, type_id, is_trx=False):
        try:
            if is_trx:
                endpoint = f"{API_BASE}GetTRXNoaverageEmerdList"
            else:
                endpoint = f"{API_BASE}GetNoaverageEmerdList"
            body = {
                "pageNo": 1, "pageSize": count, "language": 0, "typeId": type_id,
                "random": "6DEB0766860C42151A193692ED16D65A", "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = requests.post(endpoint, headers=self.headers, json=body, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    if is_trx:
                        games = d.get('data', {}).get('data', {}).get('gameslist', [])
                    else:
                        games = d.get('data', {}).get('list', [])
                    return games
            return []
        except:
            return []

# ==================== SESSION STORAGE ====================
user_sessions = {}

# ==================== TELEGRAM HELPERS ====================
def send_message(chat_id, text, reply_markup=None, **kwargs):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("result", [])
    except:
        pass
    return []

# ==================== KEYBOARDS ====================
def get_login_keyboard():
    return {"keyboard": [["🔐 Login"]], "resize_keyboard": True}

def get_main_keyboard():
    keyboard = [
        ["🎮 Game Type", "🧧 Bet Amount"],
        ["📚 Strategy", "🧧 Profit Target"],
        ["🛑 Stop Loss", "🔁 Layer"],
        ["🔄 Test Mode", "ℹ️ Info"],
        ["▶️ Start", "⏹️ Stop"],
        ["🚪 Logout"]
    ]
    return {"keyboard": keyboard, "resize_keyboard": True}

def get_game_type_keyboard():
    buttons = [[gt["name"]] for gt in GAME_TYPES.values()]
    buttons.append(["◀️ Back"])
    return {"keyboard": buttons, "resize_keyboard": True}

def get_strategy_keyboard():
    return {
        "keyboard": [
            ["📊 Pattern Analyzer", "🥇 Menus 1.6 Ultra"],
            ["🧠 Manus AI", "📈 Trend Follow"],
            ["🎨 Custom BS Pattern", "✨ Wingo Advanced"],
            ["◀️ Back"]
        ],
        "resize_keyboard": True
    }

# ==================== STRATEGY CLASSES ====================
class PatternAnalyzerStrategy:
    def __init__(self):
        self.recent_history = []
        self.max_history_length = 50
    def add_result(self, result):
        self.recent_history.append(result)
        if len(self.recent_history) > self.max_history_length:
            self.recent_history.pop(0)
    def predict(self):
        if len(self.recent_history) < 3:
            return random.choice(['B', 'S']), 0.5
        last = self.recent_history[-1]
        return ('B' if last == 'S' else 'S'), 0.6

class MenusUltraStrategy:
    def __init__(self):
        self.history = []
    def add_result(self, result):
        self.history.append(result)
        if len(self.history) > 50:
            self.history.pop(0)
    def predict(self):
        if len(self.history) < 5:
            return random.choice(['B', 'S']), 50
        scores = {'B': 0, 'S': 0}
        if self.history[0] == self.history[1] == self.history[2]:
            scores[self.history[0]] += 35
        if len(self.history) >= 4 and self.history[0] != self.history[1] and self.history[1] != self.history[2]:
            next_pred = 'B' if self.history[0] == 'S' else 'S'
            scores[next_pred] += 30
        freq = Counter(self.history[:10])
        if freq:
            scores[freq.most_common(1)[0][0]] += 25
        if len(self.history) >= 5 and self.history[0] == self.history[4] and self.history[1] == self.history[3]:
            scores[self.history[2]] += 10
        pred = 'B' if scores['B'] > scores['S'] else 'S'
        total = scores['B'] + scores['S']
        conf = min(99, int((scores[pred]/total)*100) + 35) if total > 0 else 50
        return pred, conf

class ManusAIStrategy:
    def __init__(self):
        self.last_result = 'B'
    def add_result(self, result):
        self.last_result = result
    def predict(self):
        return ('B' if self.last_result == 'S' else 'S'), 70

class TrendFollowStrategy:
    def __init__(self):
        self.history = []
        self.cycle_count = 0
    def add_result(self, result):
        self.history.append(result)
        self.cycle_count = len(self.history) % 6
    def predict(self):
        if len(self.history) < 1:
            return random.choice(['B', 'S']), 50
        last_result = self.history[-1]
        if self.cycle_count < 3:
            pred = last_result
        else:
            pred = 'B' if last_result == 'S' else 'S'
        return pred, 60

class CustomBSStrategy:
    def __init__(self, pattern_str):
        self.pattern = [c for c in pattern_str.upper() if c in 'BS']
        self.index = 0
        if not self.pattern:
            self.pattern = ['B', 'S']
    def add_result(self, result): pass
    def predict(self):
        val = self.pattern[self.index % len(self.pattern)]
        self.index += 1
        return val, 80

class WingoAdvancedStrategy:
    def __init__(self):
        self.history = []
        self.patterns = {
            "BBBBB": "SMALL", "SSSSS": "BIG", "BBBBBB": "SMALL", "SSSSSS": "BIG",
            "BBBBBBB": "SMALL", "SSSSSSS": "BIG", "BBBB": "BIG", "SSSS": "SMALL",
            "BBB": "BIG", "SSS": "SMALL", "BSBSB": "SMALL", "SBSBS": "BIG",
            "BSBSBS": "SMALL", "SBSBSB": "BIG", "BBSSBB": "BIG", "SSBBSS": "SMALL",
            "BBSS": "BIG", "SSBB": "SMALL", "BBBSSS": "BIG", "SSSBBB": "SMALL",
            "BBS": "SMALL", "SSB": "BIG", "BBBS": "SMALL", "SSSB": "BIG",
            "BBBBBS": "SMALL", "SSSSSB": "BIG", "BSSBBSSB": "SKIP", "SBBSSBBS": "SKIP",
            "BBBSBB": "BIG", "SSSBSS": "SMALL", "BBSBB": "BIG", "SSBSS": "SMALL",
            "BBBBSS": "SMALL", "SSSSBB": "BIG", "BBBBSB": "SMALL", "SSSSBS": "BIG",
            "BSSSS": "BIG", "SBBBB": "SMALL",
        }
    def add_result(self, result):
        self.history.append(result)
        if len(self.history) > 100:
            self.history.pop(0)
    def predict(self):
        if len(self.history) < 3:
            return random.choice(['B', 'S']), 50
        history_str = ''.join(self.history)
        for pattern in sorted(self.patterns.keys(), key=len, reverse=True):
            if history_str.endswith(pattern):
                action = self.patterns[pattern]
                if action == "BIG": return 'B', 85
                elif action == "SMALL": return 'S', 85
                elif action == "SKIP":
                    last = self.history[-1]
                    return ('B' if last == 'S' else 'S'), 50
        return random.choice(['B', 'S']), 50

# ==================== UI MESSAGES ====================
def format_stylish_info(sess):
    api = sess['api']
    bal = api.get_balance() if sess.get('api') and sess['api'].token else 0.0
    game_key = sess.get('game_key', DEFAULT_GAME_TYPE)
    game_name = GAME_TYPES[game_key]['name']
    strategy = sess.get('strategy', 'none')
    strategy_names = {
        'pattern_analyzer': 'Pattern Analyzer', 'menus_ultra': 'Menus 1.6 Ultra',
        'manus_ai': 'Manus AI', 'trend_follow': 'Trend Follow',
        'custom_bs': f'Custom BS: {sess.get("custom_pattern","")}', 'wingo_advanced': 'Wingo Advanced'
    }
    strategy_display = strategy_names.get(strategy, 'None')
    bet_seq = sess.get('betting_sequence', DEFAULT_BETTING_SEQUENCE)
    bet_amount_display = f"`{bet_seq}`"
    profit_target = sess.get('profit_target', 0.0)
    profit_display = f"`{profit_target:.2f} Ks`" if profit_target > 0 else "None"
    stop_loss = sess.get('stop_loss', 0.0)
    stop_display = f"`{stop_loss:.2f} Ks`" if stop_loss > 0 else "None"
    loss_limit = sess.get('loss_streak_limit', 0)
    loss_display = f"`{loss_limit}`" if loss_limit > 0 else "None"
    mode = "🧪 TEST MODE" if sess.get('test_mode', False) else "💰 REAL MODE"
    
    return f"""
🔋 *777 BIGWIN BOT ACTIVE*
🔄 *Mode:* {mode}
🎲 *Game:* {game_name}
💳 *Balance:* `{bal:.2f} Ks`
🎯 *betCount Seq:* {bet_amount_display}
📚 *Strategy:* {strategy_display}
🧧 *Profit Target:* {profit_display}
🌡️ *Stop Loss:* {stop_display}
🔁 *Layer (Loss limit):* {loss_display}
"""

def send_info(chat_id, user_id):
    sess = user_sessions.get(user_id)
    if not sess or not sess.get('api') or not sess['api'].token:
        send_message(chat_id, "❌ Not logged in. Please /start.", reply_markup=get_login_keyboard())
        return
    send_message(chat_id, format_stylish_info(sess), reply_markup=get_main_keyboard())

def send_bet_message(chat_id, amount, bet_name, issue, game_name, test_mode):
    prefix = "🧪 TEST MODE \n" if test_mode else ""
    send_message(chat_id, f"{prefix}🎮 🃏 777 BIGWIN\n🎯 *𝑩𝒆𝒕:* {bet_name} `{amount:.2f} Ks`\n🧭 {game_name}: `{issue}`")

def send_result_message(chat_id, win, result_num, actual, profit, balance, total_profit, test_mode):
    header = f"🏆 *အနိုင်ရရှိသည်* `+{profit:.2f} Ks`" if win else f"⛔ *ပါသွားပါပြီ* `{profit:.2f} Ks`"
    if test_mode: header = "🧪 " + header
    msg = f"""{header}
════════════════════════
📊 *ရလဒ်:* {actual} (`{result_num}`)
🧩 *လက်ကျန်ငွေ:* `{balance:.2f} Ks`
📈 *𝑻𝒐𝒕𝒂𝒍 𝑷𝒓𝒐𝒇𝒊𝒕:* `{total_profit:+.2f} Ks`"""
    send_message(chat_id, msg)

# ==================== BETTING LOOP ====================
def betting_loop(user_id, chat_id):
    sess = user_sessions.get(user_id)
    if not sess: return
    api = sess['api']
    seq = sess.get('betting_sequence', DEFAULT_BETTING_SEQUENCE)
    step = sess.get('current_step', 0)
    total = sess.get('total_profit', 0.0)
    loss_streak = sess.get('loss_streak', 0)
    pattern = sess.get('pattern_history', [])
    init_bal = sess.get('initial_balance', api.get_balance())
    stop_loss = sess.get('stop_loss', 0.0)
    profit_target = sess.get('profit_target', 0.0)
    loss_limit = sess.get('loss_streak_limit', 0)
    strategy_name = sess.get('strategy', 'manus_ai')
    game_key = sess.get('game_key', DEFAULT_GAME_TYPE)
    game_type = GAME_TYPES[game_key]
    game_type_id = game_type['typeId']
    wait_sec = game_type['wait_sec']
    is_trx = game_type['is_trx']
    game_name = game_type['name']
    test_mode = sess.get('test_mode', False)
    custom_pattern = sess.get('custom_pattern', '')
    
    if strategy_name == 'pattern_analyzer': strategy = PatternAnalyzerStrategy()
    elif strategy_name == 'menus_ultra': strategy = MenusUltraStrategy()
    elif strategy_name == 'manus_ai': strategy = ManusAIStrategy()
    elif strategy_name == 'trend_follow': strategy = TrendFollowStrategy()
    elif strategy_name == 'custom_bs': strategy = CustomBSStrategy(custom_pattern)
    elif strategy_name == 'wingo_advanced': strategy = WingoAdvancedStrategy()
    else: strategy = ManusAIStrategy()

    try:
        recent = api.get_recent_results(10, game_type_id, is_trx)
        for r in recent:
            num = int(r.get('number', 0))
            res = 'B' if num >= 5 else 'S'
            strategy.add_result(res)
            pattern.append(res)
            if len(pattern) > 5: pattern.pop(0)
    except: pass

    last_issue = None
    while sess.get('is_running') and not sess.get('stop_flag'):
        bal = api.get_balance()
        if stop_loss > 0 and (init_bal - bal) >= stop_loss:
            send_message(chat_id, f"🛑 *Stop Loss reached!* Loss: `{init_bal - bal:.2f} Ks`")
            break
        if profit_target > 0 and total >= profit_target:
            send_message(chat_id, f"🎯 *Profit Target reached!* Profit: `{total:.2f} Ks`")
            break

        issue = api.get_current_issue(game_type_id)
        if not issue or issue == last_issue:
            time.sleep(2)
            continue

        pred_char, _ = strategy.predict()
        bet_type = 13 if pred_char == 'B' else 14
        bet_name = "BIG" if bet_type == 13 else "SMALL"
        
        # 📌 လက်ရှိ အဆင့်အလိုက် betCount မြှောက်ဖော်ကိန်းကို ယူပါမယ်
        bet_count = seq[step % len(seq)]
        total_amount = BASE_AMOUNT * bet_count
        
        if not test_mode and total_amount > bal:
            send_message(chat_id, f"❌ *Insufficient balance:* need `{total_amount}`, have `{bal}`\nBot stopped.")
            break

        if test_mode:
            send_bet_message(chat_id, total_amount, bet_name, issue, game_name, True)
            last_issue = issue
        else:
            ok, msg, _ = api.place_bet(issue, BASE_AMOUNT, bet_count, bet_type, game_type_id)
            if not ok:
                send_message(chat_id, f"❌ Bet failed: `{msg}`")
                if "settled" in msg.lower(): last_issue = issue
                time.sleep(2)
                continue
            send_bet_message(chat_id, total_amount, bet_name, issue, game_name, False)
            last_issue = issue

        result_num = None
        start_time = time.time()
        max_wait = wait_sec + 15
        while (time.time() - start_time) < max_wait and sess.get('is_running') and not sess.get('stop_flag'):
            time.sleep(2)
            recents = api.get_recent_results(10, game_type_id, is_trx)
            for r in recents:
                if str(r.get('issueNumber')) == issue:
                    result_num = int(r.get('number', 0))
                    break
            if result_num is not None: break

        if result_num is not None:
            actual_char = 'B' if result_num >= 5 else 'S'
            actual_name = "BIG" if actual_char == 'B' else "SMALL"
            win = (pred_char == actual_char)
            
            # 🔥 FIX LOGIC HERE: ရှုံးရင် အဆမြှောက်တက်အောင် ပြင်ဆင်ထားပါတယ်
            if win:
                profit = total_amount * 0.96
                step = 0 # နိုင်ရင် ပထမဆုံးအဆင့် (1) ကို ပြန်ဆင်းမယ်
                loss_streak = 0
            else:
                profit = -total_amount
                step = (step + 1) % len(seq) # ❌ ရှုံးရင် နောက်တစ်ဆင့် (1 -> 3 -> 9 -> 27) သို့ တက်သွားမယ်
                loss_streak += 1
                
            total += profit
            strategy.add_result(actual_char)
            pattern.append(actual_char)
            if len(pattern) > 5: pattern.pop(0)
            sess['current_step'] = step
            sess['total_profit'] = total
            sess['loss_streak'] = loss_streak
            
            new_balance = api.get_balance()
            send_result_message(chat_id, win, result_num, actual_name, profit, new_balance, total, test_mode)
            if loss_limit > 0 and loss_streak >= loss_limit:
                send_message(chat_id, f"🛑 *Loss limit reached!* Stopped.")
                break
        else:
            time.sleep(2)

    sess['is_running'] = False
    send_message(chat_id, "🔴 Auto betting loop finished.")

# ==================== MESSAGE HANDLER ====================
def process_message(chat_id, text, user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'api': None, 'phone': None, 'betting_sequence': DEFAULT_BETTING_SEQUENCE.copy(),
            'current_step': 0, 'total_profit': 0.0, 'loss_streak': 0, 'win_streak': 0,
            'pattern_history': [], 'is_running': False, 'stop_flag': False,
            'initial_balance': 0.0, 'stop_loss': 0.0, 'profit_target': 0.0, 'strategy': 'none',
            'game_key': DEFAULT_GAME_TYPE, 'custom_pattern': '', 'test_mode': False,
            'loss_streak_limit': 0, 'login_step': None, 'login_phone': None
        }

    sess = user_sessions[user_id]

    if text == "🔐 Login":
        sess['login_step'] = 'phone'
        send_message(chat_id, "📱 Enter your *phone number* (without 95):")
        return
    if sess.get('login_step') == 'phone':
        sess['login_phone'] = text.strip()
        sess['login_step'] = 'password'
        send_message(chat_id, "🔑 Enter your *Password*:")
        return
    if sess.get('login_step') == 'password':
        phone = sess['login_phone']
        pwd = text.strip()
        api = LotteryAPI()
        ok, msg = api.login(phone, pwd)
        if ok:
            sess['api'] = api
            sess['phone'] = phone
            sess['initial_balance'] = api.get_balance()
            sess['login_step'] = None
            send_message(chat_id, f"{msg}\n💰 Balance: `{sess['initial_balance']:.2f} Ks`", reply_markup=get_main_keyboard())
            send_info(chat_id, user_id)
        else:
            send_message(chat_id, f"❌ {msg}\nPlease /start again.")
            sess['login_step'] = None
        return

    if not sess.get('api') or not sess['api'].token:
        send_message(chat_id, "Please login first.", reply_markup=get_login_keyboard())
        return

    if text == "🎮 Game Type":
        send_message(chat_id, "Select game type:", reply_markup=get_game_type_keyboard())
        return
    for key, gt in GAME_TYPES.items():
        if text == gt['name']:
            sess['game_key'] = key
            send_message(chat_id, f"✅ Game type set to: *{gt['name']}*", reply_markup=get_main_keyboard())
            return
    if text == "◀️ Back":
        send_message(chat_id, "Main menu:", reply_markup=get_main_keyboard())
        return

    if text == "🧧 Bet Amount":
        send_message(chat_id, "Enter your betCount sequence.\n*Example:* `1,3,9,27` \n(Base amount is 10)")
        sess['setting_seq'] = True
        return
    if sess.get('setting_seq'):
        try:
            seq = [int(x.strip()) for x in text.split(',')]
            if all(x > 0 for x in seq):
                sess['betting_sequence'] = seq
                sess['current_step'] = 0
                send_message(chat_id, f"✅ Updated: `{seq}`", reply_markup=get_main_keyboard())
            else: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_seq'] = False
        return

    if text == "🔁 Layer":
        send_message(chat_id, "Enter consecutive loss limit (0 = disabled):")
        sess['setting_loss_limit'] = True
        return
    if sess.get('setting_loss_limit'):
        try:
            limit = int(text)
            sess['loss_streak_limit'] = limit
            send_message(chat_id, f"✅ Set to `{limit}`", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_loss_limit'] = False
        return

    if text == "📚 Strategy":
        send_message(chat_id, "Select strategy:", reply_markup=get_strategy_keyboard())
        return
    if text in ["📊 Pattern Analyzer", "🥇 Menus 1.6 Ultra", "🧠 Manus AI", "📈 Trend Follow", "🎨 Custom BS Pattern", "✨ Wingo Advanced"]:
        if text == "📊 Pattern Analyzer": sess['strategy'] = 'pattern_analyzer'
        elif text == "🥇 Menus 1.6 Ultra": sess['strategy'] = 'menus_ultra'
        elif text == "🧠 Manus AI": sess['strategy'] = 'manus_ai'
        elif text == "📈 Trend Follow": sess['strategy'] = 'trend_follow'
        elif text == "✨ Wingo Advanced": sess['strategy'] = 'wingo_advanced'
        elif text == "🎨 Custom BS Pattern":
            send_message(chat_id, "Enter pattern (e.g. BBSB):")
            sess['awaiting_custom_pattern'] = True
            return
        send_message(chat_id, f"✅ Strategy set", reply_markup=get_main_keyboard())
        return
        
    if sess.get('awaiting_custom_pattern'):
        pattern = text.upper().replace(' ', '')
        if all(c in 'BS' for c in pattern) and pattern:
            sess['custom_pattern'] = pattern
            sess['strategy'] = 'custom_bs'
            send_message(chat_id, f"✅ Custom Set: `{pattern}`", reply_markup=get_main_keyboard())
        else: send_message(chat_id, "❌ Error", reply_markup=get_strategy_keyboard())
        sess['awaiting_custom_pattern'] = False
        return

    if text == "🧧 Profit Target":
        send_message(chat_id, "Enter profit target:")
        sess['setting_profit_target'] = True
        return
    if sess.get('setting_profit_target'):
        try:
            sess['profit_target'] = float(text)
            send_message(chat_id, "✅ Done", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_profit_target'] = False
        return

    if text == "🛑 Stop Loss":
        send_message(chat_id, "Enter stop loss:")
        sess['setting_stop_loss'] = True
        return
    if sess.get('setting_stop_loss'):
        try:
            sess['stop_loss'] = float(text)
            send_message(chat_id, "✅ Done", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_stop_loss'] = False
        return

    if text == "🔄 Test Mode":
        sess['test_mode'] = not sess.get('test_mode', False)
        send_message(chat_id, f"✅ Switched Mode", reply_markup=get_main_keyboard())
        return

    if text == "ℹ️ Info":
        send_info(chat_id, user_id)
        return

    if text == "▶️ Start":
        if sess.get('strategy') == 'none':
            send_message(chat_id, "⚠️ Set strategy first.")
            return
        if sess.get('is_running'):
            send_message(chat_id, "Already running.")
        else:
            sess['total_profit'] = 0.0
            sess['current_step'] = 0
            sess['loss_streak'] = 0
            sess['is_running'] = True
            sess['stop_flag'] = False
            threading.Thread(target=betting_loop, args=(user_id, chat_id), daemon=True).start()
        return

    if text == "⏹️ Stop":
        sess['stop_flag'] = True
        sess['is_running'] = False
        send_message(chat_id, "⏹️ Bot stopping...")
        return

    if text == "🚪 Logout":
        sess['stop_flag'] = True
        sess['is_running'] = False
        user_sessions[user_id] = {}
        send_message(chat_id, "✅ Logged out.", reply_markup=get_login_keyboard())
        return

# ==================== MAIN LOOP ====================
def main():
    print("🤖 Bot is starting...")
    last_update_id = 0
    while True:
        updates = get_updates(offset=last_update_id + 1)
        for update in updates:
            last_update_id = update['update_id']
            if 'message' in update:
                msg = update['message']
                chat_id = msg['chat']['id']
                user_id = msg['from']['id']
                text = msg.get('text', '')
                if text == '/start':
                    send_message(chat_id, "* Joker 777 BIGWIN Bot *\n\nClick *Login* to start.", reply_markup=get_login_keyboard())
                else:
                    process_message(chat_id, text, user_id)
        time.sleep(0.5)

if __name__ == "__main__":
    main()
