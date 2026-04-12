import streamlit as st
import google.generativeai as genai
import os
import json
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Data import
from data.morphemes import ALL_MORPHEMES

# --- Page Configuration ---
st.set_page_config(
    page_title="EtymOS",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main background and text */
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Card design */
    .stCard {
        background-color: #1e2227;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stCard:hover {
        transform: translateY(-5px);
        border-color: #58a6ff;
    }
    
    /* Morpheme Tags */
    .tag-prefix { color: #3498db; font-weight: bold; }
    .tag-root { color: #f1c40f; font-weight: bold; }
    .tag-suffix { color: #2ecc71; font-weight: bold; }
    
    /* Frequency indicators */
    .freq-high { color: #2ecc71; }
    .freq-medium { color: #f1c40f; }
    .freq-low { color: #95a5a6; }
    
    /* Header styling */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom columns for decomposition */
    .part-box {
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        margin: 5px;
        min-width: 100px;
    }
    .bg-prefix { background-color: rgba(52, 152, 219, 0.1); border: 1px solid #3498db; }
    .bg-root { background-color: rgba(241, 196, 15, 0.1); border: 1px solid #f1c40f; }
    .bg-suffix { background-color: rgba(46, 204, 113, 0.1); border: 1px solid #2ecc71; }
</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False

# --- Sidebar ---
st.sidebar.title("📖 EtymOS")
st.sidebar.markdown("---")

# Page Selection
page = st.sidebar.radio(
    "メニュー",
    ["語源辞典", "単語分解", "クイズ", "語根ワールド", "今日の語根"],
    index=0
)

# API Key logic
api_key = None

# Priority for API key:
# 1. Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
# 2. Environment Variables
elif os.getenv("GEMINI_API_KEY"):
    api_key = os.getenv("GEMINI_API_KEY")

# API Key Input in Sidebar (Manual override/fallback)
api_key_input = st.sidebar.text_input(
    "Gemini API Key",
    value=api_key if api_key else "",
    type="password",
    help="Secrets または 環境変数に設定されている場合は自動入力されます。"
)

# Use manual input if provided
if api_key_input:
    api_key = api_key_input

# Score Display
st.sidebar.markdown("---")
st.sidebar.metric("現在のスコア", f"{st.session_state.score} pts")

# Tooltip for sidebar
st.sidebar.info("語源をマスターして、英単語の迷宮を抜け出そう。")

# --- Utility Functions ---
def call_gemini(prompt):
    if not api_key:
        return None, "APIキーが設定されていません。"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.Generative("gemini-flash-lite-latest")
        response = model.generate_content(prompt)
        text = response.text
        
        # Extract JSON from response (handling potential markdown formatting)
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[-1].split("```")[0].strip()
            
        return json.loads(text), None
    except Exception as e:
        return None, f"API呼び出しに失敗しました: {str(e)}"

def render_morpheme_card(m):
    color_class = f"tag-{m['type']}"
    freq_class = f"freq-{m['frequency']}"
    examples_str = ", ".join(m['examples']) if isinstance(m['examples'], list) else m['examples']
    
    st.markdown(f"""
    <div class="stCard">
        <h3 class="{color_class}">{m['morpheme']}</h3>
        <p><strong>意味:</strong> {m['meaning']}</p>
        <p><strong>由来:</strong> {m['origin']}</p>
        <p><strong>例語:</strong> {examples_str}</p>
        <p><strong>頻度:</strong> <span class="{freq_class}">{m['frequency'].upper()}</span></p>
        <p><strong>関連語数:</strong> 約{m['related_count']}語</p>
        <hr style="border: 0.5px solid #30363d;">
        <p style="font-size: 0.9em; font-style: italic; color: #8b949e;">💡 {m['memory_hint']}</p>
    </div>
    """, unsafe_allow_html=True)

# --- Tab Logic ---
if page == "語源辞典":
    st.title("📚 語源辞典")
    
    # Filter and Search
    col1, col2 = st.columns([1, 2])
    with col1:
        type_filter = st.multiselect(
            "パーツの種類",
            ["prefix", "root", "suffix"],
            default=["prefix", "root", "suffix"]
        )
    with col2:
        search_query = st.text_input("検索", placeholder="語根、意味、例語など...")
        
    filtered_data = [
        m for m in ALL_MORPHEMES 
        if m['type'] in type_filter 
        and (search_query.lower() in m['morpheme'].lower() 
             or search_query.lower() in m['meaning'].lower() 
             or any(search_query.lower() in ex.lower() for ex in m['examples']))
    ]
    
    # Display Grid
    if not filtered_data:
        st.warning("該当する語根が見つかりませんでした。")
    else:
        # 3 columns grid
        cols = st.columns(3)
        for idx, m in enumerate(filtered_data):
            with cols[idx % 3]:
                render_morpheme_card(m)

elif page == "単語分解":
    st.title("🔍 単語分解")
    st.markdown("英単語を入力すると、その成り立ちをAIが視覚的に分解・解説します。")
    
    word_input = st.text_input("英単語を入力してください（例: transportation）", key="word_breakdown")
    
    if word_input:
        with st.spinner("AIが分解中..."):
            prompt = f"""
            英単語「{word_input}」を語源分解してください。
            以下のJSON形式のみで返してください（マークダウン不要）：
            {{
              "word": "{word_input}",
              "parts": [
                {{"text": "trans", "role": "prefix", "meaning": "越えて"}},
                {{"text": "port", "role": "root", "meaning": "運ぶ"}},
                {{"text": "ation", "role": "suffix", "meaning": "名詞化"}}
              ],
              "image_memory": "国境を越えて港から荷物を運ぶ船のイメージ",
              "etymology_story": "ラテン語のtransportareから。古代ローマで..."
            }}
            """
            result, error = call_gemini(prompt)
            
            if error:
                st.error(error)
            else:
                # Layout
                st.subheader(f"Analysis: {result['word']}")
                
                # Render parts
                cols = st.columns(len(result['parts']))
                for i, part in enumerate(result['parts']):
                    role = part['role']
                    bg_class = f"bg-{role}"
                    tag_class = f"tag-{role}"
                    with cols[i]:
                        st.markdown(f"""
                        <div class="part-box {bg_class}">
                            <div class="{tag_class}" style="font-size: 1.5em;">{part['text']}</div>
                            <div style="font-size: 0.8em; color: #8b949e;">{role.upper()}</div>
                            <div style="margin-top: 5px;">{part['meaning']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("💡 イメージ記憶法")
                st.success(result['image_memory'])
                
                with st.expander("📖 語源ストーリー"):
                    st.write(result['etymology_story'])

elif page == "クイズ":
    st.title("🧠 語源クイズ")
    
    # Quiz Filters
    q_type = st.selectbox("出題範囲を選択", ["すべて", "prefix", "root", "suffix"])
    if q_type == "すべて":
        q_pool = ALL_MORPHEMES
    else:
        q_pool = [m for m in ALL_MORPHEMES if m['type'] == q_type]
        
    if not q_pool:
        st.warning("選択した範囲にデータがありません。")
    else:
        # Initialize quiz if not exists or if type changed
        if 'current_quiz' not in st.session_state or st.session_state.get('last_q_type') != q_type:
            target = random.choice(q_pool)
            options = [target['meaning']]
            distractors = [m['meaning'] for m in ALL_MORPHEMES if m['meaning'] != target['meaning']]
            options.extend(random.sample(distractors, min(3, len(distractors))))
            random.shuffle(options)
            
            st.session_state.current_quiz = {
                'target': target,
                'options': options,
                'answered': False,
                'is_correct': False
            }
            st.session_state.last_q_type = q_type

        q = st.session_state.current_quiz
        target = q['target']
        
        st.subheader(f"この語源の意味は何？")
        st.info(f"語源: **{target['morpheme']}** ({target['type']})")
        
        # Display options
        for opt in q['options']:
            if st.button(opt, key=f"opt_{opt}", disabled=q['answered'], use_container_width=True):
                q['answered'] = True
                if opt == target['meaning']:
                    q['is_correct'] = True
                    st.session_state.score += 10
                    st.balloons()
                st.rerun()

        if q['answered']:
            if q['is_correct']:
                st.success(f"正解！: {target['meaning']}")
            else:
                st.error(f"残念！正解は: {target['meaning']}")
            
            # Post-answer Gemini content
            if 'explanation' not in q:
                with st.spinner("AIが記憶法を生成中..."):
                    prompt = f"""
                    英語の語根「{target['morpheme']}」（意味：{target['meaning']}、由来：{target['origin']}）について、
                    例語「{", ".join(target['examples'])}」を使って以下のJSON形式で返してください：
                    {{
                      "goroawase": "語呂合わせ（日本語で）",
                      "image": "例語から連想できるイメージ記憶法",
                      "story": "この語根の歴史的な語源ストーリー（2〜3文）"
                    }}
                    """
                    result, error = call_gemini(prompt)
                    if not error:
                        q['explanation'] = result
            
            if 'explanation' in q:
                exp = q['explanation']
                st.markdown("### 💡 3パターン記憶法")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**1. 語呂合わせ**")
                    st.write(exp['goroawase'])
                with col2:
                    st.markdown("**2. イメージ連想**")
                    st.write(exp['image'])
                with col3:
                    st.markdown("**3. 語源ストーリー**")
                    st.write(exp['story'])
            
            if st.button("次の問題へ"):
                del st.session_state.current_quiz
                st.rerun()

elif page == "語根ワールド":
    st.title("🌐 語根ワールド")
    st.markdown("特定の語根から広がる英単語の世界を探索しましょう。")
    
    selected_text = st.selectbox("探索する語根を選択", [m['morpheme'] for m in ALL_MORPHEMES])
    target = next(m for m in ALL_MORPHEMES if m['morpheme'] == selected_text)
    
    if st.button("探索する", type="primary"):
        with st.spinner(f"{target['morpheme']} の世界を解析中..."):
            prompt = f"""
            語根「{target['morpheme']}」（意味：{target['meaning']}、由来：{target['origin']}）について、
            以下のJSON形式のみで返してください：
            {{
              "派生語リスト": [
                {{
                  "word": "inspect",
                  "meaning": "調査する",
                  "breakdown": "in(中に)+spect(見る)",
                  "toeic_level": "500"
                }}
              ],
              "記憶イメージ": "虫眼鏡で中を覗き込むイメージ",
              "語源ストーリー": "ラテン語spectareから...",
              "同族語tip": "spectacleの-acleは道具を意味する接尾辞"
            }}
            できるだけ多くの派生語を含めてください（最低10語）。
            """
            result, error = call_gemini(prompt)
            
            if error:
                st.error(error)
            else:
                st.subheader(f"Root: {target['text']}")
                st.info(f"**記憶イメージ:** {result['記憶イメージ']}")
                
                st.markdown("### 📦 派生語ネットワーク")
                # Group by TOEIC level
                levels = {"500": [], "730": [], "900": [], "900+": []}
                for word in result['派生語リスト']:
                    lvl = word.get('toeic_level', '500')
                    if lvl in levels:
                        levels[lvl].append(word)
                    else:
                        levels["500"].append(word)
                
                # Display TOEIC Cards
                cols = st.columns(4)
                level_labels = ["~500", "~730", "~900", "900+"]
                level_keys = ["500", "730", "900", "900+"]
                level_colors = ["#2ecc71", "#3498db", "#f1c40f", "#e74c3c"]
                
                for i, key in enumerate(level_keys):
                    with cols[i]:
                        st.markdown(f"<div style='text-align:center; padding:5px; border-radius:5px; background-color:{level_colors[i]}; color:white; font-weight:bold; margin-bottom:10px;'>{level_labels[i]}</div>", unsafe_allow_html=True)
                        for w in levels[key]:
                            st.markdown(f"""
                            <div class="stCard">
                                <div style="font-weight:bold; color:#58a6ff;">{w['word']}</div>
                                <div style="font-size:0.9em;">{w['meaning']}</div>
                                <div style="font-size:0.8em; color:#8b949e; margin-top:5px;">{w['breakdown']}</div>
                            </div>
                            """, unsafe_allow_html=True)

                with st.expander("📖 語源ストーリー"):
                    st.write(result['語源ストーリー'])
                
                st.warning(f"**同族語のコツ:** {result['同族語tip']}")

elif page == "今日の語根":
    st.title("📅 今日の語根")
    
    if 'daily_root' not in st.session_state or st.button("次の語根へ"):
        st.session_state.daily_root = random.choice(ALL_MORPHEMES)
        st.session_state.daily_explanation = None
        st.rerun()
        
    target = st.session_state.daily_root
    st.header(f"Today's Pick: {target['morpheme']}")
    render_morpheme_card(target)
    
    if not st.session_state.get('daily_explanation'):
        if st.button("深掘り解説を生成"):
            with st.spinner("AIが深掘り解説を作成中..."):
                prompt = f"""
                語根「{target['morpheme']}」（意味：{target['meaning']}、由来：{target['origin']}）について、
                この語根をマスターするための「今日の深掘り解説」を執筆してください。
                歴史、現代での使われ方、学習者へのアドバイスを含めて200〜300文字程度で返してください。
                最後に「格言風の覚え方」を1つ添えてください。
                """
                try:
                    genai.configure(api_key=api_key)
                     = genai.Generative("gemini-flash-lite-latest")
                    response = .generate_content(prompt)
                    st.session_state.daily_explanation = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"解説の生成に失敗しました: {e}")
                    
    if st.session_state.get('daily_explanation'):
        st.markdown("### 🖋️ 深掘り解説")
        st.markdown(st.session_state.daily_explanation)
