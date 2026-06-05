"""
CityPostBot — локальная версия для Mac
Запуск: python3 bot_local.py
Остановка: Ctrl+C
"""
import json
import os
import urllib.request
import time
from datetime import datetime

TOKEN = "8442241163:AAEY3OnzbYzE5X4cD9GvgDbdH7-oFGt0mf4"
ADMIN_ID = 835260826
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"
GAME_DATE = "13 июня"

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

DEFAULT_GROUPS = [
    {"id": "g1", "name": "Испания чат | СНГ", "handle": "@spainchats", "platform": "Telegram", "format": "текст"},
    {"id": "g2", "name": "Испания | Для Своих", "handle": "@spain_chatss", "platform": "Telegram", "format": "текст"},
    {"id": "g3", "name": "Валенсия / Costa Blanca", "handle": "@costablanka", "platform": "Telegram", "format": "текст"},
    {"id": "g4", "name": "Испания чат | Spain News", "handle": "@SpainNewsChat", "platform": "Telegram", "format": "текст"},
    {"id": "g5", "name": "Наши в Мадриде", "handle": "—", "platform": "Telegram", "format": "текст"},
    {"id": "g6", "name": "Digital Nomad Spain", "handle": "@chatfornomads", "platform": "Telegram", "format": "текст"},
    {"id": "g7", "name": "Марбелья / Costa del Sol", "handle": "@Marbella_reklama", "platform": "Telegram", "format": "текст"},
    {"id": "g8", "name": "Business в Испании", "handle": "@konciergemarket", "platform": "Telegram", "format": "текст"},
    {"id": "g9", "name": "ВНЖ Испании Чат", "handle": "—", "platform": "Telegram", "format": "текст"},
    {"id": "g10", "name": "Русские в Малаге", "handle": "@russkie_malaga", "platform": "Telegram", "format": "текст"},
]

DB_PATH = os.path.expanduser("~/citypostbot_data.json")
USER_STATE = {}

def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        db = {"groups": DEFAULT_GROUPS, "publications": [], "link": "https://t.me/lacataciegas", "game_date": GAME_DATE}
        save_db(db)
        return db

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def api(method, **params):
    url = f"{BOT_URL}/{method}"
    data = json.dumps(params).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {method}: {e}")
        return {}

