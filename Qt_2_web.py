import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import base64
from io import BytesIO
import sqlite3
import os

# 页面设置
st.set_page_config(
    page_title="眼手匹配性能测试系统",
    page_icon="👁️🖐️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .test-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stimulus-display {
        background-color: #f0f0f0;
        border-radius: 15px;
        padding: 3rem;
        text-align: center;
        font-size: 3rem;
        min-height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2rem 0;
        border: 3px solid #ddd;
        transition: all 0.3s ease;
    }
    .reaction-button {
        background-color: #4CAF50;
        color: white;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        border-radius: 50px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0.5rem;
    }
    .reaction-button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    .stat-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #7f8c8d;
    }
</style>
""", unsafe_allow_html=True)


# 初始化数据库
def init_database():
    conn = sqlite3.connect('reaction_test_web.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            occupation TEXT,
            created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            test_type TEXT,
            stimulus_type TEXT,
            trial_index INTEGER,
            stimulus_content TEXT,
            reaction_time REAL,
            is_correct INTEGER,
            test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_statistics (
            stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            test_type TEXT,
            stimulus_type TEXT,
            avg_reaction_time REAL,
            std_reaction_time REAL,
            min_reaction_time REAL,
            max_reaction_time REAL,
            accuracy_rate REAL,
            total_trials INTEGER,
            test_date DATE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()


# 初始化session state
def init_session_state():
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'user_id': '',
            'name': '',
            'age': 25,
            'gender': '男',
            'occupation': ''
        }

    if 'test_state' not in st.session_state:
        st.session_state.test_state = {
            'is_running': False,
            'current_test': None,
            'current_stimulus': None,
            'reaction_times': [],
            'correct_responses': [],
            'current_trial': 0,
            'total_trials': 10,
            'stimulus_start_time': 0,
            'test_history': []
        }

    if 'page' not in st.session_state:
        st.session_state.page = 'home'


# 刺激物生成器
class WebStimulusGenerator:
    def __init__(self):
        self.colors = {
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'orange': '#FFA500',
            'purple': '#800080',
            'black': '#000000',
            'white': '#FFFFFF'
        }

        self.shapes = ['circle', 'triangle', 'square', 'diamond']
        self.symbols = ['↑', '↓', '←', '→', '✓', '✗', '●', '■', '▲', '▼']
        self.instructions = [
            "请点击按钮！",
            "快速反应！",
            "点击目标",
            "选择红色",
            "注意中心"
        ]

    def generate_stimulus(self, test_type, stimulus_type):
        if test_type == 'simple':
            if stimulus_type == 'color':
                color_name = random.choice(list(self.colors.keys())[:4])
                return {
                    'type': 'color',
                    'color': self.colors[color_name],
                    'name': color_name,
                    'shape': 'circle',
                    'display': f'<div style="width:150px;height:150px;border-radius:50%;background-color:{self.colors[color_name]};margin:auto;"></div>'
                }
            elif stimulus_type == 'shape':
                shape = random.choice(self.shapes)
                color = self.colors[random.choice(list(self.colors.keys())[:4])]
                if shape == 'circle':
                    display = f'<div style="width:150px;height:150px;border-radius:50%;background-color:{color};margin:auto;"></div>'
                elif shape == 'square':
                    display = f'<div style="width:150px;height:150px;background-color:{color};margin:auto;"></div>'
                elif shape == 'triangle':
                    display = f'<div style="width:0;height:0;border-left:75px solid transparent;border-right:75px solid transparent;border-bottom:150px solid {color};margin:auto;"></div>'
                else:  # diamond
                    display = f'<div style="width:150px;height:150px;background-color:{color};transform:rotate(45deg);margin:auto;"></div>'

                return {
                    'type': 'shape',
                    'shape': shape,
                    'color': color,
                    'display': display
                }
            elif stimulus_type == 'symbol':
                symbol = random.choice(self.symbols[:6])
                return {
                    'type': 'symbol',
                    'symbol': symbol,
                    'color': '#000000',
                    'display': f'<div style="font-size:100px;color:#000000;">{symbol}</div>'
                }
            else:  # text
                text = random.choice(self.instructions[:3])
                return {
                    'type': 'text',
                    'text': text,
                    'display': f'<div style="font-size:36px;color:#000000;padding:20px;">{text}</div>'
                }

        elif test_type == 'choice':
            # 生成4个选项
            options = []
            colors = random.sample(list(self.colors.keys())[:4], 4)

            for i, color_name in enumerate(colors):
                options.append({
                    'color': self.colors[color_name],
                    'name': color_name,
                    'index': i + 1
                })

            # 随机选择一个作为目标
            target = random.choice(options)

            return {
                'type': 'choice',
                'options': options,
                'target': target,
                'display': self._generate_choice_display(options, target)
            }

        else:  # disjunctive
            # 生成目标刺激和干扰刺激
            target_type = random.choice(['color', 'shape'])

            if target_type == 'color':
                target_color = random.choice(['red', 'green', 'blue', 'yellow'])
                target = {
                    'type': 'color',
                    'value': target_color,
                    'color': self.colors[target_color],
                    'shape': random.choice(self.shapes[:3])
                }

                # 生成干扰刺激（使用不同颜色）
                distractors = []
                for _ in range(random.randint(3, 6)):
                    available_colors = [c for c in ['red', 'green', 'blue', 'yellow'] if c != target_color]
                    color_name = random.choice(available_colors)
                    distractors.append({
                        'color': self.colors[color_name],
                        'shape': random.choice(self.shapes[:3])
                    })
            else:  # shape
                target_shape = random.choice(self.shapes[:4])
                target = {
                    'type': 'shape',
                    'value': target_shape,
                    'color': self.colors[random.choice(['red', 'green', 'blue', 'yellow'])],
                    'shape': target_shape
                }

                # 生成干扰刺激（使用不同形状）
                distractors = []
                for _ in range(random.randint(3, 6)):
                    available_shapes = [s for s in self.shapes[:4] if s != target_shape]
                    shape = random.choice(available_shapes)
                    distractors.append({
                        'color': self.colors[random.choice(['red', 'green', 'blue', 'yellow'])],
                        'shape': shape
                    })

            return {
                'type': 'disjunctive',
                'target_type': target_type,
                'target': target,
                'distractors': distractors,
                'display': self._generate_disjunctive_display(target, distractors)
            }

    def _generate_choice_display(self, options, target):
        html = '<div style="display:flex;justify-content:center;gap:30px;flex-wrap:wrap;">'
        for opt in options:
            is_target = (opt['name'] == target['name'])
            border = '5px solid #00FF00' if is_target else '2px solid #666'
            html += f'''
            <div style="text-align:center;">
                <div style="width:100px;height:100px;border-radius:50%;background-color:{opt['color']};
                         margin:10px;border:{border};display:flex;align-items:center;justify-content:center;">
                    <span style="color:white;font-weight:bold;font-size:24px;">{opt['index']}</span>
                </div>
                <div>选项 {opt['index']}</div>
            </div>
            '''
        html += '</div>'
        return html

    def _generate_disjunctive_display(self, target, distractors):
        all_stimuli = [target] + distractors
        random.shuffle(all_stimuli)

        html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:500px;margin:auto;">'
        for i, stim in enumerate(all_stimuli):
            is_target = (stim == target)
            border = '4px solid #FFD700' if is_target else '1px solid #999'

            if stim.get('shape', 'circle') == 'circle':
                shape_html = f'<div style="width:80px;height:80px;border-radius:50%;background-color:{stim["color"]};border:{border};margin:auto;"></div>'
            elif stim['shape'] == 'square':
                shape_html = f'<div style="width:80px;height:80px;background-color:{stim["color"]};border:{border};margin:auto;"></div>'
            elif stim['shape'] == 'triangle':
                shape_html = f'<div style="width:0;height:0;border-left:40px solid transparent;border-right:40px solid transparent;border-bottom:80px solid {stim["color"]};border-top:{border};margin:auto;"></div>'
            else:  # diamond
                shape_html = f'<div style="width:80px;height:80px;background-color:{stim["color"]};transform:rotate(45deg);border:{border};margin:auto;"></div>'

            html += f'<div style="text-align:center;">{shape_html}</div>'

        html += '</div>'
        return html


# 数据库操作
class WebDatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('reaction_test_web.db', check_same_thread=False)
        init_database()

    def save_user(self, user_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, name, age, gender, occupation)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_data['user_id'],
            user_data['name'],
            user_data['age'],
            user_data['gender'],
            user_data['occupation']
        ))
        self.conn.commit()

    def save_test_record(self, record_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO test_records 
            (user_id, test_type, stimulus_type, trial_index, stimulus_content, reaction_time, is_correct)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_data['user_id'],
            record_data['test_type'],
            record_data['stimulus_type'],
            record_data['trial_index'],
            json.dumps(record_data['stimulus_content']),
            record_data['reaction_time'],
            1 if record_data['is_correct'] else 0
        ))
        self.conn.commit()

    def save_test_statistics(self, stat_data):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO test_statistics 
            (user_id, test_type, stimulus_type, avg_reaction_time, std_reaction_time, 
             min_reaction_time, max_reaction_time, accuracy_rate, total_trials, test_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            stat_data['user_id'],
            stat_data['test_type'],
            stat_data['stimulus_type'],
            stat_data['avg_reaction_time'],
            stat_data['std_reaction_time'],
            stat_data['min_reaction_time'],
            stat_data['max_reaction_time'],
            stat_data['accuracy_rate'],
            stat_data['total_trials'],
            stat_data['test_date']
        ))
        self.conn.commit()

    def get_user_history(self, user_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM test_statistics 
            WHERE user_id = ? 
            ORDER BY test_date DESC, stat_id DESC 
            LIMIT ?
        ''', (user_id, limit))

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT user_id, name FROM users ORDER BY created_time DESC')
        return cursor.fetchall()


# 测试引擎
class WebTestEngine:
    def __init__(self):
        self.stimulus_generator = WebStimulusGenerator()
        self.db_manager = WebDatabaseManager()

    def start_test(self, test_type, stimulus_type, user_data, trials=10):
        # 重置测试状态
        st.session_state.test_state = {
            'is_running': True,
            'current_test': test_type,
            'current_stimulus_type': stimulus_type,
            'reaction_times': [],
            'correct_responses': [],
            'current_trial': 0,
            'total_trials': trials,
            'stimulus_start_time': 0,
            'user_data': user_data,
            'current_stimulus': None,
            'test_started': False,
            'waiting_for_stimulus': False
        }

        # 保存用户信息
        self.db_manager.save_user(user_data)

        # 准备第一个试次
        self.prepare_next_trial()

    def prepare_next_trial(self):
        if not st.session_state.test_state['is_running']:
            return

        # 如果所有试次完成，结束测试
        if st.session_state.test_state['current_trial'] >= st.session_state.test_state['total_trials']:
            self.complete_test()
            return

        # 设置等待状态
        st.session_state.test_state['waiting_for_stimulus'] = True
        st.session_state.test_state['test_started'] = False
        st.session_state.test_state['current_stimulus'] = None

        # 使用Streamlit的rerun来模拟等待
        st.rerun()

    def show_stimulus(self):
        if not st.session_state.test_state['is_running']:
            return

        # 生成刺激物
        test_type = st.session_state.test_state['current_test']
        stimulus_type = st.session_state.test_state['current_stimulus_type']

        stimulus = self.stimulus_generator.generate_stimulus(test_type, stimulus_type)

        # 更新状态
        st.session_state.test_state['current_stimulus'] = stimulus
        st.session_state.test_state['waiting_for_stimulus'] = False
        st.session_state.test_state['test_started'] = True
        st.session_state.test_state['stimulus_start_time'] = time.time()

        st.rerun()

    def record_response(self, response_data):
        if not st.session_state.test_state['is_running']:
            return False

        # 计算反应时间
        reaction_time = (time.time() - st.session_state.test_state['stimulus_start_time']) * 1000

        # 判断是否正确（简化处理）
        is_correct = True
        if st.session_state.test_state['current_test'] == 'choice':
            # 选择反应时：检查选择的选项
            correct_index = st.session_state.test_state['current_stimulus']['target']['index']
            is_correct = (response_data.get('selected_option') == correct_index)

        # 保存记录
        record_data = {
            'user_id': st.session_state.test_state['user_data']['user_id'],
            'test_type': st.session_state.test_state['current_test'],
            'stimulus_type': st.session_state.test_state['current_stimulus_type'],
            'trial_index': st.session_state.test_state['current_trial'],
            'stimulus_content': st.session_state.test_state['current_stimulus'],
            'reaction_time': reaction_time,
            'is_correct': is_correct
        }

        self.db_manager.save_test_record(record_data)

        # 更新状态
        st.session_state.test_state['reaction_times'].append(reaction_time)
        st.session_state.test_state['correct_responses'].append(is_correct)
        st.session_state.test_state['current_trial'] += 1

        # 准备下一个试次
        self.prepare_next_trial()

        return True

    def complete_test(self):
        if not st.session_state.test_state['is_running']:
            return

        # 计算统计结果
        stats = self.calculate_statistics()

        # 保存统计结果
        if stats:
            stat_data = {
                'user_id': st.session_state.test_state['user_data']['user_id'],
                'test_type': st.session_state.test_state['current_test'],
                'stimulus_type': st.session_state.test_state['current_stimulus_type'],
                'avg_reaction_time': stats['average'],
                'std_reaction_time': stats['std'],
                'min_reaction_time': stats['min'],
                'max_reaction_time': stats['max'],
                'accuracy_rate': stats['accuracy'],
                'total_trials': st.session_state.test_state['total_trials'],
                'test_date': datetime.now().strftime('%Y-%m-%d')
            }

            self.db_manager.save_test_statistics(stat_data)

            # 添加到历史记录
            if 'test_history' not in st.session_state:
                st.session_state.test_history = []

            st.session_state.test_history.append({
                'test_type': st.session_state.test_state['current_test'],
                'stimulus_type': st.session_state.test_state['current_stimulus_type'],
                'statistics': stats,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # 结束测试
        st.session_state.test_state['is_running'] = False
        st.rerun()

    def calculate_statistics(self):
        reaction_times = st.session_state.test_state['reaction_times']
        correct_responses = st.session_state.test_state['correct_responses']

        if not reaction_times:
            return None

        # 只计算正确反应的反应时
        valid_times = []
        for rt, correct in zip(reaction_times, correct_responses):
            if correct:
                valid_times.append(rt)

        if valid_times:
            avg_rt = np.mean(valid_times)
            std_rt = np.std(valid_times)
            min_rt = np.min(valid_times)
            max_rt = np.max(valid_times)
        else:
            avg_rt = std_rt = min_rt = max_rt = 0

        # 计算正确率
        if correct_responses:
            accuracy = sum(correct_responses) / len(correct_responses) * 100
        else:
            accuracy = 0

        return {
            'average': avg_rt,
            'std': std_rt,
            'min': min_rt,
            'max': max_rt,
            'accuracy': accuracy,
            'total_trials': len(reaction_times),
            'valid_trials': len(valid_times)
        }

    def stop_test(self):
        st.session_state.test_state['is_running'] = False
        st.rerun()


# 主应用
def main():
    # 初始化
    init_session_state()
    test_engine = WebTestEngine()
    db_manager = WebDatabaseManager()

    # 标题
    st.markdown('<h1 class="main-header">👁️🖐️ 眼手匹配性能测试系统</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#666;margin-bottom:2rem;">
        基于安全人机工程学的反应时测试系统 | 可测试简单反应时、选择反应时、析取反应时
    </div>
    """, unsafe_allow_html=True)

    # 侧边栏
    with st.sidebar:
        st.header("用户信息")

        user_id = st.text_input("用户ID", value=st.session_state.user_data['user_id'],
                                placeholder="请输入用户ID")
        name = st.text_input("姓名", value=st.session_state.user_data['name'],
                             placeholder="请输入姓名")
        age = st.number_input("年龄", min_value=10, max_value=80,
                              value=st.session_state.user_data['age'])
        gender = st.selectbox("性别", ["男", "女", "其他"],
                              index=["男", "女", "其他"].index(st.session_state.user_data['gender']))
        occupation = st.text_input("职业", value=st.session_state.user_data['occupation'],
                                   placeholder="请输入职业")

        # 更新session state
        st.session_state.user_data = {
            'user_id': user_id if user_id else f"user_{int(time.time())}",
            'name': name,
            'age': age,
            'gender': gender,
            'occupation': occupation
        }

        st.divider()

        st.header("测试设置")

        test_type = st.selectbox(
            "测试类型",
            ["simple", "choice", "disjunctive"],
            format_func=lambda x: {
                "simple": "简单反应时",
                "choice": "选择反应时",
                "disjunctive": "析取反应时"
            }[x]
        )

        stimulus_type = st.selectbox(
            "刺激类型",
            ["color", "shape", "symbol", "text"],
            format_func=lambda x: {
                "color": "颜色刺激",
                "shape": "图形刺激",
                "symbol": "符号刺激",
                "text": "语言引导"
            }[x]
        )

        trials = st.slider("测试次数", min_value=5, max_value=30, value=10)
        difficulty = st.select_slider("难度级别", options=["简单", "中等", "困难"], value="中等")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("开始测试", type="primary", use_container_width=True):
                if not st.session_state.user_data['name']:
                    st.warning("请先输入姓名")
                else:
                    test_engine.start_test(test_type, stimulus_type, st.session_state.user_data, trials)

        with col2:
            if st.button("停止测试", type="secondary", use_container_width=True):
                test_engine.stop_test()

        st.divider()

        st.header("历史用户")
        users = db_manager.get_all_users()
        if users:
            for user_id, user_name in users[:5]:
                st.text(f"{user_name} ({user_id[:8]}...)")
        else:
            st.text("暂无历史用户")

    # 主内容区
    if st.session_state.test_state['is_running']:
        display_test_interface(test_engine)
    else:
        display_home_interface(test_engine, db_manager)


