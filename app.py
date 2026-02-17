import streamlit as st
import random
import time
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import math

# ==========================================
# 0. 全局設定與 CSS (Global Config)
# ==========================================
st.set_page_config(
    page_title="零熵鍊金術: Zero-Entropy Alchemy",
    page_icon="⚗️",
    layout="wide"
)

# 引入自定義 CSS (基於 10-3.APP介面.txt 的極簡與對比度要求)
st.markdown("""
<style>
    /* 全局深色系 - 專注模式 */
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    
    /* 反應爐容器 - 物理隱喻：高壓容器 */
    .reactor-container {
        background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
        border: 2px solid #334155;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 30px rgba(56, 189, 248, 0.1);
        margin-bottom: 20px;
        transition: border-color 0.3s;
    }
    
    /* 熵值警告狀態 */
    .reactor-critical {
        border-color: #ef4444 !important;
        box-shadow: 0 0 30px rgba(239, 68, 68, 0.3) !important;
    }

    /* 卡牌按鈕 - 觸感設計 */
    div.stButton > button {
        background: linear-gradient(145deg, #334155, #1e293b) !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
        border-radius: 12px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.2rem !important;
        height: 80px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
    }
    
    /* 進度條優化 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #38bdf8, #818cf8);
    }
    
    /* 狀態文字 */
    .status-text {
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. 領域模型 (Domain Model - 16 Models Applied)
# ==========================================

@dataclass
class ElementCard:
    numerator: int
    denominator: int
    type: str = "matter"  # matter (乘法素材), antimatter (除法/稀釋素材)
    id: str = field(default_factory=lambda: str(random.randint(1000, 9999)))

    @property
    def value(self) -> Fraction:
        if self.type == "antimatter":
            return Fraction(self.denominator, self.numerator)
        return Fraction(self.numerator, self.denominator)

    @property
    def display(self) -> str:
        # 視覺化符號：乘法用實心，除法用空心或反轉符號
        op = "⨉" if self.type == "matter" else "÷"
        n_show = f"({self.numerator})" if self.numerator < 0 else f"{self.numerator}"
        return f"{op}\n{n_show}\n──\n{self.denominator}"

# ==========================================
# 2. 鍊金引擎 (The Logic Engine)
# ==========================================

class EntropyEngine:
    """負責計算系統熵值與物理反饋"""
    
    @staticmethod
    def calculate_entropy(current_val: Fraction) -> float:
        """
        Model 2: 熱力學與熵增
        熵值由分子分母的大小決定。數值越大，系統越不穩定。
        """
        n, d = abs(current_val.numerator), abs(current_val.denominator)
        if n == 0: return 0.0
        # 使用對數尺度模擬物理壓強
        entropy = math.log10(n * d + 1) * 20 
        return min(entropy, 100.0)

    @staticmethod
    def generate_latex_visualization(history: List[ElementCard]) -> str:
        """
        Model 1: 第一性原理視覺化
        生成帶有顏色標記的 LaTeX，模擬化學反應過程
        """
        if not history: return "1"

        # 構建分子分母列表
        nums, dens = [1], [1]
        raw_ops = []
        
        for card in history:
            n, d = card.numerator, card.denominator
            if card.type == "antimatter":
                nums.append(d)
                dens.append(n)
                raw_ops.append(f"\\div \\frac{{{n}}}{{{d}}}")
            else:
                nums.append(n)
                dens.append(d)
                raw_ops.append(f"\\times \\frac{{{n}}}{{{d}}}")

        # 智能約分標記 (尋找公因數)
        # 這裡僅做簡單視覺化：如果分子分母有相同絕對值的數，標記為紅色刪除線
        cancel_n = [False] * len(nums)
        cancel_d = [False] * len(dens)
        
        for i in range(1, len(nums)):
            for j in range(1, len(dens)):
                if not cancel_d[j] and abs(nums[i]) == abs(dens[j]):
                    cancel_n[i] = True
                    cancel_d[j] = True
                    break

        # 生成 LaTeX
        def fmt(val, cancel):
            color = "red" if cancel else "white"
            s_val = f"({val})" if val < 0 else f"{val}"
            if cancel:
                return f"\\color{{{color}}}{{\\cancel{{{s_val}}}}}"
            return s_val

        num_tex = " \\cdot ".join([fmt(nums[i], cancel_n[i]) for i in range(1, len(nums))])
        den_tex = " \\cdot ".join([fmt(dens[i], cancel_d[i]) for i in range(1, len(dens))])
        
        if not num_tex: num_tex = "1"
        if not den_tex: den_tex = "1"

        return f"\\frac{{{num_tex}}}{{{den_tex}}}"

# ==========================================
# 3. 遊戲狀態管理 (Game State)
# ==========================================

class AlchemyGame:
    def __init__(self):
        if 'level' not in st.session_state:
            self.reset_campaign()
            
    def reset_campaign(self):
        st.session_state.update({
            'level': 1,
            'score': 0,
            'combo': 0, # Model 3: 臨界質量
            'max_entropy_hit': False,
            'history': [],
            'hand': [],
            'target': Fraction(1, 1),
            'game_state': 'planning' # planning, verifying, won, lost
        })
        self.load_level(1)

    def load_level(self, level):
        # 難度曲線設計 (Model 15: 反脆弱)
        config = {
            1: {'range': [2, 3, 4], 'ops': 2, 'allow_div': False, 'allow_neg': False, 'name': "基礎合成 (Matter)"},
            2: {'range': [2, 3, 5], 'ops': 3, 'allow_div': False, 'allow_neg': True, 'name': "極性反轉 (Polarity)"},
            3: {'range': [2, 3, 4, 5, 6], 'ops': 3, 'allow_div': True, 'allow_neg': True, 'name': "等價交換 (Equivalent)"},
            4: {'range': [3, 4, 5, 7, 8, 9], 'ops': 4, 'allow_div': True, 'allow_neg': True, 'name': "高壓煉成 (High Pressure)"},
            5: {'range': [2, 12, 15, 20], 'ops': 5, 'allow_div': True, 'allow_neg': True, 'name': "賢者之石 (Philosopher's Stone)"}
        }
        cfg = config.get(level, config[5])
        
        # 逆向生成保證有解 (Model 9: 逆向思維)
        target = Fraction(1, 1)
        hand = []
        
        # 生成正確路徑
        for _ in range(cfg['ops']):
            n = random.choice(cfg['range'])
            d = random.choice(cfg['range'])
            while n == d: d = random.choice(cfg['range'])
            
            if cfg['allow_neg'] and random.random() < 0.4: n = -n
            is_div = cfg['allow_div'] and random.random() < 0.3
            
            card = ElementCard(n, d, "antimatter" if is_div else "matter")
            hand.append(card)
            target *= card.value

        # 加入干擾項 (Model 4: 基礎比率/陷阱)
        for _ in range(2):
            n = random.choice(cfg['range'])
            d = random.choice(cfg['range'])
            hand.append(ElementCard(n, d, "matter"))
            
        random.shuffle(hand)
        
        st.session_state.level_config = cfg
        st.session_state.target = target
        st.session_state.hand = hand
        st.session_state.history = []
        st.session_state.game_state = 'planning'
        st.session_state.max_entropy_hit = False

    def calculate_current(self):
        val = Fraction(1, 1)
        for card in st.session_state.history:
            val *= card.value
        return val

    def play_card(self, idx):
        if idx < len(st.session_state.hand):
            card = st.session_state.hand.pop(idx)
            st.session_state.history.append(card)
            
            # 檢查是否達到目標，但還沒提交 (Model 11: 回饋迴路)
            current = self.calculate_current()
            entropy = EntropyEngine.calculate_entropy(current)
            if entropy > 80:
                st.toast("⚠️ 警告：熵值過高！反應爐不穩定！請嘗試約分！", icon="🔥")
                st.session_state.max_entropy_hit = True

    def undo_move(self):
        if st.session_state.history:
            card = st.session_state.history.pop()
            st.session_state.hand.append(card)

    def submit_solution(self, confidence):
        current = self.calculate_current()
        target = st.session_state.target
        
        # Model 16: 貝葉斯更新 (信心分數影響得分)
        is_correct = current == target
        
        if is_correct:
            base_score = 100
            # 熵值獎勵：如果在低熵狀態下完成 (Model 10: 奧卡姆剃刀)
            final_entropy = EntropyEngine.calculate_entropy(current)
            entropy_bonus = 50 if final_entropy < 30 else 0
            
            # 信心獎勵
            conf_bonus = 0
            if confidence > 80: conf_bonus = 20
            elif confidence < 30: conf_bonus = -10 # 對自己沒信心但對了，運氣分
            
            total_gain = base_score + entropy_bonus + conf_bonus
            st.session_state.score += total_gain
            st.session_state.combo += 1
            st.session_state.game_state = 'won'
            
        else:
            # 懲罰
            st.session_state.combo = 0
            st.session_state.game_state = 'lost'
            if confidence > 80:
                st.toast("💀 認知偏差！高信心錯誤！", icon="📉")

# ==========================================
# 4. UI 呈現層 (View)
# ==========================================

def main():
    game = AlchemyGame()
    
    # --- Header Area ---
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.title("⚗️ Zero-Entropy Alchemy")
        st.caption(f"Level {st.session_state.level}: {st.session_state.level_config['name']}")
    with c2:
        st.metric("Score", st.session_state.score, delta=f"Combo x{st.session_state.combo}")
    with c3:
        if st.button("🔄 重置實驗"):
            game.reset_campaign()
            st.rerun()

    # --- Target & Goal (The Objective) ---
    target = st.session_state.target
    st.markdown(f"### 🎯 目標元素 (Target Essence)")
    # 使用 LaTeX 顯示目標，強調數值美學
    st.latex(f"\\Huge \\mathbf{{{target.numerator}}} / \\mathbf{{{target.denominator}}}")
    
    # --- Reactor Core (Visual Feedback) ---
    current = game.calculate_current()
    entropy = EntropyEngine.calculate_entropy(current)
    
    # 熵值計量條 (Model 2)
    entropy_color = "red" if entropy > 80 else "green"
    st.markdown(f"<p class='status-text' style='color:{entropy_color}'>Reactor Entropy: {int(entropy)}%</p>", unsafe_allow_html=True)
    st.progress(min(entropy / 100, 1.0))
    
    # 反應式可視化
    box_class = "reactor-box reactor-critical" if entropy > 80 else "reactor-box"
    st.markdown(f'<div class="{box_class}" style="background:#1e293b; padding:20px; border-radius:15px; text-align:center; min-height:150px;">', unsafe_allow_html=True)
    
    if not st.session_state.history:
        st.markdown("<h3 style='color:#64748b'>等待投入素材...</h3>", unsafe_allow_html=True)
    else:
        # 顯示化學鍵斷裂 (約分過程)
        process_tex = EntropyEngine.generate_latex_visualization(st.session_state.history)
        st.latex(f"\\Large 1 \\cdot {process_tex} = \\frac{{{current.numerator}}}{{{current.denominator}}}")
        
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Game Area ---
    if st.session_state.game_state == 'planning':
        
        # 1. 玩家手牌 (Player Hand)
        st.markdown("### 🎴 元素手牌 (Your Hand)")
        cols = st.columns(6)
        for i, card in enumerate(st.session_state.hand):
            with cols[i % 6]:
                if st.button(card.display, key=f"card_{card.id}", use_container_width=True):
                    game.play_card(i)
                    st.rerun()

        # 2. 控制區
        col_undo, col_submit = st.columns([1, 2])
        with col_undo:
            if st.button("↩️ 撤銷 (Undo)", use_container_width=True):
                game.undo_move()
                st.rerun()
                
        with col_submit:
            # Model 16: 貝葉斯信心滑桿
            confidence = st.slider("🧪 煉成信心度 (Confidence)", 0, 100, 50, key="conf_slider")
            if st.button("🔥 啟動鍊成陣 (Transmute)", type="primary", use_container_width=True):
                game.submit_solution(confidence)
                st.rerun()

    # --- Result Area ---
    elif st.session_state.game_state == 'won':
        st.success("✨ 煉成成功！元素完美平衡！")
        st.balloons()
        if st.button("🚀 前往下一層", type="primary"):
            st.session_state.level += 1
            game.load_level(st.session_state.level)
            st.rerun()
            
    elif st.session_state.game_state == 'lost':
        st.error(f"💥 煉成失敗！目標是 {target}，你煉出了 {current}")
        if st.button("🔄 重試本關"):
            game.load_level(st.session_state.level)
            st.rerun()

if __name__ == "__main__":
    main()
