"""
CityPostBot — main entry point for Railway
"""
import json
import os
import httpx
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "835260826"))
GAME_DATE = os.environ.get("GAME_DATE", "13 июня")
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"

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

DB_PATH = "/tmp/citypostbot_data.json"

def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"groups": [], "publications": [], "link": "https://t.me/lacataciegas", "game_date": GAME_DATE, "state": {}}

def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        httpx.post(f"{BOT_URL}/sendMessage", json=payload, timeout=10)
    except:
        pass

def edit(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        httpx.post(f"{BOT_URL}/editMessageText", json=payload, timeout=10)
    except:
        pass

def answer_cb(cb_id):
    try:
        httpx.post(f"{BOT_URL}/answerCallbackQuery", json={"callback_query_id": cb_id}, timeout=10)
    except:
        pass

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

def handle_update(body):
    db = load_db()

    if "callback_query" in body:
        cq = body["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        msg_id = cq["message"]["message_id"]
        data = cq["data"]
        answer_cb(cq["id"])

        if data.startswith("post_"):
            group_id = data[5:]
            group = next((g for g in db["groups"] if g["id"] == group_id), None)
            if not group:
                return
            version = next_version(group_id, db)
            text = ADS[version].format(game_date=db.get("game_date", GAME_DATE), link=db.get("link", ""))
            kb = inline_kb([[("✅ Отправила", f"sent_{group_id}_{version}"), ("⏭ Пропустить", f"skip_{group_id}")]])
            edit(chat_id, msg_id, f"📢 *{group['name']}* | {group['platform']} | {group.get('format','текст')}\nВерсия: *{version}*\n\n{'─'*28}\n\n{text}\n\n{'─'*28}\n\nСкопируй текст выше и опубликуй.", reply_markup=kb)

        elif data.startswith("sent_"):
            parts = data.split("_")
            group_id, version = parts[1], parts[2]
            group = next((g for g in db["groups"] if g["id"] == group_id), None)
            from datetime import datetime
            db["publications"].append({"group_id": group_id, "version": version, "date": datetime.now().isoformat(), "reaction": False})
            save_db(db)
            kb = inline_kb([[("👍 Был отклик", f"reaction_{group_id}_yes"), ("👎 Тишина", f"reaction_{group_id}_no")]])
            edit(chat_id, msg_id, f"✅ Записала публикацию в *{group['name'] if group else group_id}*\n\nБыл ли отклик на *предыдущую* публикацию?", reply_markup=kb)

        elif data.startswith("reaction_"):
            parts = data.split("_")
            group_id, result = parts[1], parts[2]
            pubs = [p for p in db["publications"] if p["group_id"] == group_id]
            if len(pubs) >= 2:
                pubs[-2]["reaction"] = (result == "yes")
                save_db(db)
            st = group_status(group_id, db)
            msg = "❌ Группа мёртвая — 3 публикации без отклика." if st == "dead" else "👍 Записала! Следующая публикация через 4 дня."
            edit(chat_id, msg_id, msg)

        elif data.startswith("skip_"):
            edit(chat_id, msg_id, "⏭ Пропустили.")

    elif "message" in body:
        msg = body["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        if chat_id != ADMIN_ID:
            return

        if text == "/start":
            send(chat_id, "👋 *CityPostBot* — помощник по постингу\n\n*/post* — текст для публикации\n*/groups* — список групп\n*/add* — добавить группу\n*/stats* — статистика\n*/setlink* — изменить ссылку\n*/setdate* — изменить дату игры")

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
                t += f"{em} *{g['name']}* ({g['platform']})\n   {g.get('handle','—')} | {g.get('format','текст')}\n   Публ: {len(pubs)} | Откл: {r}\n\n"
            send(chat_id, t)

        elif text == "/add":
            db["state"][str(chat_id)] = "awaiting_group"
            save_db(db)
            send(chat_id, "Отправь данные:\n\n`название | @handle | Telegram или Facebook | текст или картинка`\n\nПример:\n`Испания чат СНГ | @spainchats | Telegram | текст`")

        elif text == "/post":
            active = [g for g in db["groups"] if group_status(g["id"], db) != "dead"]
            if not active:
                send(chat_id, "Нет активных групп. Добавь через /add")
                return
            buttons = [[(f"{'✅' if group_status(g['id'],db)=='active' else '🔲'} {g['name']} ({g['platform']})", f"post_{g['id']}")] for g in active]
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
            pct = round(reactions / total * 100) if total else 0
            send(chat_id, f"📊 *Статистика*\n\nГрупп: {len(db['groups'])} (акт: {len(db['groups'])-dead}, мёрт: {dead})\nПубл: {total} | Откл: {reactions} ({pct}%)\n\n*По версиям:*\nA: {vc['A']} публ / {vr['A']} откл\nB: {vc['B']} публ / {vr['B']} откл\nC: {vc['C']} публ / {vr['C']} откл\n\n🔗 {db.get('link','—')}\n📅 {db.get('game_date','—')}")

        elif text == "/setlink":
            db["state"][str(chat_id)] = "awaiting_link"
            save_db(db)
            send(chat_id, "Отправь новую ссылку:")

        elif text == "/setdate":
            db["state"][str(chat_id)] = "awaiting_date"
            save_db(db)
            send(chat_id, "Отправь новую дату игры (например: 27 июня):")

        else:
            state = db.get("state", {}).get(str(chat_id))
            if state == "awaiting_group":
                parts = [p.strip() for p in text.split("|")]
                if len(parts) != 4:
                    send(chat_id, "❌ Неверный формат. Попробуй:\n`название | @handle | Telegram или Facebook | текст или картинка`")
                    return
                gid = f"g{len(db['groups'])+1}"
                db["groups"].append({"id": gid, "name": parts[0], "handle": parts[1], "platform": parts[2], "format": parts[3]})
                db["state"][str(chat_id)] = None
                save_db(db)
                send(chat_id, f"✅ Группа *{parts[0]}* добавлена!")
            elif state == "awaiting_link":
                db["link"] = text.strip()
                db["state"][str(chat_id)] = None
                save_db(db)
                send(chat_id, f"✅ Ссылка: {db['link']}")
            elif state == "awaiting_date":
                db["game_date"] = text.strip()
                db["state"][str(chat_id)] = None
                save_db(db)
                send(chat_id, f"✅ Дата игры: {db['game_date']}")
            else:
                send(chat_id, "Используй: /post /groups /add /stats /setlink /setdate")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        try:
            handle_update(body)
        except Exception as e:
            print(f"Error: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CityPostBot is alive")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting CityPostBot on port {port}")
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    server.serve_forever()
