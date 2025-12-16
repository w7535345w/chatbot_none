import os
import csv
import time
from datetime import datetime
import base64

import streamlit as st

# ================== 基本设置 ==================

# 本机器人属于哪个条件（你可以复制三份 app.py，分别改成 "A" / "B" / "C"）
BOT_CONDITION = "C"

# GIF：放在同一目录下，或你自己改路径
TYPING_GIF_PATH = {
    "A": "text.gif",
    "B": "0929_mark2.gif",
    "C": None,          # 条件C 不显示“输入中”
}

# 机器人头像图片（例如 bot_avatar.png）
BOT_AVATAR_PATH = "bot_avatar.png"   # 请把你的头像图片命名/放好

LOG_FILE = "chat_log.csv"


# ================== 固定回答逻辑 ==================

def get_bot_reply(user_input: str) -> str:
    text = user_input.strip()

    if "価格" in text or "値段" in text or "いくら" in text:
        return "こちらの商品の税込価格は80,000円です。割引やキャンペーンにつきましては、商品ページにてご確認いただけます。"
    elif "返品" in text or "交換" in text:
        return "返品・交換は商品到着後7日以内であれば可能です。詳しい条件はご利用規約をご確認ください。"
    elif "おすすめ" in text or "オススメ" in text or "用途" in text or "使い方" in text or "使用方法" in text:
        return "このモデルは高画質のセンサーを搭載し、フルハイビジョン動画の撮影に対応しています。それにもかかわらず、操作はシンプルで、豊富な撮影モードを備えているため、初心者からプロの方まで幅広くおすすめします！詳しい使用方法は取扱説明書をご確認ください。"
    elif "様式" in text or "色" in text or "スタイル" in text:
        return "現在、こちらの商品には、他のスタイルやカラーの在庫はございません。今後の入荷予定につきましては、商品ページにてご確認いただけます。"
    elif "商品スペック" in text or "特徴" in text or "属性" in text:
        return "こちらの商品は、本体サイズ約101.3×129×77.6mm、本体重量約475gの標準レンズ付きモデルです。撮影画面サイズは約22.3×14.9mmで、最高ISO12800相当まで感度拡張が可能です。最高約3.0コマ/秒の連続撮影に対応しています。WI-FI機能を搭載しており、スマホとの連携も可能なため、撮影した高画質な写真を手軽にSNSへ投稿できます！ハードウェアの詳細情報は、商品ページおよび取扱説明書をご確認ください。"
    elif "配送" in text or "届く" in text or "届き" in text:
        return "通常の配送の場合、発送から3~4営業日ほどでお届け予定です。"
    elif "ありがとう" in text or "感謝" in text or "OK" in text or "わかりました"in text or "分かりました" in text or "了解" in text:
        return "お役に立てると嬉しいです！またのご質問をお待ちしております。"
    elif text == "":
        return "何か気になることがあれば、自由にご質問ください。"
    else:
        return "ご質問ありがとうございます。こちらの商品について、もう少し具体的に知りたい点を教えていただけますか？"


# ================== 日志记录 ==================

