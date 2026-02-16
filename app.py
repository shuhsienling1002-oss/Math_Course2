import streamlit as st
import random
import math
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple

# ==========================================
# 1. 頁面設定與 CSS (View Layer)
# ==========================================
st.set_page_config(page_title="分數乘除連鎖反應", page_icon="🧩", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* 遊戲區塊容器 - 改為深藍色系代表深度運算 */
    .game-container {
        background: #1e293b;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        border: 2px solid #334155;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    }
    
    /* 進度條背景 */
    .progress-track {
        background: #334155;
        height: 24px;
        border-radius: 12px;
        position: relative;
        overflow: hidden;
        margin: 20px 0;
    }
    
    /* 進度條本身 - 紫色系代表乘法擴張 */
    .progress-fill {
        background: linear-gradient(90deg, #a855f7, #d8b4fe);
        height: 100%;
        transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    /* 警告色 */
    .progress-fill.warning {
        background: linear-gradient(90deg, #fca5a5, #ef4444);
    }
    
    /* 目標標記 */
    .target-marker {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 4px;
        background-color: #fbbf24;
        z-index: 10;
        box-shadow: 0 0 10px #fbbf24;
    }

    /* 卡片按鈕優化 */
    div.stButton > button {
        background-color: #38bdf8 !important; /* 天藍色 */
        color: #0f172a !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        transition: all 0.2s !important;
        font-family: 'Courier New', monospace;
    }
    div.stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4);
    }
    
    /* 除法卡片樣式 (透過 CSS class 無法直接注入 Streamlit button，但在邏輯層處理) */
    
    /* 數學推導區塊 */
    .math-steps {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #a855f7;
        margin-top: 15px;
        font-family: 'Courier New', monospace;
        color: #e2e8f0;
        line-height: 1.8;
    }
    .math-step-title {
        font-weight: bold;
        color: #fbbf24; /* Amber */
        margin-bottom: 10px;
        display: block;
        font-size: 1.1rem;
    }
    
    /* 視覺化約分 */
    .cancellation-box {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.5rem;
        flex-wrap: wrap;
        margin: 10px 0;
    }
    .fraction {
        display: inline-block;
        text-align: center;
        vertical-align: middle;
        margin: 0 5px;
    }
    .fraction > span {
        display: block;
        padding: 0 5px;
    }
    .fraction span.bottom {
        border-top: 2px solid #e2e8f0;
    }
    .crossed {
        text-decoration: line-through;
        color: #94a3b8;
        opacity: 0.6;
    }
    
    /* 狀態訊息 */
    .status-msg {
        font-size: 1.3rem;
        text-align: center;
        font-weight: bold;
        color: #38bdf8;
        margin-bottom: 15px;
        min-height: 1.5em;
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
    is_division: bool = False # 標記是否為除法卡
    id: int = field(default_factory=lambda: random.randint(10000, 99999))

    @property
    def value(self) -> Fraction:
        # 如果是除法卡，數值是倒數 (乘以倒數)
        if self.is_division:
            return Fraction(self.denominator, self.numerator)
        return Fraction(self.numerator, self.denominator)

    @property
    def is_negative(self) -> bool:
        # 判斷這個操作是否會翻轉符號
        return (self.numerator * self.denominator) < 0

    @property
    def display(self) -> str:
        # UI 顯示邏輯
        op_icon = "➗" if self.is_division else "✖️"
        
        # 處理負號顯示，讓它看起來更直觀
        n, d = self.numerator, self.denominator
        if n < 0 and d < 0: n, d = abs(n), abs(d) # 負負得正顯示
        
        # 視覺上的負號
        sign_str = "(-)" if self.is_negative else ""
        abs_n, abs_d = abs(n), abs(d)
        
        return f"{op_icon} {sign_str}{abs_n}/{abs_d}"
    
    @property
    def raw_display(self) -> str:
        op = "÷" if self.is_division else "×"
        return f"{op} {self.numerator}/{self.denominator}"

    def __repr__(self):
        return self.display

# ==========================================
# 3. 核心引擎 (Game Engine) - 乘除特化版
# ==========================================

class GameEngine:
    def __init__(self):
        # 初始化 Session State
        if 'level' not in st.session_state: self.reset_game()
    
    @property
    def level(self): return st.session_state.get('level', 1)
    @property
    def target(self): return st.session_state.get('target', Fraction(1, 1))
    @property
    def current(self): return st.session_state.get('current', Fraction(1, 1)) # 乘法起點是 1
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
        
        # 生成邏輯：確保目標不是 1 (無聊) 且分子分母不要過大
        while True:
            target, start_val, hand, correct_subset, title = self._generate_math_data(level)
            if target != 1:
                break
        
        st.session_state.target = target
        st.session_state.current = start_val # 這裡通常是 1
        st.session_state.hand = hand
        st.session_state.correct_hand_cache = correct_subset
        st.session_state.level_title = title
        
        st.session_state.game_state = 'playing'
        st.session_state.msg = f"🚀 第 {level} 關：{title}"
        st.session_state.feedback_header = "" 
        st.session_state.math_log = ""

    def _generate_math_data(self, level: int) -> Tuple[Fraction, Fraction, List[Card], List[Card], str]:
        """
        乘除法難度曲線
        """
        target_val = Fraction(1, 1)
        correct_hand = []
        allow_negative = False
        allow_division = False
        level_title = ""
        
        # 數字池 (分子/分母候選)
        nums = [2, 3, 4, 5] 
        
        if level == 1:
            nums = [2, 3]
            steps = 2
            level_title = "連鎖反應 (整數乘法)" # 簡單的約分
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

        # 1. 生產正確路徑 (Reverse Engineering)
        # 我們從 1 開始，隨機乘上幾個分數，最後的結果就是 Target
        # 這樣保證一定有解
        
        for _ in range(steps):
            n = random.choice(nums)
            d = random.choice(nums)
            
            # 避免生成 1/1
            while n == d: 
                d = random.choice(nums)
            
            # 負數邏輯
            if allow_negative and random.random() < 0.4:
                n = -n
            
            # 除法邏輯 (除以 A/B 等於 乘 B/A)
            is_div = False
            if allow_division and random.random() < 0.3:
                is_div = True
                # 如果是除法，我們記錄的是「除以 n/d」，所以實際乘數是 d/n
                # 但 Card 物件會處理這個轉換，我們這裡只要決定卡片長怎樣
            
            card = Card(n, d, is_division=is_div)
            correct_hand.append(card)
            target_val *= card.value

        target = target_val
        current = Fraction(1, 1) # 乘法起點

        # 2. 混入干擾牌
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
        st.session_state.current *= card.value # 核心運算：乘法
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
            # 乘法沒有明顯的「爆掉」，除非數值大到離譜，但這裡我們主要判斷是否還有牌
            # 提示邏輯
            if (curr > 0 and tgt < 0) or (curr < 0 and tgt > 0):
                st.session_state.msg = "⚠️ 符號不對！你需要乘上負數來翻轉符號！"
            elif abs(curr) > abs(tgt):
                st.session_state.msg = "📉 數值太大了！找個真分數 (如 1/2) 來縮小它！"
            elif abs(curr) < abs(tgt):
                st.session_state.msg = "📈 數值太小了！找個假分數 (如 3/2) 來放大它！"
            else:
                st.session_state.msg = "🤔 計算中..."

    def _trigger_end_game(self, status):
        st.session_state.game_state = 'won' if status == 'won' else 'lost'
        
        if status == 'won':
            st.session_state.msg = "🎉 連鎖反應成功！"
            st.session_state.feedback_header = "✅ 完美的約分！你找到了通往目標的路徑。"
        else:
            st.session_state.msg = "💀 實驗失敗..."
            st.session_state.feedback_header = "❌ 牌用光了，但沒有合成出目標元素。"

        st.session_state.math_log = self._generate_step_by_step_solution(st.session_state.correct_hand_cache)

    def _generate_step_by_step_solution(self, cards: List[Card]) -> str:
        """
        視覺化約分過程 (Cancellation Visualization)
        """
        if not cards: return "無解"
        
        # 1. 收集所有的分子與分母 (包含起始的 1)
        numerators = [1] 
        denominators = [1]
        
        step_html = ""
        
        # 構建運算過程 HTML
        for c in cards:
            val = c.value # 自動處理除法倒數
            n, d = val.numerator, val.denominator
            numerators.append(n)
            denominators.append(d)
            
            op_text = "÷" if c.is_division else "×"
            raw_n, raw_d = c.numerator, c.denominator
            
            step_html += f"<li>使用 <b>{c.display}</b>： 相當於乘上 <b>{n}/{d}</b></li>"

        # 2. 計算最終結果
        final_n = math.prod(numerators)
        final_d = math.prod(denominators)
        final_res = Fraction(final_n, final_d)
        
        # 3. 視覺化 HTML 構建
        # 上半部：分子列
        num_spans = ""
        for n in numerators:
            if n == 1: continue # 省略1
            num_spans += f"<span>{n}</span> × "
        num_spans = num_spans.rstrip(" × ") or "1"

        # 下半部：分母列
        den_spans = ""
        for d in denominators:
            if d == 1: continue
            den_spans += f"<span>{d}</span> × "
        den_spans = den_spans.rstrip(" × ") or "1"
        
        html = f"""
<div class="math-steps">
    <span class="math-step-title">💡 關鍵路徑解析：</span>
    <ul style="margin-bottom: 20px;">
        {step_html}
    </ul>
    
    <span class="math-step-title">🔍 約分視覺化 (Cancellation)：</span>
    <div style="background: #0f172a; padding: 15px; border-radius: 8px; text-align: center;">
        <div style="font-size: 1.2rem; margin-bottom: 10px; color: #94a3b8;">所有分子 × 所有分子 / 所有分母 × 所有分母</div>
        
        <div class="cancellation-box" style="justify-content: center;">
            <div class="fraction">
                <span class="top">{num_spans}</span>
                <span class="bottom">{den_spans}</span>
            </div>
            <div style="margin: 0 10px;">=</div>
            <div style="color: #fbbf24; font-weight: bold; font-size: 1.8rem;">
                {final_res.numerator}/{final_res.denominator}
            </div>
        </div>
        
        <div style="font-size: 0.9rem; color: #64748b; margin-top: 10px;">
            (想像一下：分子和分母相同的數字互相抵銷了！)
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

# 1. 視覺化儀表板
# 乘法很難用線性進度條表達 (因為可能變非常大或非常小)
# 我們改用「目標匹配度」視覺化
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

# 簡易進度條 (僅供參考數值大小關係)
# 邏輯：計算 Current/Target 的比例
try:
    ratio = float(engine.current / engine.target)
    # 限制在 0 - 200% 之間顯示
    if ratio < 0: progress_val = 0 # 符號相反
    else: progress_val = min(max(ratio * 50, 0), 100) # 假設目標是 50% 的位置
except:
    progress_val = 0

# 符號警告
sign_warning = ""
if (engine.current > 0 and engine.target < 0) or (engine.current < 0 and engine.target > 0):
    sign_warning = "⚠️ 符號相反！ (需要負數)"
    bar_color = "warning"
else:
    bar_color = "normal"

html_content = f"""
<div class="game-container">
    <div style="display: flex; justify-content: space-between; font-family: monospace; color: #94a3b8;">
        <span>0</span>
        <span style="color: #fbbf24;">TARGET</span>
        <span>2x Target</span>
    </div>
    <div class="progress-track">
        <div class="target-marker" style="left: 50%;"></div>
        <div class="progress-fill {bar_color}" style="width: {progress_val}%;"></div>
    </div>
    <div style="text-align: center; color: #fca5a5; font-weight: bold;">{sign_warning}</div>
</div>
"""
st.markdown(html_content, unsafe_allow_html=True)


# 2. 遊戲互動區
if engine.state == 'playing':
    st.write("### ⚗️ 選擇催化劑 (卡牌)")
    if engine.hand:
        # 自動調整列數
        cols = st.columns(len(engine.hand))
        for i, card in enumerate(engine.hand):
            with cols[i]:
                # 提示文字
                if card.is_division:
                    help_txt = f"除法：數值會變為原來的 {card.denominator}/{card.numerator} 倍"
                else:
                    help_txt = f"乘法：數值會變為原來的 {card.numerator}/{card.denominator} 倍"
                    
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

# 3. 側邊欄
with st.sidebar:
    st.markdown("### 📊 實驗室數據")
    st.write(f"Level: **{engine.level}**")
    st.caption(f"任務：{engine.level_title}")
    st.progress(min(engine.level / 10, 1.0))
    
    st.markdown("---")
    st.markdown("""
    **操作指南:**
    *   **✖️ 乘法**: 直接相乘。
    *   **➗ 除法**: 相當於乘以倒數 (翻轉)。
    *   **(-) 負號**: 會改變結果的正負號。
    *   **目標**: 讓當前數值 = 目標數值。
    """)
