import json, os, urllib.request, time
from datetime import datetime

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
    {"id":"g1","name":"Испания чат | СНГ","handle":"@spainchats","platform":"Telegram","format":"текст"},
    {"id":"g2","name":"Испания | Для Своих","handle":"@spain_chatss","platform":"Telegram","format":"текст"},
    {"id":"g3","name":"Валенсия / Costa Blanca","handle":"@costablanka","platform":"Telegram","format":"текст"},
    {"id":"g4","name":"Испания чат | Spain News","handle":"@SpainNewsChat","platform":"Telegram","format":"текст"},
    {"id":"g5","name":"Наши в Мадриде","handle":"—","platform":"Telegram","format":"текст"},
    {"id":"g6","name":"Digital Nomad Spain","handle":"@chatfornomads","platform":"Telegram","format":"текст"},
    {"id":"g7","name":"Марбелья / Costa del Sol","handle":"@Marbella_reklama","platform":"Telegram","format":"текст"},
    {"id":"g8","name":"Business в Испании","handle":"@konciergemarket","platform":"Telegram","format":"текст"},
    {"id":"g9","name":"ВНЖ Испании Чат","handle":"—","platform":"Telegram","format":"текст"},
    {"id":"g10","name":"Русские в Малаге","handle":"@russkie_malaga","platform":"Telegram","format":"текст"},
]

def load_db():
    try:
        with open(DB_PATH,"r",encoding="utf-8") as f:
            return json.load(f)
    except:
        db={"groups":DEFAULT_GROUPS,"publications":[],"link":"https://t.me/lacataciegas","game_date":"13 июня"}
        save_db(db)
        return db

def save_db(db):
    with open(DB_PATH,"w",encoding="utf-8") as f:
        json.dump(db,f,ensure_ascii=False,indent=2)