def display_test_interface(test_engine):
    """显示测试界面"""
    test_state = st.session_state.test_state

    # 测试状态信息
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        test_type_display = {
            "simple": "简单反应时",
            "choice": "选择反应时",
            "disjunctive": "析取反应时"
        }.get(test_state['current_test'], "未知")

        st.metric("测试类型", test_type_display)

    with col2:
        stimulus_type_display = {
            "color": "颜色刺激",
            "shape": "图形刺激",
            "symbol": "符号刺激",
            "text": "语言引导"
        }.get(test_state['current_stimulus_type'], "未知")

        st.metric("刺激类型", stimulus_type_display)

    with col3:
        st.metric("当前进度", f"{test_state['current_trial']}/{test_state['total_trials']}")

    with col4:
        if test_state['reaction_times']:
            avg_time = np.mean(test_state['reaction_times'][-5:]) if len(
                test_state['reaction_times']) >= 5 else np.mean(test_state['reaction_times'])
            st.metric("平均反应时", f"{avg_time:.0f} ms")
        else:
            st.metric("平均反应时", "-- ms")

    st.divider()

    # 刺激显示区域
    st.markdown("### 刺激显示区域")

    if test_state['waiting_for_stimulus']:
        # 显示等待提示
        st.markdown('<div class="stimulus-display">准备...<br><small>刺激即将出现</small></div>',
                    unsafe_allow_html=True)

        # 添加一个按钮来触发刺激显示（模拟等待后自动显示）
        if st.button("显示刺激", type="primary"):
            test_engine.show_stimulus()

    elif test_state['test_started'] and test_state['current_stimulus']:
        # 显示刺激物
        stimulus = test_state['current_stimulus']
        st.markdown(f'<div class="stimulus-display">{stimulus["display"]}</div>', unsafe_allow_html=True)

        # 反应按钮区域
        st.markdown("### 反应区域")

        if test_state['current_test'] == 'simple':
            # 简单反应时：单个反应按钮
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("点击反应", type="primary", use_container_width=True, key="simple_reaction"):
                    test_engine.record_response({})

        elif test_state['current_test'] == 'choice':
            # 选择反应时：多个选项按钮
            st.markdown("请选择对应的选项：")

            cols = st.columns(4)
            options = stimulus['options']

            for i, opt in enumerate(options):
                with cols[i]:
                    button_text = f"选项 {opt['index']}"
                    if st.button(button_text, use_container_width=True,
                                 key=f"choice_{opt['index']}"):
                        test_engine.record_response({'selected_option': opt['index']})

        else:  # disjunctive
            # 析取反应时：目标选择
            st.markdown("请点击目标刺激：")

            # 由于Streamlit的限制，我们使用按钮来模拟点击
            st.info(f"目标类型：{stimulus['target_type']} - {stimulus['target']['value']}")

            if st.button("选择目标", type="primary", key="disjunctive_target"):
                test_engine.record_response({'selected_target': True})

    # 实时统计
    st.divider()
    st.markdown("### 实时统计")

    if test_state['reaction_times']:
        col1, col2, col3 = st.columns(3)

        with col1:
            latest_time = test_state['reaction_times'][-1]
            st.metric("上次反应时", f"{latest_time:.0f} ms")

        with col2:
            if test_state['correct_responses']:
                accuracy = sum(test_state['correct_responses']) / len(test_state['correct_responses']) * 100
                st.metric("当前准确率", f"{accuracy:.1f}%")
            else:
                st.metric("当前准确率", "--")

        with col3:
            if len(test_state['reaction_times']) >= 2:
                trend = "↑" if test_state['reaction_times'][-1] > test_state['reaction_times'][-2] else "↓"
                st.metric("趋势", trend)
            else:
                st.metric("趋势", "--")

        # 反应时折线图
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(test_state['reaction_times']) + 1)),
            y=test_state['reaction_times'],
            mode='lines+markers',
            name='反应时',
            line=dict(color='blue', width=2)
        ))

        # 添加平均线
        if len(test_state['reaction_times']) > 1:
            avg_line = np.mean(test_state['reaction_times'])
            fig.add_hline(y=avg_line, line_dash="dash", line_color="red",
                          annotation_text=f"平均: {avg_line:.0f}ms")

        fig.update_layout(
            title="反应时变化曲线",
            xaxis_title="试次",
            yaxis_title="反应时 (ms)",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    # 测试说明
    with st.expander("测试说明"):
        if test_state['current_test'] == 'simple':
            st.info("""
            **简单反应时测试说明：**
            1. 当刺激物出现时，尽快点击"点击反应"按钮
            2. 反应时间越短，成绩越好
            3. 请保持注意力集中
            """)
        elif test_state['current_test'] == 'choice':
            st.info("""
            **选择反应时测试说明：**
            1. 观察出现的刺激物（有颜色边框的为目标）
            2. 根据目标刺激的颜色，点击对应的选项按钮
            3. 既要快速又要准确
            """)
        else:  # disjunctive
            st.info("""
            **析取反应时测试说明：**
            1. 从多个刺激物中找到目标刺激
            2. 目标刺激有金色边框
            3. 点击"选择目标"按钮确认选择
            """)


def display_home_interface(test_engine, db_manager):
    """显示主界面"""
    # 功能介绍
    st.markdown("""
    <div class="test-card">
        <h3>📊 系统功能介绍</h3>
        <p>本系统基于安全人机工程学原理，用于测试人的眼手匹配性能，包括三种反应时测试：</p>
        <ul>
            <li><b>简单反应时</b>：对单一刺激做出固定反应的时间</li>
            <li><b>选择反应时</b>：对多个刺激中特定刺激做出特定反应的时间</li>
            <li><b>析取反应时</b>：从多个刺激中辨别目标刺激并做出反应的时间</li>
        </ul>
        <p>通过不同视觉刺激物（颜色、图形、符号、语言引导）测量用户的反应时间，为界面设计提供数据支持。</p>
    </div>
    """, unsafe_allow_html=True)

    # 快速开始指南
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">第一步</div>
            <div style="font-size:3rem;">👤</div>
            <h3>填写信息</h3>
            <p>在左侧栏填写用户信息</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">第二步</div>
            <div style="font-size:3rem;">⚙️</div>
            <h3>设置参数</h3>
            <p>选择测试类型和刺激类型</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-label">第三步</div>
            <div style="font-size:3rem;">🚀</div>
            <h3>开始测试</h3>
            <p>点击"开始测试"按钮</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 历史统计
    st.markdown("### 📈 历史统计")

    user_id = st.session_state.user_data['user_id']
    if user_id:
        history = db_manager.get_user_history(user_id, limit=10)

        if history:
            # 创建统计图表
            df = pd.DataFrame(history)

            # 平均反应时图表
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=df['test_date'],
                y=df['avg_reaction_time'],
                name='平均反应时',
                marker_color='skyblue'
            ))

            fig1.update_layout(
                title="历史平均反应时",
                xaxis_title="测试日期",
                yaxis_title="反应时 (ms)",
                height=300
            )

            st.plotly_chart(fig1, use_container_width=True)

            # 正确率图表
            col1, col2 = st.columns(2)

            with col1:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=df['test_date'],
                    y=df['accuracy_rate'],
                    mode='lines+markers',
                    name='正确率',
                    line=dict(color='green', width=3)
                ))

                fig2.update_layout(
                    title="正确率变化",
                    xaxis_title="测试日期",
                    yaxis_title="正确率 (%)",
                    height=300
                )

                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                # 测试类型分布
                test_type_counts = df['test_type'].value_counts()
                fig3 = go.Figure(data=[go.Pie(
                    labels=test_type_counts.index,
                    values=test_type_counts.values,
                    hole=.3
                )])

                fig3.update_layout(
                    title="测试类型分布",
                    height=300
                )

                st.plotly_chart(fig3, use_container_width=True)

            # 数据表格
            st.markdown("### 详细历史记录")
            display_df = df[['test_date', 'test_type', 'stimulus_type',
                             'avg_reaction_time', 'accuracy_rate', 'total_trials']].copy()
            display_df.columns = ['测试日期', '测试类型', '刺激类型', '平均反应时(ms)', '正确率(%)', '测试次数']

            # 格式化
            display_df['平均反应时(ms)'] = display_df['平均反应时(ms)'].round(1)
            display_df['正确率(%)'] = display_df['正确率(%)'].round(1)

            st.dataframe(display_df, use_container_width=True)

            # 导出按钮
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 导出历史数据 (CSV)",
                data=csv,
                file_name=f"reaction_test_history_{user_id}.csv",
                mime="text/csv"
            )
        else:
            st.info("暂无历史测试数据，请先进行测试。")
    else:
        st.info("请先填写用户信息查看历史统计。")

    st.divider()

    # 人机工程学原理说明
    with st.expander("📚 安全人机工程学原理说明", expanded=False):
        st.markdown("""
        ### 反应时理论基础

        1. **简单反应时**：对单一刺激做出固定反应的时间
           - 影响因素：刺激强度、感官通道、预备时间
           - 正常范围：150-250ms

        2. **选择反应时**：对多个刺激中特定刺激做出特定反应的时间
           - 影响因素：刺激数量、刺激相似性、练习程度
           - 正常范围：300-500ms

        3. **析取反应时**：从多个刺激中辨别目标刺激并做出反应的时间
           - 影响因素：目标与非目标的相似度、干扰物数量
           - 正常范围：400-700ms

        ### 视觉刺激设计原则

        - **颜色对比度**：不低于4.5:1
        - **图形辨识度**：符合国际通用符号标准
        - **信息层次**：主次分明，引导视线自然流动
        - **位置布局**：符合F形视觉扫描模式

        ### 应用价值

        1. **人机界面设计**：为显示器刷新率、操作响应时间提供设计依据
        2. **职业选拔**：用于需要快速反应职业的人员筛选
        3. **医疗康复**：评估认知功能恢复情况
        4. **教育培训**：提高学生注意力集中能力
        """)


if __name__ == "__main__":
    main()