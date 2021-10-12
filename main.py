from flask import Flask, request, abort,render_template, make_response, redirect, session
import os
import re

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    PostbackEvent,FollowEvent, RichMenu, RichMenuArea,
    RichMenuBounds, RichMenuSize, URIAction, QuickReply, QuickReplyButton, messages, URITemplateAction
)
from linebot.models import actions
from linebot.models.actions import MessageAction, PostbackAction
import pandas as pd
from linebot.models.events import ThingsEvent
from unipa_scr import getInfoFromUnipa, check_login
from dataframe_hadler import *
import dotenv
import json
import requests
# database用
from sqlalchemy import create_engine

app = Flask(__name__)
app.secret_key = "4th5h9ir"

URL = "https://250d-210-137-33-126.ngrok.io"

dotenv.load_dotenv("./info/.env")
UserID = os.environ["USERID"]
PassWord = os.environ["PASS"]
line_bot_api = LineBotApi(os.environ["CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

# dbを格納するフォルダを作成
if not os.path.isdir("./users"):
    os.mkdir("users")


# richmenuが存在すれば削除する
richs=[]
for menu in line_bot_api.get_rich_menu_list():
    richs.append(re.search(r"MenuId\": \"(.+)\", \"selected", f'{menu}').group(1))
for rich in richs:
    line_bot_api.delete_rich_menu(rich)

# richmenuを作成
rich_menu_to_create = RichMenu(
    size = RichMenuSize(width=2500, height=1686),
    selected = True,
    name = 'richmenu for unipa',
    chat_bar_text = 'メニュー',
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=1273, height=868),
            action=PostbackAction(data='renew')
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1278, y=0, width=1211, height=864),
            action=PostbackAction(data='deadline')
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=864, width=1268, height=818),
            action=PostbackAction(data="not_submitted")
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=1273, y=877, width=1227, height=805),
            action=PostbackAction(data="forget")
        )
    ]
)
richMenuId = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)

with open("image/menu.png", 'rb') as f:
    line_bot_api.set_rich_menu_image(richMenuId, "image/png", f)
# set the default rich menu
line_bot_api.set_default_rich_menu(richMenuId)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 登録画面を表示する
@app.route("/callback/", methods=["GET"])
def registerform():
    if request.method == 'GET':
        return render_template("index.html")

@app.route("/callback/registerform", methods=["POST", "GET"])
def registered():
    if request.method == 'POST':
        name = request.cookies.get('username')
        pwd = request.cookies.get('password')
        print(name, pwd)
        """
        user = request.form["username"]
        pas = request.form["password"]
        eml = request.form["email"]
        slb = request.form["slabel"]
        user_info = {"user":str(user),"pass":str(pas),"email":str(eml),"slabel":str(slb)}
        print(user)
        print(pas)
        """
        # loginできるかを調べる
        if not check_login(userID=name, PassWord=pwd):
            user_info = {"user":str(name),"pass":str(pwd)}
            # cookieで保存(30日間保存)
            resp = make_response(render_template("index.html"))
            max_age = 60*60*24*10
            resp.set_cookie("user_info",value=json.dumps(user_info),max_age=max_age)
            return render_template("registered_user.html")
        else:
            return redirect(f"/callback/")

    if request.method == 'GET':
        return redirect("/callback/")


# メッセージを受け取った時のアクション
@handler.add(MessageEvent, message=TextMessage)
def send_infomation(event):
    # 変な動作するかも？
    global user_id
    user_id = event.source.user_id
    if event.message.text == '登録':
        items = []
        items.append(QuickReplyButton(action=URIAction(label='登録する', uri=URL + '/callback/registerform'), image_url="https://unipa.u-hyogo.ac.jp/uprx/images/univLogo.png?pfdrid_c=true"))
        items.append(QuickReplyButton(action=PostbackAction(label='登録しない', data='not_register')))
        messages = TextSendMessage(text="ログイン情報を登録する？",
                                quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, messages=messages)

    elif event.message.text == '課題':
        items = []
        items.append(QuickReplyButton(action=PostbackAction(label="見る", data='課題')))
        messages = TextSendMessage(text="課題をみる？",
                                quick_reply=QuickReply(items=items))
        line_bot_api.reply_message(event.reply_token, messages=messages)



    # 更新してとメッセージを受けたらファイルを作成
    elif event.message.text == '更新して':
        try:
            df = getInfoFromUnipa(UserID=UserID, PassWord=PassWord)
            # databaseに登録
            engine = create_engine(f'sqlite:///users/{user_id}.db', echo=False)
            df.to_sql('homeworks', con=engine, index=False, if_exists='replace')

            line_bot_api.push_message(
            to=user_id,
            messages=TextSendMessage(text='更新が完了したよ')
            )
        except Exception as e:
            line_bot_api.push_message(
            to=user_id,
            messages=TextSendMessage(text=f'{e}')
            )
    else:
        line_bot_api.push_message(
        to=user_id,
        messages=TextSendMessage(text = 'よくわからないよ')
        )

