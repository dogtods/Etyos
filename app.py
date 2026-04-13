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
    ["語源辞典", "単語分解", "クイズ", "語根ワールド", "今日の語根", "文章から学ぶ"],
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
        model = genai.GenerativeModel("gemini-flash-lite-latest")
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
                st.subheader(f"Root: {target['morpheme']}")
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
                    model = genai.GenerativeModel("gemini-flash-lite-latest")
                    response = model.generate_content(prompt)
                    st.session_state.daily_explanation = response.text
                    st.rerun()
                except Exception as e:
                    st.error(f"解説の生成に失敗しました: {e}")
                    
    if st.session_state.get('daily_explanation'):
        st.markdown("### 🖋️ 深掘り解説")
        st.markdown(st.session_state.daily_explanation)

elif page == "文章から学ぶ":
    st.title("📖 文章から学ぶ")
    st.markdown("文章を入力してください。日本語の場合は自動的に英訳してから語源を解析します。")

    # キャッシュの初期化
    if "text_cache" not in st.session_state:
        st.session_state["text_cache"] = {}
    if "analysis_stats" not in st.session_state:
        st.session_state["analysis_stats"] = {"local": 0, "api": 0, "cache": 0, "api_calls": 0}
    if "translated_text" not in st.session_state:
        st.session_state["translated_text"] = None
    if "analysis_digest" not in st.session_state:
        st.session_state["analysis_digest"] = None

    col_main, col_side = st.columns([7, 3])

    with col_main:
        input_text = st.text_area("文章を入力してください", height=200, placeholder="Example: The transportation system is essential for international commerce.\nまたは日本語：輸送システムは国際貿易に不可欠です。", key="study_text_input")
        
        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            analyze_btn = st.button("🔍 解析する", type="primary")
        with btn_col2:
            if st.button("🗑️ キャッシュクリア"):
                st.session_state["text_cache"] = {}
                st.session_state["analysis_stats"] = {"local": 0, "api": 0, "cache": 0, "api_calls": 0}
                st.session_state["translated_text"] = None
                st.session_state["analysis_digest"] = None
                st.rerun()

        if input_text:
            import re
            
            # 日本語判定関数
            def has_japanese(text):
                return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))

            if analyze_btn:
                # 日本語が含まれる場合は翻訳を実行
                if has_japanese(input_text):
                    with st.spinner("日本語を英語に翻訳中..."):
                        trans_prompt = f"""
                        以下の日本語を自然な英語に翻訳してください。
                        JSON形式で返してください（マークダウン不要）：
                        {{
                          "translated_text": "Translated English text"
                        }}
                        
                        日本語：{input_text}
                        """
                        res, err = call_gemini(trans_prompt)
                        st.session_state["analysis_stats"]["api_calls"] += 1
                        if not err and res:
                            st.session_state["translated_text"] = res.get("translated_text", "")
                        else:
                            st.error(f"翻訳に失敗しました: {err}")
                else:
                    st.session_state["translated_text"] = None

            # 解析対象のテキストを決定
            target_text = st.session_state["translated_text"] if st.session_state["translated_text"] else input_text
            
            if analyze_btn:
                # 解析処理
                words = re.findall(r'\b\w+\b', target_text)
                unique_words = list(set([w.lower() for w in words]))
                
                unknown_words_to_api = []
                
                for word in unique_words:
                    if word in st.session_state["text_cache"]:
                        st.session_state["analysis_stats"]["cache"] += 1
                        continue
                    
                    found = False
                    # Step 1: Local matching
                    for m in ALL_MORPHEMES:
                        patterns = [p.strip().replace('-', '') for p in m['morpheme'].split('/')]
                        if word in [ex.lower() for ex in m['examples']] or any(p in word for p in patterns):
                            st.session_state["text_cache"][word] = {
                                "morpheme": m['morpheme'],
                                "meaning": m['meaning'],
                                "type": m['type']
                            }
                            st.session_state["analysis_stats"]["local"] += 1
                            found = True
                            break
                    
                    if not found:
                        if len(word) >= 4:
                            unknown_words_to_api.append(word)
                        else:
                            st.session_state["text_cache"][word] = None

                # Step 2: API Call (Etymology Analysis + Digest)
                with st.spinner("AIが語源の繋がりを解析中..."):
                    unknown_list_str = ", ".join(unknown_words_to_api) if unknown_words_to_api else "なし"
                    prompt = f"""
                    以下の英文に含まれる語源を分析し、学習者が単語の成り立ちを理解しやすくなる「語源ダイジェスト」を作成してください。
                    また、未知の単語リストについても分析してください。

                    英文：{target_text}
                    未知の単語リスト：{unknown_list_str}

                    以下のJSON形式のみで返してください：
                    {{
                      "analyzed": [
                        {{
                          "word": "example",
                          "root": "empl",
                          "root_meaning": "取る",
                          "role": "root"
                        }}
                      ],
                      "digest": "この文章で中心となる語根は『〇〇』です。これは『〜』という意味があり、単語△△（意味）は『✕✕』という風に成り立っています。"
                    }}
                    """
                    result, error = call_gemini(prompt)
                    st.session_state["analysis_stats"]["api_calls"] += 1
                    
                    if not error and result:
                        if "analyzed" in result:
                            for item in result["analyzed"]:
                                w_key = item["word"].lower()
                                st.session_state["text_cache"][w_key] = {
                                    "morpheme": item["root"],
                                    "meaning": item["root_meaning"],
                                    "type": item["role"]
                                }
                                st.session_state["analysis_stats"]["api"] += 1
                        st.session_state["analysis_digest"] = result.get("digest", "")
                    
                    # Cache the rest as None to avoid repeated calls
                    for w in unknown_words_to_api:
                        if w not in st.session_state["text_cache"]:
                            st.session_state["text_cache"][w] = None

            # 解析結果の表示 (target_textを使用)
            if st.session_state["translated_text"]:
                st.info(f"🤖 **AI翻訳結果:** {st.session_state['translated_text']}")

            # ハイライト表示の生成
            display_html = ""
            tokens = re.findall(r'\w+|[^\w\s]|\s+', target_text)
            
            for token in tokens:
                w_lower = token.lower()
                if w_lower in st.session_state["text_cache"] and st.session_state["text_cache"][w_lower]:
                    res = st.session_state["text_cache"][w_lower]
                    m_type = res["type"]
                    
                    if m_type == "prefix":
                        bg, border = "rgba(52,152,219,0.25)", "#3498db"
                    elif m_type == "root":
                        bg, border = "rgba(241,196,15,0.25)", "#f1c40f"
                    elif m_type == "suffix":
                        bg, border = "rgba(46,204,113,0.25)", "#2ecc71"
                    else:
                        bg, border = "transparent", "none"
                        
                    display_html += f'<span style="background-color: {bg}; border-bottom: 2px solid {border}; padding: 1px 3px; border-radius: 3px;">{token}<sub style="color:#8b949e; font-size:0.7em; margin-left: 2px;">{res["morpheme"]}</sub></span>'
                else:
                    display_html += token
            
            st.markdown(f'<div style="line-height: 2.2; font-size: 1.15em; background-color: #1e2227; padding: 25px; border-radius: 12px; border: 1px solid #30363d; color: #e0e0e0; min-height: 100px;">{display_html}</div>', unsafe_allow_html=True)

            if st.session_state["analysis_digest"]:
                st.markdown(f"""
                <div style="background-color: rgba(88, 166, 255, 0.1); border-left: 5px solid #58a6ff; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <h4 style="margin-top: 0; color: #58a6ff;">💡 AI語源ダイジェスト</h4>
                    <p style="font-size: 0.95em; color: #e0e0e0; line-height: 1.6;">{st.session_state['analysis_digest']}</p>
                </div>
                """, unsafe_allow_html=True)

    with col_side:
        st.subheader("📊 語根ランキング")
        
        # 決定された表示対象テキスト
        display_target = st.session_state["translated_text"] if st.session_state["translated_text"] else input_text
        
        if display_target and "text_cache" in st.session_state:
            words_in_text = re.findall(r'\b\w+\b', display_target)
            matches_in_text = []
            for w in words_in_text:
                w_l = w.lower()
                if w_l in st.session_state["text_cache"] and st.session_state["text_cache"][w_l]:
                    matches_in_text.append((w, st.session_state["text_cache"][w_l]))
            
            if matches_in_text:
                morpheme_counts = {}
                for word, m_info in matches_in_text:
                    m_key = f"{m_info['morpheme']}|{m_info['type']}"
                    if m_key not in morpheme_counts:
                        morpheme_counts[m_key] = {"info": m_info, "words": set(), "count": 0}
                    morpheme_counts[m_key]["words"].add(word)
                    morpheme_counts[m_key]["count"] += 1
                
                sorted_ranks = sorted(morpheme_counts.items(), key=lambda x: x[1]["count"], reverse=True)
                max_count = sorted_ranks[0][1]["count"] if sorted_ranks else 1
                
                for m_id, data in sorted_ranks:
                    info = data["info"]
                    m_type = info["type"]
                    color = "#3498db" if m_type == "prefix" else "#f1c40f" if m_type == "root" else "#2ecc71"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="margin-top: 15px;">
                            <span style="color: {color}; font-weight: bold; font-size: 1.1em;">{info['morpheme']}</span> 
                            <span style="font-size: 0.8em; color: #8b949e; margin-left: 5px;">({info['meaning']})</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.progress(data["count"] / max_count)
                        st.markdown(f"<p style='font-size: 0.85em; color: #8b949e; margin-top: -10px;'>検出語: {', '.join(list(data['words']))}</p>", unsafe_allow_html=True)
            else:
                st.info("文章を解析して語源を見つけましょう。")
        
        st.markdown("---")
        st.subheader("⚙️ API使用状況")
        stats = st.session_state.get("analysis_stats", {"local": 0, "api": 0, "cache": 0, "api_calls": 0})
        st.caption(f"ローカル照合: {stats['local']} 語")
        st.caption(f"API解析: {stats['api']} 語")
        st.caption(f"キャッシュ使用: {stats['cache']} 語")
        st.caption(f"今回のAPIコール: {stats['api_calls']} 回")