def log_interaction(session_id: str, cond: str, role: str, message: str):
    os.makedirs("logs", exist_ok=True)
    filepath = os.path.join("logs", LOG_FILE)
    now = datetime.now().isoformat(timespec="seconds")

    header = ["timestamp", "session_id", "condition", "role", "message"]
    write_header = not os.path.exists(filepath)

    with open(filepath, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(header)
        writer.writerow([now, session_id, cond, role, message])


# ================== 辅助函数：图片/GIF 转 base64 ==================

def image_to_base64(path: str):
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        b = f.read()
    return base64.b64encode(b).decode("utf-8")


# 消息气泡 HTML（左右对齐 + 圆角），附带 HTML 转义，防止显示代码
def render_message_html(role: str, content: str, bot_avatar_src: str | None) -> str:
    safe_content = (
        content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if role == "assistant":
        avatar_html = ""
        if bot_avatar_src:
            avatar_html = f'<img src="{bot_avatar_src}" class="avatar" />'
        return f"""
        <div class="msg-row bot">
            {avatar_html}
            <div class="bubble bot-bubble">{safe_content}</div>
        </div>
        """
    else:  # user
        return f"""
        <div class="msg-row user">
            <div class="bubble user-bubble">{safe_content}</div>
        </div>
        """


# “输入中”行：头像 + GIF 在左侧
def render_typing_html(bot_avatar_src: str | None, gif_path: str, width: int = 60) -> str:
    if not os.path.exists(gif_path):
        return ""
    with open(gif_path, "rb") as f:
        data = f.read()
    gif_b64 = base64.b64encode(data).decode("utf-8")

    avatar_html = ""
    if bot_avatar_src:
        avatar_html = f'<img src="{bot_avatar_src}" class="avatar" />'

    return f"""
    <div class="msg-row bot typing-row">
        {avatar_html}
        <img src="data:image/gif;base64,{gif_b64}" class="typing-gif" width="{width}" />
    </div>
    """
def render_typing_dots_html(bot_avatar_src: str | None, dots: str = "…") -> str:
    avatar_html = ""
    if bot_avatar_src:
        avatar_html = f'<img src="{bot_avatar_src}" class="avatar" />'
    return f"""
    <div class="msg-row bot typing-row">
        {avatar_html}
        <div class="bubble bot-bubble typing-bubble">{dots}</div>
    </div>
    """


# ================== 页面 CSS（边框 + 头部 + 气泡样式） ==================

CUSTOM_CSS = """
<style>
/* 背景颜色 */
body {
    background-color: #f2f2f2;
}

/* 主区域居中 */
.main {
    max-width: 900px;
    margin: 0 auto;
}

/* Streamlit 外层容器稍微收窄，并透明一点 */
.block-container {
    padding-top: 0.5rem;
    background-color: transparent;
}

/* ==== 聊天窗口整体：有固定宽度 + 圆角边框 + 阴影 ==== */
.chat-wrapper {
    max-width: 820px;
    margin: 24px auto;
    border: 3px solid #bfbfbf;          /* 边框颜色 */
    border-radius: 18px;                 /* 圆角 */
    background-color: #000000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);  /* 立体感 */
    overflow: hidden;                    /* 让边角干净 */
}

/* 顶部栏 */
.chat-header {
    background: linear-gradient(135deg, #4a90e2, #6ec6ff);
    color: #ffffff;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.chat-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.chat-header-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.chat-header-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.chat-header-title {
    font-size: 15px;
    font-weight: 600;
}

.chat-header-subtitle {
    font-size: 12px;
    opacity: 0.9;
}

.chat-header-right {
    font-size: 12px;
    opacity: 0.9;
}

/* 聊天体区域（消息区） */
.chat-body {
    padding: 12px 14px 10px 14px;
    max-height: 500px;
    overflow-y: auto;
    background-color: #fafafa;
}

/* 每一行消息（旧在上，新在下） */
.msg-row {
    display: flex;
    margin-bottom: 8px;
}

/* 机器人在左 */
.msg-row.bot {
    justify-content: flex-start;
}

/* 用户在右 */
.msg-row.user {
    justify-content: flex-end;
}

/* 头像 */
.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    margin-right: 8px;
    object-fit: cover;
}

/* 气泡基础样式 */
.bubble {
    padding: 8px 12px;
    border-radius: 16px;
    max-width: 75%;
    font-size: 14px;
    line-height: 1.4;
}

/* 机器人气泡：淡灰色 + 细边框 */
.bot-bubble {
    background-color: #f2f2f2;
    color: #333333;
    border: 1px solid #d9d9d9;
    border-radius: 16px 16px 16px 4px;
}

/* 用户气泡：淡蓝色 */
.user-bubble {
    background-color: #d8eafe;
    color: #003366;
    border-radius: 16px 16px 4px 16px;
}

/* 输入中行（GIF） */
.typing-row {
    align-items: center;
}

.typing-gif {
    border-radius: 12px;
}
.visibility: hidden{
    opacity: 0.7;
    font-weight: 600;
}


/* 去掉默认侧边栏 */
[data-testid="stSidebar"] {
    display: none;
}
</style>
"""


# ================== 主程序 ==================

def main():
    st.set_page_config(page_title="オンラインチャット", page_icon="💬", layout="centered")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ---------- 会话状态初始化 ----------
    if "messages" not in st.session_state:
        st.session_state.messages = []  # [{"role": "assistant"/"user", "content": "..."}]
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    if "initialized" not in st.session_state:
        st.session_state.initialized = False

    session_id = st.session_state.session_id

    # 头像 base64（头部 + 消息里都会用）
    bot_avatar_b64 = image_to_base64(BOT_AVATAR_PATH)
    bot_avatar_src = f"data:image/png;base64,{bot_avatar_b64}" if bot_avatar_b64 else None

    # 初次进入时，添加一条机器人开场白
    if not st.session_state.initialized:
        greeting = "こんにちは、当店へようこそ。私はAIカスタマーサービスです。ご用件をお伺いしてもよろしいでしょうか？"
        st.session_state.messages.append({"role": "assistant", "content": greeting})
        log_interaction(session_id, BOT_CONDITION, "assistant", greeting)
        st.session_state.initialized = True

    # ---------- 布局：先占好聊天区域，再读输入 ----------
    chat_container = st.container()

    # 输入框：放在代码上，但逻辑上先处理输入，再在 container 里统一渲染
    pending_reply = None
    user_input = st.chat_input("ご質問を入力してください…")

    if user_input:
        text = user_input.strip()
        if text != "":
            # 更新历史：先加入用户消息
            st.session_state.messages.append({"role": "user", "content": text})
            log_interaction(session_id, BOT_CONDITION, "user", text)

            # 计算机器人的固定回复，本轮稍后显示
            pending_reply = get_bot_reply(text)

    # ---------- 在 container 中渲染整个聊天窗口 ----------
    with chat_container:
        # 外层固定边框盒子
        st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

        # 顶部栏
        header_avatar_html = (
            f'<div class="chat-header-avatar"><img src="{bot_avatar_src}" /></div>'
            if bot_avatar_src else
            '<div class="chat-header-avatar"></div>'
        )

        st.markdown(
            f"""
            <div class="chat-header">
                <div class="chat-header-left">
                    {header_avatar_html}
                    <div>
                        <div class="chat-header-title">カスタマーサポート</div>
                        <div class="chat-header-subtitle">オンライン · 平日 10:00–18:00</div>
                    </div>
                </div>
                <div class="chat-header-right">
                    チャットサポート
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 聊天内容区域开始
        st.markdown('<div class="chat-body">', unsafe_allow_html=True)

        # 1. 渲染当前所有历史消息（旧在上，新在下）
        history_html_parts = []
        for msg in st.session_state.messages:
            history_html_parts.append(
                render_message_html(msg["role"], msg["content"], bot_avatar_src)
            )
        st.markdown("".join(history_html_parts), unsafe_allow_html=True)

        # 2. 如果本轮有 pending_reply，在最下方显示“输入中”GIF → 真实回复
        GIF_DELAY_SEC = 5.0
        NO_GIF_DELAY_SEC = 5.0

        if pending_reply is not None:
            gif_path = TYPING_GIF_PATH.get(BOT_CONDITION)
            use_gif = bool(gif_path) and (BOT_CONDITION in ["A", "B"])

            # ✅ 关键：不管有没有GIF，都用 placeholder，避免“新增元素淡入导致透明闪烁”
            reply_placeholder = st.empty()

            if use_gif:
                reply_placeholder.markdown(
                    render_typing_html(bot_avatar_src, gif_path, width=75),
                    unsafe_allow_html=True
                )
                time.sleep(GIF_DELAY_SEC)
            else:
                # 条件C：不显示GIF，但仍然显示一个很轻的“…”并延迟
                reply_placeholder.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)

                time.sleep(NO_GIF_DELAY_SEC)

            # 用同一个 placeholder 替换为最终回复（不会闪/透明）
            bot_html = render_message_html("assistant", pending_reply, bot_avatar_src)
            reply_placeholder.markdown(bot_html, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": pending_reply})
            log_interaction(session_id, BOT_CONDITION, "assistant", pending_reply)


        # 结束 chat-body 和 chat-wrapper
        st.markdown("</div></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
