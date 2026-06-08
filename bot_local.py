import json, os, urllib.request, time, threading
from datetime import datetime, timedelta

TOKEN = "8442241163:AAEY3OnzbYzE5X4cD9GvgDbdH7-oFGt0mf4"
ADMIN_ID = 835260826
BOT_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_PATH = os.path.expanduser("~/citypostbot_data.json")
USER_STATE = {}

ADS = {
    "A": "Привет!\n\nУчите испанский, но не хватает живой практики?\n\nВ разговорном клубе La Ciudad de los Sentidos играем в детективную игру на испанском — 5 человек, у каждого своя роль.\n\nСледующие игры — {game_date}, уровень A1-A2.\nПрисоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\nВнутри клуба — тренажёр для подготовки к роли 🎮",
    "B": "Привет!\n\nЖивёте в Испании, но говорить по-испански всё ещё страшно?\n\nLa Ciudad de los Sentidos — разговорный клуб, где практика спрятана внутри детективной игры. 5 человек, у каждого роль, всё на испанском.\n\nСледующие игры — {game_date}, уровень A1-A2.\nПрисоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\nВнутри клуба — тренажёр для подготовки к роли 🎮",
    "C": "Привет!\n\nИспанский нужен уже сейчас — а говорить всё ещё страшно?\n\nLa Ciudad de los Sentidos — разговорный клуб, детективная игра на испанском. 5 человек, у каждого своя роль.\n\nСледующие игры — {game_date}, уровень A1-A2.\nПрисоединяйтесь, чтобы выбрать удобное время 👉 {link}\n\nТренажёр для подготовки к роли — внутри клуба 🎮"
}

DEFAULT_GROUPS = [
    {"id":"g1","name":"Испания чат | СНГ","handle":"@spainchats","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g2","name":"Испания | Для Своих","handle":"@spain_chatss","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g3","name":"Валенсия / Costa Blanca","handle":"@costablanka","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g4","name":"Испания чат | Spain News","handle":"@SpainNewsChat","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g5","name":"Наши в Мадриде","handle":"—","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g6","name":"Digital Nomad Spain","handle":"@chatfornomads","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g7","name":"Марбелья / Costa del Sol","handle":"@Marbella_reklama","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g8","name":"Business в Испании","handle":"@konciergemarket","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g9","name":"ВНЖ Испании Чат","handle":"—","platform":"Telegram","format":"текст","group_link":""},
    {"id":"g10","name":"Русские в Малаге","handle":"@russkie_malaga","platform":"Telegram","format":"текст","group_link":""},
]

def load_db():
    try:
        with open(DB_PATH,"r",encoding="utf-8") as f:
            db = json.load(f)
        changed = False
        for g in db.get("groups", []):
            if "group_link" not in g:
                g["group_link"] = ""
                changed = True
        # Добавляем images если нет
        if "images" not in db:
            db["images"] = []
            changed = True
        if changed:
            save_db(db)
        return db
    except:
        db={"groups":DEFAULT_GROUPS,"publications":[],"link":"https://t.me/oksanamaikova_spanish","game_date":"13 июня","images":[]}
        save_db(db)
        return db

def save_db(db):
    with open(DB_PATH,"w",encoding="utf-8") as f:
        json.dump(db,f,ensure_ascii=False,indent=2)

REDIRECT_BASE = "http://tg.hcs-tomsk.ru/b"

def get_link_for_group(g, db):
    """Ссылка для группы.
    Если у группы своя ссылка (group_link) — использует её.
    Иначе — ведёт напрямую на канал (db['link']). Редирект-сервер отключён.
    """
    if g.get("group_link"):
        return g["group_link"]
    return db.get("link", "")

def next_image(gid, db):
    """Возвращает file_id картинки для группы (ротация по кругу)."""
    images = db.get("images", [])
    if not images:
        return None
    pubs = [p for p in db["publications"] if p["group_id"] == gid]
    idx = len(pubs) % len(images)
    return images[idx]

