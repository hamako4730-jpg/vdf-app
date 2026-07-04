import streamlit as st
import sqlite3
import requests
import datetime

# システム定数
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKERS = {
    "四国めたん (ノーマル)": 2,
    "春日部つむぎ (ノーマル)": 8
}
DB_NAME = "daily_goals.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (date TEXT PRIMARY KEY, goal TEXT, tasks TEXT)''')
    conn.commit()
    conn.close()

def save_goal(date, goal, tasks):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO goals (date, goal, tasks) VALUES (?, ?, ?)", (date, goal, tasks))
    conn.commit()
    conn.close()

def generate_voice(text, speaker_id):
    try:
        query_res = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": speaker_id}
        )
        query_res.raise_for_status()
        synth_res = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": speaker_id},
            json=query_res.json()
        )
        synth_res.raise_for_status()
        return synth_res.content
    except requests.exceptions.RequestException:
        st.error("[System Error] VOICEVOXとの通信に失敗しました。VOICEVOXが起動しているか確認してください。")
        return None

# UI構成 (VDF仕様 - タイトル1行化対応)
st.set_page_config(page_title="VDF. System", page_icon="⚙️")

# CSSを注入してタイトルを1行に強制し、画面幅に合わせてサイズを自動調整する
st.markdown("""
    <style>
    .vdf-title {
        font-size: clamp(1.2rem, 4vw, 2.5rem);
        white-space: nowrap;
        font-weight: bold;
        padding-bottom: 1rem;
    }
    </style>
    <div class="vdf-title">VDF. (バイブデザインファクトリー)</div>
""", unsafe_allow_html=True)

init_db()
today_str = datetime.date.today().strftime("%Y-%m-%d")
st.write(f"**システム日付:** {today_str}")

st.markdown("### 1. 目標定義 (Core Vibe)")
goal_text = st.text_area("今日の目標", height=100)

st.markdown("### 2. タスク分解 (Sync Tasks)")
tasks_text = st.text_area("実行タスクリスト", height=150, help="タスクを改行して入力してください。")

st.markdown("### 3. システム設定")
selected_voice = st.radio("音声モデル選択", list(SPEAKERS.keys()), horizontal=True)

if st.button("VDFルーティンを開始", type="primary"):
    if not goal_text.strip():
        st.warning("目標が入力されていません。Core Vibeを定義してください。")
    else:
        save_goal(today_str, goal_text, tasks_text)
        st.success("データベースへの同期が完了しました。")

        speech_text = f"代表、おはようございます。本日の目標は、{goal_text}、ですね。"
        if tasks_text.strip():
            formatted_tasks = tasks_text.replace('\n', '、')
            speech_text += f"実行するタスクは、{formatted_tasks}、です。"
        speech_text += "本日も1日、ミッションを完遂しましょう。"

        speaker_id = SPEAKERS[selected_voice]
        
        with st.spinner('VOICEVOX音声エンジンで合成中...'):
            audio_data = generate_voice(speech_text, speaker_id)
            if audio_data:
                st.audio(audio_data, format="audio/wav")