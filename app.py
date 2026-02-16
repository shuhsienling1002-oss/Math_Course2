import streamlit as st
import random
import math
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ==========================================
# 1. 核心配置與 CSS (UI/UX-CRF)
# ==========================================
st.set_page_config(
    page_title="分數鍊金術",
    page_icon="⚗️",
    layout="centered"
)

st.markdown("""
<style>
    /* 全局暗色系實驗室風格 */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* 修正：增強 Caption (頂部關卡資訊) 的對比度 */
    .stCaption {
        color: #94a3b8 !important;
        font-size: 1rem !important;
        font-weight: bold !important;
    }

    /* 修正：自定義訊息欄 (取代 st.info 的預設樣式) */
    .custom-info-box {
        background-color: rgba(56, 189, 248, 0.1); /* 淡藍背景 */
        border: 1px solid #38bdf8; /* 亮藍邊框 */
        color: #e0f2fe; /* 極亮白藍文字 */
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
    }

    /* 頂部狀態欄 */
    .status-bar {
        background: #1e293b;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* 卡牌按鈕優化 */
    div.stButton > button {
        background: linear-gradient(145deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        font-size: 1.2rem !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 0 #1d4ed8 !important; /* 3D 按壓感 */
    }
    div.stButton > button:active {
        transform: translateY(4px) !important;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        filter: brightness(1.1);
    }
    
    /* 除法卡牌特殊色 */
    .division-card > button {
        background: linear-gradient(145deg, #ec4899, #db2777) !important;
        box-shadow: 0 4px 0 #be185d !important;
    }

    /* 勝利結算區 */
    .victory-modal {
        background: rgba(16, 185, 129, 0.1);
        border: 2px solid #10b981;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 領域模型 (Domain Model)
# ==========================================

@dataclass
class MathCard:
    numerator: int
    denominator: int
    is_division: bool = False
    id: str = field(default_factory=lambda: f"{random.randint(1000,9999)}")

    @property
    def raw_value(self) -> Fraction:
        """卡牌面值的原始分數"""
        return Fraction(self.numerator, self.denominator)

    @property
    def effect_value(self) -> Fraction:
        """卡牌產生的實際乘數效果 (除法會翻轉)"""
        if self.is_division:
            return Fraction(self.denominator, self.numerator)
        return Fraction(self.numerator, self.denominator)

    def to_latex(self) -> str:
        """生成 LaTeX 顯示字串"""
        n, d = self.numerator, self.denominator
        # 處理負號顯示
        sign = "-" if (n * d < 0) else ""
        n, d = abs(n), abs(d)
        
        # 使用雙反斜線 \\frac 避免 Python 轉義錯誤
        frac_str = f"\\frac{{{n}}}{{{d}}}"
        
        if self.is_division:
            return f"\\div {sign}{frac_str}"
        else:
            return f"\\times {sign}{frac_str}"

# ==========================================
# 3. 遊戲邏輯核心 (Logic Layer)
# ==========================================

class AlchemyEngine:
    """負責數學計算與關卡生成，不涉及任何 UI"""
    
    @staticmethod
    def generate_level(level: int) -> dict:
        """生成關卡數據"""
        # 難度曲線配置
        config = {
            1: {'nums': [2, 3], 'steps': 2, 'neg': False, 'div': False, 'title': "基礎合成 (整數)"},
            2: {'nums': [2, 3, 4], 'steps': 2, 'neg': False, 'div': False, 'title': "等價交換 (約分)"},
            3: {'nums': [2, 3, 4, 5], 'steps': 3, 'neg': True, 'div': False, 'title': "極性反轉 (負數)"},
            4: {'nums': [2, 3, 5, 7], 'steps': 3, 'neg': True, 'div': True, 'title': "逆向煉成 (除法)"},
            5: {'nums': [2, 3, 4, 5, 6, 8, 9], 'steps': 4, 'neg': True, 'div': True, 'title': "賢者之石 (高階)"}
        }
        cfg = config.get(level, config[5])
        
        # 1. 生成目標路徑 (保證有解 - 逆向工程法)
        target_val = Fraction(1, 1)
        correct_cards = []
        
        for _ in range(cfg['steps']):
            n = random.choice(cfg['nums'])
            d = random.choice(cfg['nums'])
            while n == d: d = random.choice(cfg['nums']) # 避免生成 1
            
            if cfg['neg'] and random.random() < 0.4: n = -n
            is_div = cfg['div'] and random.random() < 0.3
            
            card = MathCard(n, d, is_division=is_div)
            correct_cards.append(card)
            target_val *= card.effect_value

        # 2. 生成干擾項
        distractors = []
        for _ in range(2):
            n = random.choice(cfg['nums'])
            d = random.choice(cfg['nums'])
            if cfg['neg'] and random.random() < 0.4: n = -n
            is_div = cfg['div'] and random.random() < 0.3
            distractors.append(MathCard(n, d, is_division=is_div))

        # 3. 混合手牌
        hand = correct_cards + distractors
        random.shuffle(hand)
        
        return {
            "target": target_val,
            "hand": hand,
            "title": cfg['title'],
            "optimal_path": correct_cards # 用於提示或結算
        }

    @staticmethod
    def calculate_current(history: List[MathCard]) -> Fraction:
        val = Fraction(1, 1)
        for card in history:
            val *= card.effect_value
        return val

    @staticmethod
    def generate_equation_latex(history: List[MathCard]) -> str:
        if not history:
            return "1"
        latex = "1"
        for card in history:
            latex += f" {card.to_latex()}"
        return latex

# ==========================================
# 4. 狀態管理 (State Management)
# ==========================================

class GameState:
    def __init__(self):
        if 'level' not in st.session_state:
            st.session_state.update({
                'level': 1,
                'target': Fraction(1, 1),
                'hand': [],
                'history': [], # 已打出的卡牌
                'game_status': 'playing', # playing, won, lost
                'msg': '準備開始煉成...'
            })
            self.start_level(1)

    def start_level(self, level):
        st.session_state.level = level
        data = AlchemyEngine.generate_level(level)
        st.session_state.target = data['target']
        st.session_state.hand = data['hand']
        st.session_state.level_title = data['title']
        st.session_state.history = []
        st.session_state.game_status = 'playing'
        st.session_state.msg = f"第 {level} 關：{data['title']}"

    def play_card(self, card_idx):
        hand = st.session_state.hand
        if 0 <= card_idx < len(hand):
            card = hand.pop(card_idx)
            st.session_state.history.append(card)
            self._check_status()

    def undo(self):
        if st.session_state.history:
            card = st.session_state.history.pop()
            st.session_state.hand.append(card)
            st.session_state.game_status = 'playing'
            st.session_state.msg = "時光回溯成功"

    def _check_status(self):
        current = AlchemyEngine.calculate_current(st.session_state.history)
        target = st.session_state.target
        
        if current == target:
            st.session_state.game_status = 'won'
            st.session_state.msg = "煉成成功！元素穩定！"
        elif not st.session_state.hand:
            st.session_state.game_status = 'lost'
            st.session_state.msg = "素材耗盡，煉成失敗..."
        else:
            # 提供 Scaffolding (鷹架) 提示
            if (current > 0 > target) or (current < 0 < target):
                st.session_state.msg = "⚠️ 警告：符號(正負)相反！"
            elif abs(current) > abs(target):
                st.session_state.msg = "📉 提示：數值過大，需要變小"
            elif abs(current) < abs(target):
                st.session_state.msg = "📈 提示：數值過小，需要變大"
            else:
                st.session_state.msg = "⚗️ 反應進行中..."

    def next_level(self):
        self.start_level(st.session_state.level + 1)

    def retry(self):
        self.start_level(st.session_state.level)

# ==========================================
# 5. UI 呈現層 (View Layer)
# ==========================================

def main():
    game = GameState()
    
    # --- Header Area ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("⚗️ 分數鍊金術")
    with col2:
        st.caption(f"當前關卡: {st.session_state.level}")
        if st.button("🔄 重置"):
            game.retry()
            st.rerun()

    # --- Target vs Current Dashboard ---
    target = st.session_state.target
    current = AlchemyEngine.calculate_current(st.session_state.history)
    
    # 使用 LaTeX 顯示目標與當前值
    # 【修正】標題全中文，字體放大
    c1, c2, c3 = st.columns([1, 0.2, 1])
    with c1:
        st.markdown(f"### 🎯 目標數值\n$$\\Huge \\frac{{{target.numerator}}}{{{target.denominator}}}$$")
    with c2:
        # 狀態指示圖標
        icon = "⚖️"
        if current == target: icon = "✅"
        elif st.session_state.game_status == 'lost': icon = "❌"
        st.markdown(f"<div style='font-size:3rem; text-align:center; padding-top:20px'>{icon}</div>", unsafe_allow_html=True)
    with c3:
        color = "#4ade80" if current == target else "#facc15"
        # 【修正】標題全中文，字體放大
        st.markdown(f"### 🧪 當前數值\n$$\\Huge \\color{{{color}}}{{\\frac{{{current.numerator}}}{{{current.denominator}}}}}$$")

    # --- 狀態訊息 ---
    st.markdown(f'<div class="custom-info-box">{st.session_state.msg}</div>', unsafe_allow_html=True)

    # --- 算式鏈 (Equation Chain) ---
    st.markdown("**📜 煉成公式：**")
    latex_eq = AlchemyEngine.generate_equation_latex(st.session_state.history)
    st.latex(f"{latex_eq} = \\frac{{{current.numerator}}}{{{current.denominator}}}")

    # --- 遊戲區 (Play Area) ---
    if st.session_state.game_status == 'playing':
        st.markdown("---")
        st.write("👇 點擊卡牌加入反應爐：")
        
        # 手牌區
        hand = st.session_state.hand
        if hand:
            cols = st.columns(4)
            for i, card in enumerate(hand):
                col_idx = i % 4
                with cols[col_idx]:
                    # 視覺區分除法與乘法
                    btn_label = f"➗ {card.numerator}/{card.denominator}" if card.is_division else f"✖️ {card.numerator}/{card.denominator}"
                    if card.raw_value < 0: btn_label += " (-)"
                    
                    if st.button(btn_label, key=f"card_{card.id}"):
                        game.play_card(i)
                        st.rerun()
        
        # 功能區
        st.markdown("---")
        if st.session_state.history:
            if st.button("↩️ 復原上一步", type="secondary"):
                game.undo()
                st.rerun()

    # --- 結算區 (Result Area) ---
    elif st.session_state.game_status == 'won':
        st.markdown("""
        <div class="victory-modal">
            <h2>🎉 煉成成功！</h2>
            <p>你完美平衡了分子與分母。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 詳細的約分過程展示
        with st.expander("🔍 查看反應原理 (逐步解析)", expanded=True):
            st.write("你的計算路徑：")
            st.latex(latex_eq)
            st.write("這證明了：")
            # 使用 underbrace (下括號) 與標準等號
            st.latex(f"\\underbrace{{\\frac{{{current.numerator}}}{{{current.denominator}}}}}_{{\\text{{當前數值}}}} = \\underbrace{{\\frac{{{target.numerator}}}{{{target.denominator}}}}}_{{\\text{{目標數值}}}}")

        if st.button("🚀 前往下一關", type="primary", use_container_width=True):
            game.next_level()
            st.rerun()

    elif st.session_state.game_status == 'lost':
        st.error("💥 實驗失敗：無法合成目標元素。")
        if st.button("🔄 重新實驗", type="primary", use_container_width=True):
            game.retry()
            st.rerun()

if __name__ == "__main__":
    main()
