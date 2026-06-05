"""
CityPostBot — webhook handler for Vercel
"""
import json
import os
import httpx
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "835260826"))
GAME_DATE = os.environ.get("GAME_DATE", "13 июня")
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"

# ─── Тексты объявлений ───────────────────────────────────────
ADS = {
    "A": (
        "Привет! 👋\n\n"
        "Учите испанский, но не хватает живой практики?\n\n"
        "В разговорном клубе *La Ciudad de los Sentidos* играем в детективную игру на испанском — "
        "5 человек, у каждого своя роль.\n\n"
        "Следующие игры — *{game_date}*, уровень A1–A2.\n"
        "Присоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\n"
        "Внутри клуба — тренажёр для подготовки к роли 🎮"
    ),
    "B": (
        "Привет! 👋\n\n"
        "Живёте в Испании, но говорить по-испански всё ещё страшно?\n\n"
        "*La Ciudad de los Sentidos* — разговорный клуб, где практика спрятана внутри детективной игры. "
        "5 человек, у каждого роль, всё на испанском.\n\n"
        "Следующие игры — *{game_date}*, уровень A1–A2.\n"
        "Присоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\n"
        "Внутри клуба — тренажёр для подготовки к роли 🎮"
    ),
    "C": (
        "Привет! 👋\n\n"
        "Испанский нужен уже сейчас — а говорить всё ещё страшно?\n\n"
        "*La Ciudad de los Sentidos* — разговорный клуб, детективная игра на испанском. "
        "5 человек, у каждого своя роль.\n\n"
        "Следующие игры — *{game_date}*, уровень A1–A2.\n"
        "Присоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\n"
        "Тренажёр для подготовки к роли — внутри клуба 🎮"
    )
}

# ─── Хранилище (JSON в /tmp для Vercel) ─────────────────────
DB_PATH = "/tmp/citypostbot_data.json"

def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "groups": [],
            "publications": [],
            "link": "https://t.me/lacataciegas",
            "game_date": GAME_DATE,
            "state": {}
        }

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

