import streamlit as st
import random
import math
import uuid
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ==========================================
# 0. 全局設定 (Global Config)
# ==========================================
MAX_LEVEL = 5  # 總關卡數

# ==========================================
# 1. 核心配置與 CSS
# ==========================================
st.set_page_config(
    page_title="分數鍊金術 v2.2",
    page_icon="⚗️",
    layout="centered"
)

st.markdown("""
<style>
    /* 全局暗色系實驗室風格 */
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    
    /* 頂部進度條優化 */
    .stProgress > div > div > div > div {
        background-color: #38bdf8;
    }

    /* 煉成反應爐 (公式區容器) */
    .reactor-box {
        background: #1e293b;
        border: 2px solid #475569;
        border-radius: 12px;
        padding: 10px;
        margin: 15px 0;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        text-align: center;
    }

    /* 卡牌按鈕 - 增強質感 */
    div.stButton > button {
        background: linear-gradient(180deg, #334155, #1e293b) !important;
        color: #e2e8f0 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-family: 'Courier New', monospace !important;
        font-size: 1.1rem !important;
        transition: all 0.1s !important;
    }
    div.stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        transform: translateY(-2px);
    }
    div.stButton > button:active {
        transform: translateY(1px);
    }
    
    /* 狀態提示 */
    .status-msg {
        text-align: center;
        font-weight: bold;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .msg-info { background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid #38bdf8; }
    .msg-warn { background: rgba(250, 204, 21, 0.1); color: #facc15; border: 1px solid #facc15; }
    .msg-error { background: rgba(248, 113, 113, 0.1); color: #f87171; border: 1px solid #f87171; }
    .msg-success { background: rgba(74, 222, 128, 0.1); color: #4ade80; border: 1px solid #4ade80; }

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
    # 使用 uuid 避免 ID 碰撞
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def effect_value(self) -> Fraction:
        """實際運算效果 (除法翻轉)"""
        if self.is_division:
            return Fraction(self.denominator, self.numerator)
        return Fraction(self.numerator, self.denominator)

    @property
    def display_text(self) -> str:
        """按鈕上顯示的文字"""
        op = "➗" if self.is_division else "✖️"
        # 負數顯示括號
        n_display = f"({self.numerator})" if self.numerator < 0 else f"{self.numerator}"
        return f"{op} {n_display}/{self.denominator}"

# ==========================================
# 3. 鍊金引擎 (Logic Layer)
# ==========================================

class AlchemyEngine:
    
    @staticmethod
    def generate_level(level: int) -> dict:
        config = {
            1: {'nums': [2, 3], 'steps': 2, 'neg': False, 'div': False, 'title': "基礎合成 (整數)"},
            2: {'nums': [2, 3, 4], 'steps': 2, 'neg': False, 'div': False, 'title': "等價交換 (約分)"},
            3: {'nums': [2, 3, 4, 5], 'steps': 3, 'neg': True, 'div': False, 'title': "極性反轉 (負數)"},
            4: {'nums': [2, 3, 5, 7], 'steps': 3, 'neg': True, 'div': True, 'title': "逆向煉成 (除法)"},
            5: {'nums': [2, 3, 4, 5, 6, 8, 9], 'steps': 4, 'neg': True, 'div': True, 'title': "賢者之石 (高階)"}
        }
        cfg = config.get(level, config[5])
        
        target_val = Fraction(1, 1)
        correct_cards = []
        
        # 逆向生成保證有解
        for _ in range(cfg['steps']):
            n = random.choice(cfg['nums'])
            d = random.choice(cfg['nums'])
            while n == d: d = random.choice(cfg['nums'])
            
            if cfg['neg'] and random.random() < 0.5: n = -n
            is_div = cfg['div'] and random.random() < 0.3
            
            card = MathCard(n, d, is_division=is_div)
            correct_cards.append(card)
            # 計算目標值
            if is_div:
                target_val *= Fraction(d, n)
            else:
                target_val *= Fraction(n, d)

        # 生成干擾項
        distractors = []
        for _ in range(2):
            n = random.choice(cfg['nums'])
            d = random.choice(cfg['nums'])
            if cfg['neg'] and random.random() < 0.5: n = -n
            is_div = cfg['div'] and random.random() < 0.3
            distractors.append(MathCard(n, d, is_division=is_div))

        hand = correct_cards + distractors
        random.shuffle(hand)
        
        return {"target": target_val, "hand": hand, "title": cfg['title']}

    @staticmethod
    def calculate_current(history: List[MathCard]) -> Fraction:
        val = Fraction(1, 1)
        for card in history:
            val *= card.effect_value
        return val

    @staticmethod
    def generate_visual_cancellation(history: List[MathCard]) -> str:
        """
        生成帶有約分刪除線的 LaTeX
        """
        if not history: return "1"

        # 1. 收集所有的分子與分母 (展開除法)
        nums = [1]
        dens = [1]
        
        raw_latex_parts = []
        
        for card in history:
            n, d = card.numerator, card.denominator
            if card.is_division:
                # 除法：視覺上顯示翻轉
                nums.append(d)
                dens.append(n)
                # 負號處理
                raw_latex_parts.append(f"\\div \\frac{{{n}}}{{{d}}}")
            else:
                nums.append(n)
                dens.append(d)
                raw_latex_parts.append(f"\\times \\frac{{{n}}}{{{d}}}")

        # 2. 找尋公因數並標記約分 (視覺標記)
        cancel_map_n = [False] * len(nums)
        cancel_map_d = [False] * len(dens)
        
        for i in range(len(nums)):
            for j in range(len(dens)):
                if not cancel_map_d[j] and abs(nums[i]) == abs(dens[j]) and abs(nums[i]) != 1:
                    cancel_map_n[i] = True
                    cancel_map_d[j] = True
                    break
        
        # 3. 生成合併後的 LaTeX
        # 分子
        num_tex = ""
        for i, val in enumerate(nums):
            if i == 0 and val == 1 and len(nums)>1: continue 
            s_val = f"({val})" if val < 0 else f"{val}"
            if cancel_map_n[i]:
                num_tex += f" \\cancel{{{s_val}}} \\cdot"
            else:
                num_tex += f" {s_val} \\cdot"
        
        # 分母
        den_tex = ""
        for i, val in enumerate(dens):
            if i == 0 and val == 1 and len(dens)>1: continue
            s_val = f"({val})" if val < 0 else f"{val}"
            if cancel_map_d[i]:
                den_tex += f" \\cancel{{{s_val}}} \\cdot"
            else:
                den_tex += f" {s_val} \\cdot"

        num_tex = num_tex.rstrip(" \\cdot")
        den_tex = den_tex.rstrip(" \\cdot")
        
        if not num_tex: num_tex = "1"
        if not den_tex: den_tex = "1"

        # 組合部分
        full_raw = "".join(raw_latex_parts)
        if full_raw.startswith("\\times"): full_raw = full_raw[6:]
        
        # 返回純 LaTeX 字符串 (不含 $$)
        return f"1 {full_raw} = \\frac{{{num_tex}}}{{{den_tex}}}"

# ==========================================
# 4. 狀態管理
# ==========================================

class GameState:
    def __init__(self):
        if 'level' not in st.session_state:
            self.init_game()
    
    def init_game(self):
        st.session_state.update({
            'level': 1,
            'history': [],
            'game_status': 'playing',
            'msg': '準備開始煉成...',
            'msg_type': 'info'
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
        st.session_state.msg_type = 'info'

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
            st.session_state.msg = "時光回溯：已撤銷上一步"
            st.session_state.msg_type = 'info'

    # [FIX] 補回遺失的 retry 方法，解決 AttributeError
    def retry(self):
        self.start_level(st.session_state.level)

    def _check_status(self):
        current = AlchemyEngine.calculate_current(st.session_state.history)
        target = st.session_state.target
        
        if current == target:
            st.session_state.game_status = 'won'
            st.session_state.msg = "✨ 煉成成功！元素完美平衡！"
            st.session_state.msg_type = 'success'
        elif not st.session_state.hand:
            st.session_state.game_status = 'lost'
            st.session_state.msg = "🌑 煉成失敗：素材耗盡，無法達成目標。"
            st.session_state.msg_type = 'error'
        else:
            # Scaffolding
            if (current > 0 > target) or (current < 0 < target):
                st.session_state.msg = "⚠️ 極性錯誤！正負號相反，請投入負數素材。"
                st.session_state.msg_type = 'warn'
            elif abs(current) > abs(target):
                st.session_state.msg = "📉 濃度過高：數值過大，需要除法或分數來稀釋。"
                st.session_state.msg_type = 'info'
            elif abs(current) < abs(target):
                st.session_state.msg = "📈 濃度不足：數值過小，需要乘法來增強。"
                st.session_state.msg_type = 'info'
            else:
                st.session_state.msg = "⚗️ 反應進行中..."
                st.session_state.msg_type = 'info'

    def next_level(self):
        if st.session_state.level >= MAX_LEVEL:
            st.session_state.game_status = 'completed'
        else:
            self.start_level(st.session_state.level + 1)
            
    def restart_game(self):
        self.init_game()

# ==========================================
# 5. UI 呈現層
# ==========================================

def main():
    game = GameState()
    
    # --- Top Bar ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("⚗️ 分數鍊金術")
    with c2:
        if st.button("🔄 重置實驗"):
            game.restart_game()
            st.rerun()

    progress = st.session_state.level / MAX_LEVEL
    st.progress(progress)
    st.caption(f"Level {st.session_state.level}/{MAX_LEVEL}: {st.session_state.get('level_title', '')}")

    # --- Game Completed ---
    if st.session_state.game_status == 'completed':
        st.balloons()
        st.markdown("""
        <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:30px;border-radius:15px;text-align:center;color:white;">
            <h1>🏆 賢者之石已煉成！</h1>
            <p>你已掌握所有鍊金術奧義 (分數運算)。</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎓 開啟新一輪試煉", use_container_width=True):
            game.restart_game()
            st.rerun()
        return

    # --- Dashboard ---
    target = st.session_state.target
    current = AlchemyEngine.calculate_current(st.session_state.history)
    
    # 視覺化對比
    col_tgt, col_mid, col_cur = st.columns([1, 0.2, 1])
    with col_tgt:
        st.markdown(f"<div style='text-align:center;color:#94a3b8'>目標元素</div>", unsafe_allow_html=True)
        st.latex(f"\\Huge \\frac{{{target.numerator}}}{{{target.denominator}}}")
    with col_mid:
        status_icon = "⚖️"
        if current == target: status_icon = "✅"
        elif st.session_state.game_status == 'lost': status_icon = "❌"
        st.markdown(f"<div style='text-align:center;font-size:2.5rem;padding-top:10px'>{status_icon}</div>", unsafe_allow_html=True)
    with col_cur:
        cur_color = "#4ade80" if current == target else "#facc15"
        st.markdown(f"<div style='text-align:center;color:#94a3b8'>當前混合物</div>", unsafe_allow_html=True)
        st.latex(f"\\Huge \\color{{{cur_color}}}{{\\frac{{{current.numerator}}}{{{current.denominator}}}}}")

    # --- Message Box ---
    msg_cls = f"msg-{st.session_state.msg_type}"
    st.markdown(f'<div class="status-msg {msg_cls}">{st.session_state.msg}</div>', unsafe_allow_html=True)

    # --- Reactor (Visual Equation) ---
    st.markdown("**📜 煉成反應式：**")
    
    # 1. 生成不含 $$ 的 LaTeX
    visual_latex = AlchemyEngine.generate_visual_cancellation(st.session_state.history)
    
    # 2. 開啟容器
    st.markdown('<div class="reactor-box">', unsafe_allow_html=True)
    
    # 3. 渲染 LaTeX (自動處理符號)
    final_equation = f"{visual_latex} = \\frac{{{current.numerator}}}{{{current.denominator}}}"
    st.latex(final_equation)
    
    # 4. 關閉容器
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Play Area ---
    if st.session_state.game_status == 'playing':
        st.write("👇 點擊素材投入反應爐：")
        hand = st.session_state.hand
        
        if hand:
            cols = st.columns(4)
            for i, card in enumerate(hand):
                with cols[i % 4]:
                    if st.button(card.display_text, key=f"card_{card.id}", use_container_width=True):
                        game.play_card(i)
                        st.rerun()
        
        if st.session_state.history:
            st.markdown("---")
            if st.button("↩️ 撤銷投入 (Undo)"):
                game.undo()
                st.rerun()

    # --- Result Actions ---
    elif st.session_state.game_status == 'won':
        if st.button("🚀 前往下一層", type="primary", use_container_width=True):
            game.next_level()
            st.rerun()
            
    elif st.session_state.game_status == 'lost':
        if st.button("💥 清理反應爐 (重試)", type="primary", use_container_width=True):
            game.retry()
            st.rerun()

if __name__ == "__main__":
    main()