def api(method, **params):
    data=json.dumps(params).encode()
    req=urllib.request.Request(f"{BOT_URL}/{method}",data=data,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {method}: {e}")
        return {}

def send(chat_id, text, reply_markup=None):
    p={"chat_id":chat_id,"text":text}
    if reply_markup: p["reply_markup"]=reply_markup
    api("sendMessage",**p)

def send_photo(chat_id, photo, caption, reply_markup=None):
    """Отправляет картинку с текстом как подписью."""
    p={"chat_id":chat_id,"photo":photo,"caption":caption,"parse_mode":"HTML"}
    if reply_markup: p["reply_markup"]=reply_markup
    return api("sendPhoto",**p)

def edit(chat_id, msg_id, text, reply_markup=None):
    p={"chat_id":chat_id,"message_id":msg_id,"text":text}
    if reply_markup: p["reply_markup"]=reply_markup
    api("editMessageText",**p)

def kb(buttons):
    return {"inline_keyboard":[[{"text":b[0],"callback_data":b[1]} for b in row] for row in buttons]}

def kb_url(label, url):
    """Кнопка-ссылка (открывает URL вместо callback)."""
    return {"inline_keyboard":[[{"text":label,"url":url}]]}

# ── ГОСТЕВОЙ ОФФЕР (видят все, кроме админа) ──────────────────────
TRIBUTE_LINK = "https://t.me/tribute/app?startapp=sRi5"

WELCOME_TEXT = (
"✨ Как устроена подписка\n\n"
"Клуб — это живая система, к которой нужно привыкнуть. Поэтому вход разделён на этапы — и играть ты можешь начать сразу, а не «когда-нибудь потом».\n\n"
"🔸 7 дней — бесплатно. Заходишь, осматриваешься, видишь свой уровень. И уже в эти дни можешь сыграть свою первую игру — если попадаешь в расписание и чувствуешь силы.\n\n"
"🔸 Первый месяц — €1,30. Целый месяц внутри клуба: подготовка, материалы и живые игры по расписанию. Никто никуда не торопит — играешь, когда готов.\n\n"
"🔸 Дальше — €10 в месяц. Одна сюжетная игра уже включена в подписку. Дополнительные игры — €5 для участников клуба.\n\n"
"Стоимость одной игры без клубной карты — €10. В клубе — выгоднее с первого дня.\n\n"
"✨ Как ты растёшь внутри клуба\n\n"
"Здесь нет обязательного маршрута и нет давления двигаться быстрее, чем ты готов. Подготовился. Поиграл. Почувствовал свою речь. Хочешь — шаг на следующий уровень. Хочешь — остаёшься и повторяешь игру, с той же командой или с новой.\n\n"
"Игры можно проходить заново. Уровни можно менять в любую сторону. Цель не в том, чтобы быстрее пройти материал. Цель — начать говорить и не останавливаться.\n\n"
"🔗 Твой следующий шаг\n\n"
"Прямо сейчас мы готовимся к игре для уровня A1–A2.\n\n"
"🔸 переходишь по кнопке ниже\n"
"🔸 заходишь в клуб\n"
"🔸 получаешь первые материалы\n"
"🔸 начинаешь готовиться"
)

def send_welcome(cid, db):
    """Показывает гостю оффер: картинка CLUB ACCESS (если загружена) отдельным
    сообщением + текст с кнопкой Tribute. Текст длиннее лимита подписи к фото
    (1024), поэтому шлём двумя сообщениями — так ничего не обрезается."""
    btn = {"inline_keyboard":[[{"text":"🔸 Начать подготовку","url":TRIBUTE_LINK}]]}
    wimg = db.get("welcome_image")
    if wimg:
        api("sendPhoto", chat_id=cid, photo=wimg)
    api("sendMessage", chat_id=cid, text=WELCOME_TEXT, reply_markup=btn)

def next_ver(gid, db):
    pubs=[p for p in db["publications"] if p["group_id"]==gid]
    v=["A","B","C"]
    if not pubs: return "A"
    return v[(v.index(pubs[-1].get("version","A"))+1)%3]

def gstatus(gid, db):
    pubs=[p for p in db["publications"] if p["group_id"]==gid]
    if not pubs: return "new"
    r=pubs[-3:]
    if len(r)>=3 and all(not p.get("reaction") for p in r): return "dead"
    return "active"

def check_schedule():
    while True:
        try:
            db = load_db()
            now = datetime.now()
            notified = db.get("notified", {})
            for g in db["groups"]:
                gid = g["id"]
                if gstatus(gid, db) == "dead":
                    continue
                pubs = [p for p in db["publications"] if p["group_id"] == gid]
                if pubs:
                    last_date = datetime.fromisoformat(pubs[-1]["date"])
                    days_since = (now - last_date).days
                    due = days_since >= 7
                else:
                    due = True
                if due:
                    today = now.strftime("%Y-%m-%d")
                    last_notified = notified.get(gid, "")
                    if last_notified != today:
                        ver = next_ver(gid, db)
                        send(ADMIN_ID,
                            f"🔔 Пора постить!\n\n"
                            f"Группа: {g['name']}\n"
                            f"Версия объявления: {ver}\n\n"
                            f"Нажми /post чтобы открыть.")
                        notified[gid] = today
                        db["notified"] = notified
                        save_db(db)
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(3600)

def on_callback(cq, db):
    cid=cq["message"]["chat"]["id"]
    mid=cq["message"]["message_id"]
    data=cq["data"]
    api("answerCallbackQuery",callback_query_id=cq["id"])

    if data.startswith("post_"):
        gid=data[5:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        ver=next_ver(gid,db)
        link=get_link_for_group(g,db)
        text=ADS[ver].format(game_date=db.get("game_date","13 июня"),link=link)
        link_label = "🔗 своя" if g.get("group_link") else "🔗 общая"
        images = db.get("images", [])
        image_file_id = next_image(gid, db)
        img_label = f"🖼 картинка {(len([p for p in db['publications'] if p['group_id']==gid]) % len(images)) + 1} из {len(images)}" if images else "🖼 картинок нет — /setimage"

        # Отправляем новое сообщение с превью картинки и текстом
        preview = (
            f"Группа: {g['name']} | {g['platform']}\n"
            f"Версия: {ver} | Ссылка: {link_label} | {img_label}\n\n"
            f"{'─'*30}\n\n"
            f"{text}\n\n"
            f"{'─'*30}\n\n"
            f"Скопируй текст выше и опубликуй в группу.\n"
            f"{'⚠️ Картинка: отправь её вручную вместе с текстом.' if image_file_id else '⚠️ Картинок нет — добавь через /setimage'}"
        )
        edit(cid, mid, preview,
            reply_markup=kb([
                [("✅ Отправила", f"sent_{gid}_{ver}"), ("⏭ Пропустить", f"skip_{gid}")],
                [("🖼 Показать картинку", f"showimg_{gid}")] if image_file_id else []
            ]))

    elif data.startswith("showimg_"):
        gid=data[8:]
        image_file_id = next_image(gid, db)
        if image_file_id:
            send_photo(cid, image_file_id, "Картинка для поста 👆\nСкопируй и прикрепи к тексту при публикации.")
        else:
            send(cid, "Картинок нет. Добавь через /setimage")

    elif data.startswith("sent_"):
        parts=data.split("_"); gid,ver=parts[1],parts[2]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        db["publications"].append({"group_id":gid,"version":ver,"date":datetime.now().isoformat(),"reaction":False})
        save_db(db)
        edit(cid,mid,
            f"Записала публикацию в {g['name'] if g else gid}\n\nБыл ли отклик на предыдущую публикацию?",
            reply_markup=kb([[("👍 Был отклик",f"reaction_{gid}_yes"),("👎 Тишина",f"reaction_{gid}_no")]]))

    elif data.startswith("reaction_"):
        parts=data.split("_"); gid,res=parts[1],parts[2]
        pubs=[p for p in db["publications"] if p["group_id"]==gid]
        if len(pubs)>=2: pubs[-2]["reaction"]=(res=="yes"); save_db(db)
        st=gstatus(gid,db)
        edit(cid,mid,"Группа мертвая — убрана из ротации." if st=="dead" else "Записала! Напомню через 7 дней.")

    elif data.startswith("skip_"):
        edit(cid,mid,"Пропустили.")

    elif data.startswith("delete_"):
        gid=data[7:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        edit(cid,mid,
            f"Удалить группу «{g['name']}»?\n\nВсе данные о публикациях в эту группу тоже удалятся.",
            reply_markup=kb([[("✅ Да, удалить",f"confirmdelete_{gid}"),("❌ Отмена",f"canceldelete_{gid}")]]))

    elif data.startswith("confirmdelete_"):
        gid=data[14:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        name=g["name"]
        db["groups"]=[x for x in db["groups"] if x["id"]!=gid]
        db["publications"]=[p for p in db["publications"] if p["group_id"]!=gid]
        save_db(db)
        edit(cid,mid,f"Группа «{name}» удалена.")

    elif data.startswith("canceldelete_"):
        edit(cid,mid,"Отмена. Группа не удалена.")

    elif data.startswith("leadgroup_"):
        source_id=data[10:]
        if source_id=="direct":
            source_name="Написал напрямую"
        else:
            g=next((x for x in db["groups"] if x["id"]==source_id),None)
            source_name=g["name"] if g else source_id
        USER_STATE[cid]=f"awaiting_lead_name|{source_name}"
        edit(cid,mid,f"Источник: {source_name}\n\nНапиши имя человека (или ник в Telegram):")

    elif data.startswith("setstatus_"):
        gid=data[10:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        cur=gstatus(gid,db)
        cur_label={"new":"🔲 новая","active":"✅ активная","dead":"❌ мёртвая"}.get(cur,cur)
        edit(cid,mid,
            f"Группа: {g['name']}\nТекущий статус: {cur_label}\n\nВыбери новый статус:",
            reply_markup=kb([
                [("✅ Активная",f"setstatusval_{gid}_active"),("❌ Мёртвая",f"setstatusval_{gid}_dead")],
                [("🔲 Сбросить (новая)",f"setstatusval_{gid}_new")]
            ]))

    elif data.startswith("setstatusval_"):
        parts=data.split("_"); gid,new_status=parts[1],parts[2]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        if new_status=="active":
            for p in db["publications"]:
                if p["group_id"]==gid: p["reaction"]=True
            save_db(db)
            edit(cid,mid,f"Группа «{g['name']}» → ✅ активная")
        elif new_status=="dead":
            for _ in range(3):
                db["publications"].append({"group_id":gid,"version":"A","date":datetime.now().isoformat(),"reaction":False})
            save_db(db)
            edit(cid,mid,f"Группа «{g['name']}» → ❌ мёртвая (убрана из ротации)")
        elif new_status=="new":
            db["publications"]=[p for p in db["publications"] if p["group_id"]!=gid]
            save_db(db)
            edit(cid,mid,f"Группа «{g['name']}» → 🔲 сброшена (новая)")

    elif data.startswith("setgl_"):
        gid=data[6:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        current=g.get("group_link","") or "не задана"
        USER_STATE[cid]=f"awaiting_grouplink_{gid}"
        edit(cid,mid,f"Группа: {g['name']}\nТекущая ссылка: {current}\n\nОтправь новую пригласительную ссылку для этой группы:")

    elif data.startswith("delimg_"):
        idx=int(data[7:])
        images=db.get("images",[])
        if 0 <= idx < len(images):
            images.pop(idx)
            db["images"]=images
            save_db(db)
            edit(cid,mid,f"Картинка {idx+1} удалена. Осталось: {len(images)}/3")
        else:
            edit(cid,mid,"Картинка не найдена.")

def on_message(msg, db):
    cid=msg["chat"]["id"]
    text=msg.get("text","")
    photo=msg.get("photo")

    # ── ГОСТЬ (не админ) ──────────────────────────────────────────
    # Любой человек, пришедший по помеченной ссылке ?start=gID:
    # фиксируем лид (источник), показываем оффер. Админку не видит.
    if cid!=ADMIN_ID:
        if text and text.startswith("/start"):
            parts = text.split(" ", 1)
            if len(parts) == 2:
                source_gid = parts[1].strip()
                g = next((x for x in db["groups"] if x["id"] == source_gid), None)
                if g:
                    if "leads" not in db:
                        db["leads"] = []
                    db["leads"].append({
                        "user_id": cid,
                        "source_group_id": source_gid,
                        "source_group_name": g["name"],
                        "date": datetime.now().isoformat()
                    })
                    save_db(db)
            send_welcome(cid, db)
        else:
            # любое другое сообщение от гостя — тоже показываем оффер
            send_welcome(cid, db)
        return

    state=USER_STATE.get(cid)

    # ── ЗАГРУЗКА КАРТИНКИ ──────────────────────────────────────────
    if photo and state=="awaiting_welcome_image":
        file_id=photo[-1]["file_id"]
        db["welcome_image"]=file_id
        save_db(db)
        USER_STATE[cid]=None
        send(cid,"✅ Картинка приветствия сохранена!\n\nТеперь все гости, пришедшие по ссылке, увидят её перед текстом оффера.\n\nПроверь сам: /preview")
        return

    if photo and state=="awaiting_image":
        images=db.get("images",[])
        if len(images)>=3:
            send(cid,"Уже 3 картинки сохранено. Сначала удали одну через /images")
            USER_STATE[cid]=None
            return
        file_id=photo[-1]["file_id"]  # берём самое высокое разрешение
        images.append(file_id)
        db["images"]=images
        save_db(db)
        USER_STATE[cid]=None
        send(cid,f"✅ Картинка {len(images)} из 3 сохранена!\n\nВсего картинок: {len(images)}\nЧередуются при каждой публикации A→B→C.\n\nДобавь ещё через /setimage или смотри /images")
        return

    if photo and state!="awaiting_image":
        send(cid,"Картинку получила, но сейчас не жду загрузки.\n\nЧтобы сохранить картинку — сначала напиши /setimage")
        return

    # ── КОМАНДЫ ───────────────────────────────────────────────────
    if text and text.startswith("/start"):
        USER_STATE[cid]=None
        send(cid,
"🤖 CityPostBot — рекламный отдел La Ciudad\n\n"
"━━━ 📢 ПОСТИНГ ━━━\n"
"/post — выбрать группу и получить текст объявления\n"
"/setdate — изменить дату игры в объявлениях\n\n"
"━━━ 🖼 КАРТИНКИ ━━━\n"
"/setimage — загрузить картинку (до 3 штук, ротация)\n"
"/images — посмотреть сохранённые картинки\n"
"/clearimages — удалить все картинки\n\n"
"━━━ 🎟 ОФФЕР ДЛЯ ГОСТЕЙ ━━━\n"
"/setwelcomeimage — картинка приветствия (CLUB ACCESS)\n"
"/preview — посмотреть оффер глазами гостя\n\n"
"━━━ 👥 ГРУППЫ ━━━\n"
"/groups — список всех групп со статусами\n"
"/find — найти группу по названию или @handle\n"
"/add — добавить новую группу\n"
"/delete — удалить группу из базы\n"
"/status — вручную сменить статус группы\n"
"/setlink — изменить общую ссылку в постах\n"
"/setgrouplink — уникальная ссылка для группы\n\n"
"━━━ 📊 АНАЛИТИКА ━━━\n"
"/stats — статистика публикаций и откликов\n"
"/sources — откуда приходят люди (UTM-метки)\n\n"
"━━━ 🎯 ЛИДЫ ━━━\n"
"/lead — записать заинтересованного человека\n"
"/leads — список всех лидов с источниками\n\n"
"━━━━━━━━━━━━━━━━━━━━\n"
"💡 Картинки чередуются: пост A→картинка 1, B→2, C→3"
)

    elif text=="/setimage":
        images=db.get("images",[])
        if len(images)>=3:
            send(cid,f"Уже сохранено 3 картинки.\n\nПосмотри /images — удали одну, потом загружай новую.")
            return
        USER_STATE[cid]="awaiting_image"
        send(cid,f"Отправь картинку (сейчас {len(images)}/3).\n\nКартинки чередуются: пост A → картинка 1, B → картинка 2, C → картинка 3.")

    elif text=="/images":
        images=db.get("images",[])
        if not images:
            send(cid,"Картинок нет.\n\nДобавь через /setimage")
            return
        send(cid,f"Сохранено {len(images)}/3 картинок. Отправляю:")
        for i, file_id in enumerate(images):
            btns=kb([[(f"🗑 Удалить картинку {i+1}", f"delimg_{i}")]])
            send_photo(cid, file_id, f"Картинка {i+1} из {len(images)}", reply_markup=btns)

    elif text=="/clearimages":
        db["images"]=[]
        save_db(db)
        send(cid,"Все картинки удалены.")

    elif text=="/setwelcomeimage":
        USER_STATE[cid]="awaiting_welcome_image"
        send(cid,"Отправь картинку для приветствия гостей (CLUB ACCESS).\n\nЕё увидит каждый, кто перейдёт по помеченной ссылке из объявления.")

    elif text=="/preview" or text.startswith("/preview@"):
        send(cid,"👇 Так гость видит оффер при входе по ссылке:")
        try:
            send_welcome(cid, db)
        except Exception as e:
            send(cid, f"⚠️ Ошибка показа оффера: {e}")

    elif text=="/groups":
        if not db["groups"]: send(cid,"Групп нет."); return
        t="Группы:\n\n"
        for g in db["groups"]:
            st=gstatus(g["id"],db)
            em={"new":"🔲","active":"✅","dead":"❌"}.get(st,"🔲")
            pubs=[p for p in db["publications"] if p["group_id"]==g["id"]]
            r=sum(1 for p in pubs if p.get("reaction"))
            has_link = "🔗" if g.get("group_link") else "·"
            t+=f"{em} {has_link} {g['name']} ({g['platform']})\n   {g.get('handle','—')} | Публ: {len(pubs)} | Откл: {r}\n\n"
        t+="🔗 = своя ссылка · = общая ссылка"
        send(cid,t)

    elif text=="/add":
        USER_STATE[cid]="awaiting_group"
        send(cid,"Отправь данные:\n\nназвание | @handle | Telegram или Facebook | текст или картинка\n\nПример:\nРусские в Барселоне | @rusbarcelona | Telegram | текст")

    elif text=="/post":
        active=[g for g in db["groups"] if gstatus(g["id"],db)!="dead"]
        if not active: send(cid,"Нет активных групп."); return
        btns=[[(f"{'✅' if gstatus(g['id'],db)=='active' else '🔲'} {g['name']}",f"post_{g['id']}")] for g in active]
        images=db.get("images",[])
        img_note = f"\n\n🖼 Картинок в ротации: {len(images)}/3" if images else "\n\n⚠️ Картинок нет — добавь через /setimage"
        send(cid,f"Выбери группу:{img_note}",reply_markup=kb(btns))

    elif text=="/stats":
        total=len(db["publications"])
        reactions=sum(1 for p in db["publications"] if p.get("reaction"))
        dead=sum(1 for g in db["groups"] if gstatus(g["id"],db)=="dead")
        vc={"A":0,"B":0,"C":0}; vr={"A":0,"B":0,"C":0}
        for p in db["publications"]:
            v=p.get("version","A"); vc[v]=vc.get(v,0)+1
            if p.get("reaction"): vr[v]=vr.get(v,0)+1
        pct=round(reactions/total*100) if total else 0
        groups_with_link=sum(1 for g in db["groups"] if g.get("group_link"))
        images=db.get("images",[])
        send(cid,f"Статистика\n\nГрупп: {len(db['groups'])} (акт: {len(db['groups'])-dead}, мёрт: {dead})\nСвоя ссылка: {groups_with_link} из {len(db['groups'])}\nКартинок в ротации: {len(images)}/3\nПубл: {total} | Откл: {reactions} ({pct}%)\n\nA: {vc['A']} / {vr['A']} откл\nB: {vc['B']} / {vr['B']} откл\nC: {vc['C']} / {vr['C']} откл\n\nОбщая ссылка: {db.get('link','—')}\nДата: {db.get('game_date','—')}")

    elif text=="/setlink":
        USER_STATE[cid]="awaiting_link"
        send(cid,"Отправь новую общую ссылку:")

    elif text=="/setdate":
        USER_STATE[cid]="awaiting_date"
        send(cid,"Отправь новую дату игры:")

    elif text=="/setgrouplink":
        if not db["groups"]: send(cid,"Групп нет."); return
        btns=[(f"{'🔗 ' if g.get('group_link') else '· '}{g['name']}",f"setgl_{g['id']}") for g in db["groups"]]
        send(cid,"Выбери группу для которой хочешь задать уникальную ссылку:",reply_markup=kb([[b] for b in btns]))

    elif text=="/delete":
        if not db["groups"]: send(cid,"Групп нет."); return
        btns=[[(f"🗑 {g['name']}",f"delete_{g['id']}")] for g in db["groups"]]
        send(cid,"Выбери группу для удаления:",reply_markup=kb(btns))

    elif text=="/status":
        if not db["groups"]: send(cid,"Групп нет."); return
        btns=[[(f"{'✅' if gstatus(g['id'],db)=='active' else '❌' if gstatus(g['id'],db)=='dead' else '🔲'} {g['name']}",f"setstatus_{g['id']}")] for g in db["groups"]]
        send(cid,"Выбери группу для смены статуса:",reply_markup=kb(btns))

    elif text=="/lead":
        USER_STATE[cid]="awaiting_lead_name"
        if not db["groups"]:
            send(cid,"Сначала добавь группы через /add")
            return
        btns=[[(f"{g['name']}",f"leadgroup_{g['id']}")] for g in db["groups"]]
        btns.append([("📝 Написал напрямую (не из группы)","leadgroup_direct")])
        send(cid,"Из какой группы написал человек?",reply_markup=kb(btns))

    elif text=="/leads":
        auto_leads=db.get("leads",[])
        manual_leads=db.get("manual_leads",[])
        if not auto_leads and not manual_leads:
            send(cid,"Лидов пока нет.\n\nАвтоматические появятся, когда люди перейдут по помеченной ссылке из объявления.\nРучные добавляются через /lead")
            return
        t=""
        if auto_leads:
            t+=f"🔗 Автоматические лиды — пришли по ссылке ({len(auto_leads)}):\n\n"
            for l in reversed(auto_leads):
                date=l.get("date","")[:10]
                src=l.get("source_group_name","—")
                uid=l.get("user_id","—")
                t+=f"👤 ID {uid}\n   Источник: {src}\n   Дата: {date}\n\n"
        if manual_leads:
            t+=f"📝 Ручные лиды ({len(manual_leads)}):\n\n"
            for l in reversed(manual_leads):
                date=l.get("date","")[:10]
                name=l.get("name","—")
                source=l.get("source","—")
                note=l.get("note","")
                t+=f"👤 {name}\n   Источник: {source}\n   Дата: {date}"
                if note: t+=f"\n   Заметка: {note}"
                t+="\n\n"
        send(cid,t)

    elif text and text.startswith("/find"):
        query = text[5:].strip().lower()
        if not query:
            send(cid, "Напиши что искать:\n/find барселона\n/find @handle")
        else:
            found = [g for g in db["groups"]
                     if query in g["name"].lower() or query in g.get("handle","").lower()]
            if found:
                t = f"Найдено ({len(found)}):\n\n"
                for g in found:
                    st = gstatus(g["id"], db)
                    em = {"new":"🔲","active":"✅","dead":"❌"}.get(st,"🔲")
                    pubs = [p for p in db["publications"] if p["group_id"]==g["id"]]
                    t += f"{em} {g['name']}\n   {g.get('handle','—')} | Публ: {len(pubs)}\n\n"
            else:
                t = f"❌ «{query}» не найдено в базе.\n\nДобавить через /add"
            send(cid, t)

    elif text=="/sources":
        leads = db.get("leads", [])
        if not leads:
            send(cid,"Переходов по меткам пока нет.\n\nКогда кто-то кликнет ссылку из поста и напишет боту — появится здесь.")
        else:
            from collections import Counter
            counts = Counter(l["source_group_name"] for l in leads)
            t = f"Источники ({len(leads)} переходов):\n\n"
            for name, cnt in counts.most_common():
                t += f"• {name}: {cnt}\n"
            send(cid, t)

    elif state=="awaiting_group":
        parts=[p.strip() for p in text.split("|")]
        if len(parts)!=4: send(cid,"Неверный формат.\n\nназвание | @handle | Telegram или Facebook | текст или картинка"); return
        gid=f"g{len(db['groups'])+1}"
        db["groups"].append({"id":gid,"name":parts[0],"handle":parts[1],"platform":parts[2],"format":parts[3],"group_link":""})
        save_db(db); USER_STATE[cid]=None; send(cid,f"Группа {parts[0]} добавлена!")

    elif state=="awaiting_link":
        db["link"]=text.strip(); save_db(db); USER_STATE[cid]=None
        send(cid,f"Общая ссылка обновлена: {db['link']}")

    elif state=="awaiting_date":
        db["game_date"]=text.strip(); save_db(db); USER_STATE[cid]=None
        send(cid,f"Дата игры: {db['game_date']}")

    elif state and state.startswith("awaiting_grouplink_"):
        gid=state.replace("awaiting_grouplink_","")
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if g:
            g["group_link"]=text.strip()
            save_db(db)
            send(cid,f"Ссылка для «{g['name']}» сохранена:\n{g['group_link']}")
        USER_STATE[cid]=None

    elif state and state.startswith("awaiting_lead_name|"):
        source_name=state.split("|",1)[1]
        name=text.strip()
        USER_STATE[cid]=f"awaiting_lead_note|{source_name}|{name}"
        send(cid,f"Имя: {name}\nИсточник: {source_name}\n\nДобавь заметку (что спросил, какой уровень, интерес) или напиши «-» если заметок нет:")

    elif state and state.startswith("awaiting_lead_note|"):
        parts=state.split("|",2)
        source_name=parts[1]
        name=parts[2]
        note=text.strip() if text.strip()!="-" else ""
        if "manual_leads" not in db:
            db["manual_leads"]=[]
        db["manual_leads"].append({
            "name": name,
            "source": source_name,
            "note": note,
            "date": datetime.now().isoformat()
        })
        save_db(db)
        USER_STATE[cid]=None
        msg=f"✅ Лид записан!\n\n👤 {name}\n   Источник: {source_name}"
        if note: msg+=f"\n   Заметка: {note}"
        send(cid,msg)

    else:
        send(cid,"Используй: /post /setimage /images /groups /find /add /delete /status /stats /setlink /setgrouplink /setdate /sources /lead /leads")

def main():
    print("CityPostBot запущен. Остановка: Ctrl+C")
    t = threading.Thread(target=check_schedule, daemon=True)
    t.start()
    print("Планировщик запущен (проверка каждый час)")
    api("deleteWebhook")
    api("setMyCommands", commands=[
        {"command":"start","description":"📋 Шпаргалка — все команды"},
        {"command":"post","description":"📢 Получить текст объявления для группы"},
        {"command":"setimage","description":"🖼 Загрузить картинку для постов (до 3 штук)"},
        {"command":"images","description":"🖼 Посмотреть сохранённые картинки"},
        {"command":"clearimages","description":"🗑 Удалить все картинки"},
        {"command":"groups","description":"👥 Список всех групп со статусами"},
        {"command":"find","description":"🔍 Найти группу по названию или @handle"},
        {"command":"add","description":"➕ Добавить новую группу"},
        {"command":"delete","description":"🗑 Удалить группу из базы"},
        {"command":"status","description":"🔄 Сменить статус группы"},
        {"command":"stats","description":"📊 Статистика публикаций и откликов"},
        {"command":"sources","description":"🔍 Откуда приходят люди (UTM)"},
        {"command":"lead","description":"🎯 Записать заинтересованного человека"},
        {"command":"leads","description":"📋 Список всех лидов"},
        {"command":"setlink","description":"🔗 Изменить общую ссылку в постах"},
        {"command":"setgrouplink","description":"🔗 Уникальная ссылка для группы"},
        {"command":"setdate","description":"📅 Изменить дату игры в объявлениях"},
        {"command":"setwelcomeimage","description":"🎟 Картинка приветствия для гостей"},
        {"command":"preview","description":"👁 Посмотреть оффер глазами гостя"},
    ])
    print("Меню команд зарегистрировано")
    offset=0
    while True:
        try:
            result=api("getUpdates",offset=offset,timeout=30)
            for u in result.get("result",[]):
                offset=u["update_id"]+1
                db=load_db()
                if "callback_query" in u: on_callback(u["callback_query"],db)
                elif "message" in u: on_message(u["message"],db)
        except KeyboardInterrupt:
            print("\nБот остановлен."); break
        except Exception as e:
            print(f"Ошибка: {e}"); time.sleep(5)

if __name__=="__main__":
    main()