def send(chat_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        params["reply_markup"] = reply_markup
    api("sendMessage", **params)

def edit(chat_id, message_id, text, reply_markup=None):
    params = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        params["reply_markup"] = reply_markup
    api("editMessageText", **params)

def inline_kb(buttons):
    return {"inline_keyboard": [[{"text": b[0], "callback_data": b[1]} for b in row] for row in buttons]}

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

def handle_callback(cq, db):
    chat_id = cq["message"]["chat"]["id"]
    msg_id = cq["message"]["message_id"]
    data = cq["data"]
    api("answerCallbackQuery", callback_query_id=cq["id"])

    if data.startswith("post_"):
        group_id = data[5:]
        group = next((g for g in db["groups"] if g["id"] == group_id), None)
        if not group:
            return
        version = next_version(group_id, db)
        text = ADS[version].format(game_date=db.get("game_date", GAME_DATE), link=db.get("link", ""))
        kb = inline_kb([[("✅ Отправила", f"sent_{group_id}_{version}"), ("⏭ Пропустить", f"skip_{group_id}")]])
        edit(chat_id, msg_id,
            f"📢 *{group['name']}* | {group['platform']} | {group.get('format','текст')}\n"
            f"Версия: *{version}*\n\n{'─'*28}\n\n{text}\n\n{'─'*28}\n\nСкопируй текст выше и опубликуй.",
            reply_markup=kb)

    elif data.startswith("sent_"):
        parts = data.split("_")
        group_id, version = parts[1], parts[2]
        group = next((g for g in db["groups"] if g["id"] == group_id), None)
        db["publications"].append({
            "group_id": group_id,
            "version": version,
            "date": datetime.now().isoformat(),
            "reaction": False
        })
        save_db(db)
        kb = inline_kb([[("👍 Был отклик", f"reaction_{group_id}_yes"), ("👎 Тишина", f"reaction_{group_id}_no")]])
        edit(chat_id, msg_id,
            f"✅ Записала публикацию в *{group['name'] if group else group_id}*\n\n"
            f"Был ли отклик на предыдущую публикацию в этой группе?",
            reply_markup=kb)

    elif data.startswith("reaction_"):
        parts = data.split("_")
        group_id, result = parts[1], parts[2]
        pubs = [p for p in db["publications"] if p["group_id"] == group_id]
        if len(pubs) >= 2:
            pubs[-2]["reaction"] = (result == "yes")
            save_db(db)
        st = group_status(group_id, db)
        msg = "❌ Группа мёртвая — 3 публикации без отклика." if st == "dead" else "👍 Записала! Следующая через 4 дня."
        edit(chat_id, msg_id, msg)

    elif data.startswith("skip_"):
        edit(chat_id, msg_id, "⏭ Пропустили.")

def handle_message(msg, db):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    if chat_id != ADMIN_ID:
        return
    state = USER_STATE.get(chat_id)

    if text == "/start":
        USER_STATE[chat_id] = None
        send(chat_id,
            "👋 *CityPostBot* — помощник по постингу\n\n"
            "*/post* — текст для публикации\n"
            "*/groups* — список групп\n"
            "*/add* — добавить группу\n"
            "*/stats* — статистика\n"
            "*/setlink* — изменить ссылку\n"
            "*/setdate* — изменить дату игры"
        )
    elif text == "/groups":
        if not db["groups"]:
            send(chat_id, "Групп нет. Добавь через /add")
            return
        t = "📋 *Группы:*\n\n"
        for g in db["groups"]:
            st = group_status(g["id"], db)
            em = {"new": "🔲", "active": "✅", "dead": "❌"}.get(st, "🔲")
            pubs = [p for p in db["publications"] if p["group_id"] == g["id"]]
            r = sum(1 for p in pubs if p.get("reaction"))
            t += f"{em} *{g['name']}* ({g['platform']})\n   {g.get('handle','—')} | Публ: {len(pubs)} | Откл: {r}\n\n"
        send(chat_id, t)
    elif text == "/add":
        USER_STATE[chat_id] = "awaiting_group"
        send(chat_id, "Отправь данные:\n\n`название | @handle | Telegram или Facebook | текст или картинка`")
    elif text == "/post":
        active = [g for g in db["groups"] if group_status(g["id"], db) != "dead"]
        if not active:
            send(chat_id, "Нет активных групп.")
            return
        buttons = [[(f"{'✅' if group_status(g['id'],db)=='active' else '🔲'} {g['name']}", f"post_{g['id']}")] for g in active]
        send(chat_id, "📢 Выбери группу:", reply_markup=inline_kb(buttons))
    elif text == "/stats":
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
        pct = round(reactions/total*100) if total else 0
        send(chat_id,
            f"📊 *Статистика*\n\n"
            f"Групп: {len(db['groups'])} (акт: {len(db['groups'])-dead}, мёрт: {dead})\n"
            f"Публ: {total} | Откл: {reactions} ({pct}%)\n\n"
            f"A: {vc['A']} / {vr['A']} откл\n"
            f"B: {vc['B']} / {vr['B']} откл\n"
            f"C: {vc['C']} / {vr['C']} откл\n\n"
            f"🔗 {db.get('link','—')}\n"
            f"📅 {db.get('game_date','—')}"
        )
    elif text == "/setlink":
        USER_STATE[chat_id] = "awaiting_link"
        send(chat_id, "Отправь новую ссылку:")
    elif text == "/setdate":
        USER_STATE[chat_id] = "awaiting_date"
        send(chat_id, "Отправь новую дату игры:")
    elif state == "awaiting_group":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) != 4:
            send(chat_id, "❌ Неверный формат.\n\n`название | @handle | Telegram или Facebook | текст или картинка`")
            return
        gid = f"g{len(db['groups'])+1}"
        db["groups"].append({"id": gid, "name": parts[0], "handle": parts[1], "platform": parts[2], "format": parts[3]})
        save_db(db)
        USER_STATE[chat_id] = None
        send(chat_id, f"✅ Группа *{parts[0]}* добавлена!")
    elif state == "awaiting_link":
        db["link"] = text.strip()
        save_db(db)
        USER_STATE[chat_id] = None
        send(chat_id, f"✅ Ссылка: {db['link']}")
    elif state == "awaiting_date":
        db["game_date"] = text.strip()
        save_db(db)
        USER_STATE[chat_id] = None
        send(chat_id, f"✅ Дата игры: {db['game_date']}")
    else:
        send(chat_id, "Используй: /post /groups /add /stats /setlink /setdate")

def main():
    print("🤖 CityPostBot запущен. Остановка: Ctrl+C")
    api("deleteWebhook")
    offset = 0
    while True:
        try:
            result = api("getUpdates", offset=offset, timeout=30)
            updates = result.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                db = load_db()
                if "callback_query" in update:
                    handle_callback(update["callback_query"], db)
                elif "message" in update:
                    handle_message(update["message"], db)
        except KeyboardInterrupt:
            print("\n👋 Бот остановлен.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