def api(method,**params):
    data=json.dumps(params).encode()
    req=urllib.request.Request(f"{BOT_URL}/{method}",data=data,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {method}: {e}")
        return {}

def send(chat_id,text,reply_markup=None):
    p={"chat_id":chat_id,"text":text}
    if reply_markup: p["reply_markup"]=reply_markup
    api("sendMessage",**p)

def edit(chat_id,msg_id,text,reply_markup=None):
    p={"chat_id":chat_id,"message_id":msg_id,"text":text}
    if reply_markup: p["reply_markup"]=reply_markup
    api("editMessageText",**p)

def kb(buttons):
    return {"inline_keyboard":[[{"text":b[0],"callback_data":b[1]} for b in row] for row in buttons]}

def next_ver(gid,db):
    pubs=[p for p in db["publications"] if p["group_id"]==gid]
    v=["A","B","C"]
    if not pubs: return "A"
    return v[(v.index(pubs[-1].get("version","A"))+1)%3]

def gstatus(gid,db):
    pubs=[p for p in db["publications"] if p["group_id"]==gid]
    if not pubs: return "new"
    r=pubs[-3:]
    if len(r)>=3 and all(not p.get("reaction") for p in r): return "dead"
    return "active"

def on_callback(cq,db):
    cid=cq["message"]["chat"]["id"]
    mid=cq["message"]["message_id"]
    data=cq["data"]
    api("answerCallbackQuery",callback_query_id=cq["id"])

    if data.startswith("post_"):
        gid=data[5:]
        g=next((x for x in db["groups"] if x["id"]==gid),None)
        if not g: return
        ver=next_ver(gid,db)
        text=ADS[ver].format(game_date=db.get("game_date","13 июня"),link=db.get("link",""))
        edit(cid,mid,
            f"Группа: {g['name']} | {g['platform']}\nВерсия: {ver}\n\n"+"─"*30+f"\n\n{text}\n\n"+"─"*30+"\n\nСкопируй текст выше и опубликуй в группу.",
            reply_markup=kb([[("✅ Отправила",f"sent_{gid}_{ver}"),("⏭ Пропустить",f"skip_{gid}")]]))

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
        edit(cid,mid,"Группа мертвая — убрана из ротации." if st=="dead" else "Записала! Следующая через 4 дня.")

    elif data.startswith("skip_"):
        edit(cid,mid,"Пропустили.")

def on_message(msg,db):
    cid=msg["chat"]["id"]
    text=msg.get("text","")
    if cid!=ADMIN_ID: return
    state=USER_STATE.get(cid)

    if text=="/start":
        USER_STATE[cid]=None
        send(cid,"CityPostBot — помощник по постингу\n\n/post — текст для публикации\n/groups — список групп\n/add — добавить группу\n/stats — статистика\n/setlink — изменить ссылку\n/setdate — изменить дату игры")
    elif text=="/groups":
        if not db["groups"]: send(cid,"Групп нет."); return
        t="Группы:\n\n"
        for g in db["groups"]:
            st=gstatus(g["id"],db)
            em={"new":"🔲","active":"✅","dead":"❌"}.get(st,"🔲")
            pubs=[p for p in db["publications"] if p["group_id"]==g["id"]]
            r=sum(1 for p in pubs if p.get("reaction"))
            t+=f"{em} {g['name']} ({g['platform']})\n   {g.get('handle','—')} | Публ: {len(pubs)} | Откл: {r}\n\n"
        send(cid,t)
    elif text=="/add":
        USER_STATE[cid]="awaiting_group"
        send(cid,"Отправь данные:\n\nназвание | @handle | Telegram или Facebook | текст или картинка\n\nПример:\nРусские в Барселоне | @rusbarcelona | Telegram | текст")
    elif text=="/post":
        active=[g for g in db["groups"] if gstatus(g["id"],db)!="dead"]
        if not active: send(cid,"Нет активных групп."); return
        btns=[[(f"{'✅' if gstatus(g['id'],db)=='active' else '🔲'} {g['name']}",f"post_{g['id']}")] for g in active]
        send(cid,"Выбери группу:",reply_markup=kb(btns))
    elif text=="/stats":
        total=len(db["publications"])
        reactions=sum(1 for p in db["publications"] if p.get("reaction"))
        dead=sum(1 for g in db["groups"] if gstatus(g["id"],db)=="dead")
        vc={"A":0,"B":0,"C":0}; vr={"A":0,"B":0,"C":0}
        for p in db["publications"]:
            v=p.get("version","A"); vc[v]=vc.get(v,0)+1
            if p.get("reaction"): vr[v]=vr.get(v,0)+1
        pct=round(reactions/total*100) if total else 0
        send(cid,f"Статистика\n\nГрупп: {len(db['groups'])} (акт: {len(db['groups'])-dead}, мёрт: {dead})\nПубл: {total} | Откл: {reactions} ({pct}%)\n\nA: {vc['A']} / {vr['A']} откл\nB: {vc['B']} / {vr['B']} откл\nC: {vc['C']} / {vr['C']} откл\n\nСсылка: {db.get('link','—')}\nДата: {db.get('game_date','—')}")
    elif text=="/setlink":
        USER_STATE[cid]="awaiting_link"; send(cid,"Отправь новую ссылку:")
    elif text=="/setdate":
        USER_STATE[cid]="awaiting_date"; send(cid,"Отправь новую дату игры:")
    elif state=="awaiting_group":
        parts=[p.strip() for p in text.split("|")]
        if len(parts)!=4: send(cid,"Неверный формат.\n\nназвание | @handle | Telegram или Facebook | текст или картинка"); return
        gid=f"g{len(db['groups'])+1}"
        db["groups"].append({"id":gid,"name":parts[0],"handle":parts[1],"platform":parts[2],"format":parts[3]})
        save_db(db); USER_STATE[cid]=None; send(cid,f"Группа {parts[0]} добавлена!")
    elif state=="awaiting_link":
        db["link"]=text.strip(); save_db(db); USER_STATE[cid]=None; send(cid,f"Ссылка: {db['link']}")
    elif state=="awaiting_date":
        db["game_date"]=text.strip(); save_db(db); USER_STATE[cid]=None; send(cid,f"Дата игры: {db['game_date']}")
    else:
        send(cid,"Используй: /post /groups /add /stats /setlink /setdate")

def main():
    print("CityPostBot запущен. Остановка: Ctrl+C")
    api("deleteWebhook")
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