# 友達追加・ブロック解除時のアクション
@handler.add(FollowEvent)
def on_follow(event):
    return

@handler.add(ThingsEvent)
def on_things(event):
    return

# ボタンなどの反応があった時のアクション
@handler.add(PostbackEvent)
def on_postback(event):
    user_id = event.source.user_id
    postback_msg = event.postback.data
    if postback_msg == 'not_register':
        line_bot_api.push_message(
        to=user_id,
        messages=TextSendMessage(text='まずは登録しよう')
        )
    # cookie情報を取得
    elif postback_msg == '課題':
        username = session['name']
        pwd = session['pwd']
        print(username)
        print(pwd)
    else:
        # 更新ボタンが押されたら（左上のボタン）課題情報を最新にする
        if postback_msg == 'renew':
            try:
                df = getInfoFromUnipa(UserID=UserID, PassWord=PassWord)
                # databaseに登録
                engine = create_engine(f'sqlite:///users/{user_id}.db', echo=False)
                df.to_sql('homeworks', con=engine, index=False, if_exists='replace')

                line_bot_api.push_message(
                to=user_id,
                messages=TextSendMessage(text='更新が完了したよ')
                )
            except:
                line_bot_api.push_message(
                to=user_id,
                messages=TextSendMessage(text='情報の取得に失敗したよ')
                )
        elif os.path.isfile(f'users/{user_id}.db'):
            engine = create_engine(f'sqlite:///users/{user_id}.db', echo=False)
            df = pd.read_sql("SELECT * FROM homeworks", engine)
            # 締切間近の課題ボタンが押されたら（右上のボタン）
            if postback_msg == 'deadline':
                deadline_homework = make_deadline_str(df)
                if deadline_homework == '締め切りが近い課題は':
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text="締め切りが近い課題はないよ！")
                    )
                else:
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text=deadline_homework)
                    )                
            
            # 未提出の課題ボタンが押されたら（左下のボタン）
            elif postback_msg == 'not_submitted':
                not_submit_homework = make_not_submmit_str(df)
                if not_submit_homework == '未提出の課題は':
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text="未提出の課題はないよ！")
                    )
                else:
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text=not_submit_homework)
                    )

            # 出し忘れの課題ボタンが押されたら（右下のボタン）
            elif postback_msg == 'forget':
                rest_homework = make_forget_homework_str(df)
                if rest_homework == '出し忘れた課題は':
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text="出し忘れた課題はないよ！")
                    )
                else:
                    line_bot_api.push_message(
                    to=user_id,
                    messages=TextSendMessage(text=rest_homework)
                    )                
        elif not os.path.isfile(f'users/{user_id}.db'):
            line_bot_api.push_message(
            to=user_id,
            messages=TextSendMessage(text='最初は左上の「最新の課題に更新」を押してね')
            )

# ユーザーの名前を取得する
def getDisplayName(user_id):
    access = os.environ["CHANNEL_ACCESS_TOKEN"]
    headers = {
        "Authorization": f"Bearer {access}"
    }
    response = requests.get(f"https://api.line.me/v2/bot/profile/{user_id}",headers=headers)
    return response

# 連携
def get_link_token(user_id):
    access = os.environ["CHANNEL_ACCESS_TOKEN"]
    headers = {
        "Authorization": f"Bearer {access}"
    }
    response = requests.get(f"https://api.line.me/v2/bot/user/{user_id}/linkToken",headers=headers)
    return response

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)