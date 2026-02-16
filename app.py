import streamlit as st
import random
import math
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple

# ==========================================
# 1. 頁面設定與 CSS (View Layer) - 絕對黑字版
# ==========================================
st.set_page_config(page_title="分數乘除連鎖反應", page_icon="🧩", layout="centered")

st.markdown("""
<style>
    /* 1. 全局強制深色背景 */
    .stApp { 
        background-color: #020617; 
        color: #f8fafc; 
    }
    
    /* 2. Metric 數值與標籤 */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: 700 !important;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
    }
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }

    /* 3. Metric Delta (差值小字) */
    [data-testid="stMetricDelta"] {
        background-color: rgba(51, 65, 85, 0.8) !important;
        border: 1px solid #475569 !important;
        padding: 4px 8px !important;
        border-radius: 6px !important;
        width: fit-content !important;
        margin-top: 5px !important;
    }
    [data-testid="stMetricDelta"] svg { fill: #facc15 !important; }
    [data-testid="stMetricDelta"] > div { color: #f8fafc !important; font-weight: bold !important; }

    /* =========================================================
       4. 【核彈級修復】按鈕文字強制全黑
       ========================================================= */
    
    /* 第一層：鎖定按鈕本體 */
    div.stButton > button {
        background-color: #facc15 !important; /* 亮黃底 */
        border: 2px solid #fbbf24 !important;
        color: #000000 !important; /* 設定第一層文字為黑 */
    }

    /* 第二層：鎖定按鈕內的所有子元素 (p, div, span) */
    div.stButton > button * {
        color: #000000 !important;
        fill: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* 強制 Webkit 內核填充黑色 */
        font-weight: 900 !important; /* 特粗體 */
        font-size: 24px !important;
        font-family: 'Courier New', monospace !important;
    }

    /* 滑鼠懸停狀態：依然全黑 */
    div.stButton > button:hover {
        background-color: #fde047 !important;
        border-color: #ffffff !important;
    }
    div.stButton > button:hover * {
        color: #000000 !important;
    }
    
    /* 點擊狀態：依然全黑 */
    div.stButton > button:active * {
        color: #000000 !important;
    }

    /* ========================================================= */

    /* 遊戲區塊容器 */
    .game-container {
        background: #1e293b;
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 20px;
        border: 2px solid #475569;
        box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }
    
    /* 進度條 */
    .progress-track {
        background: #334155;
        height: 28px;
        border-radius: 14px;
        position: relative;
        overflow: hidden;
        margin: 25px 0;
        border: 1px solid #64748b;
    }
    .progress-fill {
        background: linear-gradient(90deg, #c084fc, #e879f9);
        height: 100%;
        transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.5);
    }
    .progress-fill.warning {
        background: linear-gradient(90deg, #fca5a5, #ef4444);
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
    }
    .target-marker {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 6px;
        background-color: #facc15;
        z-index: 10;
        box-shadow: 0 0 10px #facc15;
    }
    
    /* 數學推導區塊 */
    .math-steps {
        background-color: #0f172a;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        border-left: 6px solid #22d3ee;
        margin-top: 20px;
        font-family: 'Courier New', monospace;
        color: #f1f5f9;
        line-height: 1.8;
        font-size: 1.1rem;
    }
    .math-step-title {
        font-weight: bold;
        color: #22d3ee;
        margin-bottom: 15px;
        display: block;
        font-size: 1.2rem;
    }
    
    /* 視覺化約分 */
    .cancellation-wrapper {
        background: #020617; 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center;
        border: 1px solid #1e293b;
    }
    .cancellation-box {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        font-size: 1.8rem;
        flex-wrap: wrap;
        margin: 15px 0;
        font-weight: bold;
    }
    .fraction {
        display: inline-block;
        text-align: center;
        vertical-align: middle;
        margin: 0 8px;
    }
    .fraction > span {
        display: block;
        padding: 2px 8px;
        color: #ffffff; 
    }
    .fraction span.bottom {
        border-top: 3px solid #ffffff; 
        margin-top: 2px;
    }
    .equals-sign { color: #94a3b8; font-size: 2rem; }
    .final-result { color: #4ade80; font-weight: 900; font-size: 2.2rem; }
    
    /* 狀態訊息 */
    .status-msg {
        font-size: 1.4rem;
        text-align: center;
        font-weight: bold;
        color: #38bdf8;
        margin-bottom: 15px;
        background: rgba(56, 189, 248, 0.1);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .label-text {
        color: #cbd5e1;
        font-weight: bold;
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 數據模型 (Data Model)
# ==========================================

@dataclass
class Card:
    numerator: int
    denominator: int
    is_division: bool = False 
    id: int = field(default_factory=lambda: random.randint(10000, 99999))

    @property
    def value(self) -> Fraction:
        if self.is_division:
            return Fraction(self.denominator, self.numerator)
        return Fraction(self.numerator, self.denominator)

    @property
    def is_negative(self) -> bool:
        return (self.numerator * self.denominator) < 0

    @property
    def display(self) -> str:
        op_icon = "➗" if self.is_division else "✖️"
        n, d = self.numerator, self.denominator
        if n < 0 and d < 0: n, d = abs(n), abs(d)
        
        sign_str = "(-)" if self.is_negative else ""
        abs_n, abs_d = abs(n), abs(d)
        
        return f"{op_icon} {sign_str}{abs_n}/{abs_d}"
    
    def __repr__(self):
        return self.display

# ==========================================
# 3. 核心引擎 (Game Engine)
# ==========================================

class GameEngine:
    def __init__(self):
        if 'level' not in st.session_state: self.reset_game()
    
    @property
    def level(self): return st.session_state.get('level', 1)
    @property
    def target(self): return st.session_state.get('target', Fraction(1, 1))
    @property
    def current(self): return st.session_state.get('current', Fraction(1, 1)) 
    @property
    def hand(self): return st.session_state.get('hand', [])
    @property
    def message(self): return st.session_state.get('msg', "系統載入中...")
    @property
    def state(self): return st.session_state.get('game_state', 'playing')
    @property
    def feedback_header(self): return st.session_state.get('feedback_header', "")
    @property
    def math_log(self): return st.session_state.get('math_log', "")
    @property
    def level_title(self): return st.session_state.get('level_title', "")

    def reset_game(self):
        st.session_state.level = 1
        self.start_level(1)

    def start_level(self, level: int):
        st.session_state.level = level
        while True:
            target, start_val, hand, correct_subset, title = self._generate_math_data(level)
            if target != 1:
                break
        
        st.session_state.target = target
        st.session_state.current = start_val
        st.session_state.hand = hand
        st.session_state.correct_hand_cache = correct_subset
        st.session_state.level_title = title
        st.session_state.game_state = 'playing'
        st.session_state.msg = f"🚀 第 {level} 關：{title}"
        st.session_state.feedback_header = "" 
        st.session_state.math_log = ""

    def _generate_math_data(self, level: int) -> Tuple[Fraction, Fraction, List[Card], List[Card], str]:
        target_val = Fraction(1, 1)
        correct_hand = []
        allow_negative = False
        allow_division = False
        level_title = ""
        nums = [2, 3, 4, 5] 
        
        if level == 1:
            nums = [2, 3]
            steps = 2
            level_title = "連鎖反應 (整數乘法)"
        elif level == 2:
            nums = [2, 3, 4]
            steps = 2
            level_title = "基礎約分 (消消樂)"
        elif level == 3:
            nums = [2, 3, 4, 5, 6]
            steps = 3
            level_title = "進階約分 (尋找因數)"
        elif level == 4:
            nums = [2, 3, 4, 5]
            steps = 3
            allow_negative = True
            level_title = "符號翻轉 (負數乘法)"
        elif level == 5:
            nums = [2, 3, 4, 5, 6, 8]
            steps = 3
            allow_negative = True
            allow_division = True
            level_title = "逆向操作 (除法登場)"
        else:
            nums = [2, 3, 4, 5, 6, 7, 8, 9]
            steps = 4
            allow_negative = True
            allow_division = True
            level_title = "極限連乘 (大師級)"

        for _ in range(steps):
            n = random.choice(nums)
            d = random.choice(nums)
            while n == d: d = random.choice(nums)
            if allow_negative and random.random() < 0.4: n = -n
            is_div = False
            if allow_division and random.random() < 0.3: is_div = True
            
            card = Card(n, d, is_division=is_div)
            correct_hand.append(card)
            target_val *= card.value

        target = target_val
        current = Fraction(1, 1)
        distractor_count = random.randint(2, 3)
        distractors = []
        for _ in range(distractor_count):
            n = random.choice(nums)
            d = random.choice(nums)
            if allow_negative and random.random() < 0.4: n = -n
            is_div = allow_division and random.random() < 0.3
            distractors.append(Card(n, d, is_division=is_div))
            
        final_hand = correct_hand + distractors
        random.shuffle(final_hand)
        return target, current, final_hand, correct_hand, level_title

    def play_card(self, card_idx: int):
        if self.state != 'playing': return
        if not st.session_state.get('hand') or card_idx >= len(st.session_state.hand): return
        card = st.session_state.hand.pop(card_idx)
        st.session_state.current *= card.value
        self._check_win_condition()

    def _check_win_condition(self):
        curr = st.session_state.current
        tgt = st.session_state.target
        hand = st.session_state.hand
        
        if curr == tgt:
            self._trigger_end_game('won')
        elif len(hand) == 0:
            self._trigger_end_game('lost_empty')
        else:
            if (curr > 0 and tgt < 0) or (curr < 0 and tgt > 0):
                st.session_state.msg = "⚠️ 符號不對！你需要負數牌！"
            elif abs(curr) > abs(tgt):
                st.session_state.msg = "📉 數值太大！找個分數縮小它！"
            elif abs(curr) < abs(tgt):
                st.session_state.msg = "📈 數值太小！找個分數放大它！"
            else:
                st.session_state.msg = "🤔 計算中..."

    def _trigger_end_game(self, status):
        st.session_state.game_state = 'won' if status == 'won' else 'lost'
        if status == 'won':
            st.session_state.msg = "🎉 實驗成功！"
            st.session_state.feedback_header = "✅ 完美的約分！"
        else:
            st.session_state.msg = "💀 實驗失敗..."
            st.session_state.feedback_header = "❌ 沒有合成出目標元素。"
        st.session_state.math_log = self._generate_step_by_step_solution(st.session_state.correct_hand_cache)

    def _generate_step_by_step_solution(self, cards: List[Card]) -> str:
        if not cards: return "無解"
        
        numerators = [1] 
        denominators = [1]
        step_html = ""
        
        for c in cards:
            val = c.value
            n, d = val.numerator, val.denominator
            numerators.append(n)
            denominators.append(d)
            step_html += f"<li>使用 <b>{c.display}</b>： 乘上 <span style='color:#facc15'>{n}/{d}</span></li>"

        final_n = math.prod(numerators)
        final_d = math.prod(denominators)
        final_res = Fraction(final_n, final_d)
        
        num_spans = ""
        for n in numerators:
            if n == 1: continue 
            num_spans += f"<span>{n}</span> × "
        num_spans = num_spans.rstrip(" × ") or "1"

        den_spans = ""
        for d in denominators:
            if d == 1: continue
            den_spans += f"<span>{d}</span> × "
        den_spans = den_spans.rstrip(" × ") or "1"
        
        html = f"""
<div class="math-steps">
    <span class="math-step-title">💡 關鍵路徑解析：</span>
    <ul style="margin-bottom: 20px; color: #cbd5e1;">
        {step_html}
    </ul>
    
    <span class="math-step-title">🔍 約分視覺化 (Cancellation)：</span>
    <div class="cancellation-wrapper">
        <div style="font-size: 1rem; margin-bottom: 10px; color: #94a3b8;">分子乘分子 / 分母乘分母</div>
        
        <div class="cancellation-box">
            <div class="fraction">
                <span class="top">{num_spans}</span>
                <span class="bottom">{den_spans}</span>
            </div>
            <div class="equals-sign">=</div>
            <div class="final-result">
                {final_res.numerator}/{final_res.denominator}
            </div>
        </div>
        
        <div style="font-size: 0.9rem; color: #64748b; margin-top: 10px;">
            (提示：上下的相同數字可以互相抵銷！)
        </div>
    </div>
</div>
"""
        return html

    def next_level(self):
        self.start_level(self.level + 1)

    def retry_level(self):
        self.start_level(self.level)

# ==========================================
# 4. UI 渲染層 (View Layer)
# ==========================================

engine = GameEngine()

st.title(f"🧬 分數乘除連鎖反應")
st.markdown(f"<div class='status-msg'>{engine.message}</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric(label="🏁 目標數值 (Target)", value=str(engine.target))
with col2:
    delta_color = "normal"
    if engine.current == engine.target: delta_color = "normal"
    elif engine.current == 1: delta_color = "off"
    else: delta_color = "inverse"
    
    st.metric(
        label="🧪 當前混合物 (Current)", 
        value=str(engine.current), 
        delta=f"距離目標: {engine.target - engine.current}",
        delta_color=delta_color
    )

try:
    ratio = float(engine.current / engine.target)
    if ratio < 0: progress_val = 0 
    else: progress_val = min(max(ratio * 50, 0), 100) 
except:
    progress_val = 0

sign_warning = ""
bar_color = "normal"
if (engine.current > 0 and engine.target < 0) or (engine.current < 0 and engine.target > 0):
    sign_warning = "⚠️ 符號相反！ (需要負數)"
    bar_color = "warning"

html_content = f"""
<div class="game-container">
    <div style="display: flex; justify-content: space-between; font-family: monospace;" class="label-text">
        <span>0</span>
        <span style="color: #facc15;">TARGET</span>
        <span>2x Target</span>
    </div>
    <div class="progress-track">
        <div class="target-marker" style="left: 50%;"></div>
        <div class="progress-fill {bar_color}" style="width: {progress_val}%;"></div>
    </div>
    <div style="text-align: center; color: #fca5a5; font-weight: bold; font-size: 1.2rem;">{sign_warning}</div>
</div>
"""
st.markdown(html_content, unsafe_allow_html=True)

if engine.state == 'playing':
    st.write("### ⚗️ 選擇催化劑 (卡牌)")
    if engine.hand:
        cols = st.columns(len(engine.hand))
        for i, card in enumerate(engine.hand):
            with cols[i]:
                help_txt = f"除法：變為原來的 {card.denominator}/{card.numerator} 倍" if card.is_division else f"乘法：變為原來的 {card.numerator}/{card.denominator} 倍"
                if st.button(f"{card.display}", key=f"btn_{card.id}", help=help_txt):
                    engine.play_card(i)
                    st.rerun()
    else:
        st.info("手牌已空，正在結算...")

else:
    st.markdown("---")
    if engine.state == 'won':
        st.success(engine.feedback_header)
    else:
        st.error(engine.feedback_header)
    
    st.markdown(engine.math_log, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if engine.state == 'won':
            if st.button("🚀 下一關 (Next Level)", type="primary", use_container_width=True):
                engine.next_level()
                st.rerun()
        else:
            if st.button("🔄 重置實驗 (Retry)", type="secondary", use_container_width=True):
                engine.retry_level()
                st.rerun()

with st.sidebar:
    st.markdown("### 📊 實驗室數據")
    st.write(f"Level: **{engine.level}**")
    st.caption(f"任務：{engine.level_title}")
    st.progress(min(engine.level / 10, 1.0))
    st.markdown("---")
    st.markdown("""
    **操作指南:**
    *   **✖️ 乘法**: 直接相乘。
    *   **➗ 除法**: 乘以倒數。
    *   **(-) 負號**: 改變正負。
    """)