# ─── Telegram API helpers ────────────────────────────────────
def send(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    httpx.post(f"{BOT_URL}/sendMessage", json=payload, timeout=10)

def edit(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    httpx.post(f"{BOT_URL}/editMessageText", json=payload, timeout=10)

def answer_callback(callback_id, text=""):
    httpx.post(f"{BOT_URL}/answerCallbackQuery",
               json={"callback_query_id": callback_id, "text": text}, timeout=10)

# ─── Логика ──────────────────────────────────────────────────
def next_version(group_id, db):
    pubs = [p for p in db["publications"] if p["group_id"] == group_id]
    versions = ["A", "B", "C"]
    if not pubs:
        return "A"
    last = pubs[-1].get("version", "A")
    return versions[(versions.index(last) + 1) % 3]

def group_status(group_id, db):
    pubs = [p for p in db["publications"] if p["group_id"] == group_id]
    if not pubs:
        return "new"
    recent = pubs[-3:]
    if len(recent) >= 3 and all(not p.get("reaction") for p in recent):
        return "dead"
    return "active"

def inline_kb(buttons):
    """buttons = [[("label", "callback_data"), ...], ...]"""
    return {
        "inline_keyboard": [
            [{"text": b[0], "callback_data": b[1]} for b in row]
            for row in buttons
        ]
    }

# ─── Обработка команд ────────────────────────────────────────
def handle_start(chat_id):
    send(chat_id,
        "👋 *CityPostBot* — помощник по постингу La Ciudad de los Sentidos\n\n"
        "*/post* — получить текст для публикации\n"
        "*/groups* — список групп\n"
        "*/add* — добавить группу\n"
        "*/stats* — статистика\n"
        "*/setlink* — изменить ссылку\n"
        "*/setdate* — изменить дату игры"
    )

def handle_groups(chat_id, db):
    if not db["groups"]:
        send(chat_id, "Групп пока нет. Добавь через /add")
        return
    text = "📋 *Группы:*\n\n"
    for g in db["groups"]:
        st = group_status(g["id"], db)
        emoji = {"new": "🔲", "active": "✅", "dead": "❌"}.get(st, "🔲")
        pubs = [p for p in db["publications"] if p["group_id"] == g["id"]]
        reactions = sum(1 for p in pubs if p.get("reaction"))
        text += f"{emoji} *{g['name']}* ({g['platform']})\n"
        text += f"   {g.get('handle','—')} | {g.get('format','текст')}\n"
        text += f"   Публикаций: {len(pubs)} | Откликов: {reactions}\n\n"
    send(chat_id, text)

def handle_add(chat_id, db):
    db["state"][str(chat_id)] = "awaiting_group"
    save_db(db)
    send(chat_id,
        "Отправь данные группы в формате:\n\n"
        "`название | @handle | Telegram или Facebook | текст или картинка`\n\n"
        "Пример:\n`Испания чат СНГ | @spainchats | Telegram | текст`"
    )

def handle_post(chat_id, db):
    active = [g for g in db["groups"] if group_status(g["id"], db) != "dead"]
    if not active:
        send(chat_id, "Нет активных групп. Добавь через /add")
        return
    buttons = [
        [(f"{'✅' if group_status(g['id'],db)=='active' else '🔲'} {g['name']} ({g['platform']})",
          f"post_{g['id']}")]
        for g in active
    ]
    send(chat_id, "📢 Выбери группу:", reply_markup=inline_kb(buttons))

def handle_stats(chat_id, db):
    total = len(db["publications"])
    reactions = sum(1 for p in db["publications"] if p.get("reaction"))
    dead = sum(1 for g in db["groups"] if group_status(g["id"], db) == "dead")
    vc = {"A": 0, "B": 0, "C": 0}
    vr = {"A": 0, "B": 0, "C": 0}
    for p in db["publications"]:
        v = p.get("version", "A")
        vc[v] = vc.get(v, 0) + 1
        if p.get("reaction"):
            vr[v] = vr.get(v, 0) + 1
    pct = round(reactions / total * 100) if total else 0
    send(chat_id,
        f"📊 *Статистика*\n\n"
        f"Групп: {len(db['groups'])} (активных: {len(db['groups'])-dead}, мёртвых: {dead})\n"
        f"Публикаций: {total} | Откликов: {reactions} ({pct}%)\n\n"
        f"*По версиям:*\n"
        f"A: {vc['A']} публ. / {vr['A']} откл.\n"
        f"B: {vc['B']} публ. / {vr['B']} откл.\n"
        f"C: {vc['C']} публ. / {vr['C']} откл.\n\n"
        f"🔗 Ссылка: {db.get('link','—')}\n"
        f"📅 Дата игры: {db.get('game_date','—')}"
    )

def handle_setlink(chat_id, db):
    db["state"][str(chat_id)] = "awaiting_link"
    save_db(db)
    send(chat_id, "Отправь новую ссылку:")

def handle_setdate(chat_id, db):
    db["state"][str(chat_id)] = "awaiting_date"
    save_db(db)
    send(chat_id, "Отправь новую дату игры (например: 27 июня):")

# ─── Обработка callback ──────────────────────────────────────
def handle_callback(chat_id, message_id, callback_id, data, db):
    answer_callback(callback_id)

    if data.startswith("post_"):
        group_id = data[5:]
        group = next((g for g in db["groups"] if g["id"] == group_id), None)
        if not group:
            return
        version = next_version(group_id, db)
        text = ADS[version].format(
            game_date=db.get("game_date", GAME_DATE),
            link=db.get("link", "https://t.me/lacataciegas")
        )
        kb = inline_kb([[
            ("✅ Отправила", f"sent_{group_id}_{version}"),
            ("⏭ Пропустить", f"skip_{group_id}")
        ]])
        edit(chat_id, message_id,
            f"📢 *{group['name']}* | {group['platform']} | {group.get('format','текст')}\n"
            f"Версия: *{version}*\n\n"
            f"{'─'*28}\n\n{text}\n\n{'─'*28}\n\n"
            f"Скопируй текст выше и опубликуй в группу.",
            reply_markup=kb
        )

    elif data.startswith("sent_"):
        parts = data.split("_")
        group_id, version = parts[1], parts[2]
        group = next((g for g in db["groups"] if g["id"] == group_id), None)
        from datetime import datetime
        db["publications"].append({
            "group_id": group_id,
            "version": version,
            "date": datetime.now().isoformat(),
            "reaction": False
        })
        save_db(db)
        kb = inline_kb([[
            ("👍 Был отклик", f"reaction_{group_id}_yes"),
            ("👎 Тишина", f"reaction_{group_id}_no")
        ]])
        edit(chat_id, message_id,
            f"✅ Записала публикацию в *{group['name'] if group else group_id}*\n\n"
            f"Был ли отклик на *предыдущую* публикацию в этой группе?",
            reply_markup=kb
        )

    elif data.startswith("reaction_"):
        parts = data.split("_")
        group_id, result = parts[1], parts[2]
        pubs = [p for p in db["publications"] if p["group_id"] == group_id]
        if len(pubs) >= 2:
            pubs[-2]["reaction"] = (result == "yes")
            save_db(db)
        st = group_status(group_id, db)
        if st == "dead":
            msg = "❌ Группа мёртвая — 3 публикации без отклика. Убрана из ротации."
        else:
            msg = "👍 Записала! Следующая публикация через 4 дня."
        edit(chat_id, message_id, msg)

    elif data.startswith("skip_"):
        edit(chat_id, message_id, "⏭ Пропустили.")

# ─── Обработка текстовых сообщений ──────────────────────────
def handle_text(chat_id, text, db):
    state = db.get("state", {}).get(str(chat_id))

    if state == "awaiting_group":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 4:
            send(chat_id, "❌ Неверный формат. Попробуй снова:\n`название | @handle | Telegram или Facebook | текст или картинка`")
            return
        group_id = f"g{len(db['groups'])+1}"
        db["groups"].append({
            "id": group_id,
            "name": parts[0],
            "handle": parts[1],
            "platform": parts[2],
            "format": parts[3]
        })
        db["state"][str(chat_id)] = None
        save_db(db)
        send(chat_id, f"✅ Группа *{parts[0]}* добавлена!")

    elif state == "awaiting_link":
        db["link"] = text.strip()
        db["state"][str(chat_id)] = None
        save_db(db)
        send(chat_id, f"✅ Ссылка обновлена: {db['link']}")

    elif state == "awaiting_date":
        db["game_date"] = text.strip()
        db["state"][str(chat_id)] = None
        save_db(db)
        send(chat_id, f"✅ Дата игры: {db['game_date']}")

    else:
        send(chat_id, "Используй команды: /post /groups /add /stats /setlink /setdate")

# ─── Vercel entry point ──────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        db = load_db()

        if "callback_query" in body:
            cq = body["callback_query"]
            chat_id = cq["message"]["chat"]["id"]
            message_id = cq["message"]["message_id"]
            handle_callback(chat_id, message_id, cq["id"], cq["data"], db)

        elif "message" in body:
            msg = body["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")

            if chat_id != ADMIN_ID:
                self.send_response(200)
                self.end_headers()
                return

            if text == "/start":
                handle_start(chat_id)
            elif text == "/groups":
                handle_groups(chat_id, db)
            elif text == "/add":
                handle_add(chat_id, db)
            elif text == "/post":
                handle_post(chat_id, db)
            elif text == "/stats":
                handle_stats(chat_id, db)
            elif text == "/setlink":
                handle_setlink(chat_id, db)
            elif text == "/setdate":
                handle_setdate(chat_id, db)
            else:
                handle_text(chat_id, text, db)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CityPostBot is alive")

    def log_message(self, format, *args):
        pass
