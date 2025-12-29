#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
眼手匹配性能测试软件系统
安全人机工程课程设计
作者：学生姓名
学号：XXXXXXXX
"""

import sys
import time
import random
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class StimulusGenerator:
    """刺激物生成器类"""

    def __init__(self):
        # 颜色库 - 使用高对比度颜色
        self.colors = {
            'red': QColor(255, 0, 0),
            'green': QColor(0, 200, 0),
            'blue': QColor(0, 120, 255),
            'yellow': QColor(255, 220, 0),
            'white': QColor(255, 255, 255),
            'black': QColor(0, 0, 0),
            'orange': QColor(255, 140, 0),
            'purple': QColor(160, 0, 220)
        }

        # 图形库
        self.shapes = ['circle', 'triangle', 'square', 'diamond', 'pentagon']

        # 符号库
        self.symbols = ['↑', '↓', '←', '→', '✓', '✗', '●', '■', '▲', '▼']

        # 文字提示库
        self.instructions = [
            "请按空格键",
            "快速反应！",
            "点击目标",
            "选择红色",
            "注意中心",
            "准备开始",
            "请按对应键",
            "找到目标"
        ]

        # 反应键映射
        self.key_mapping = {
            'red': Qt.Key.Key_1,
            'green': Qt.Key.Key_2,
            'blue': Qt.Key.Key_3,
            'yellow': Qt.Key.Key_4,
            'circle': Qt.Key.Key_Q,
            'triangle': Qt.Key.Key_W,
            'square': Qt.Key.Key_E,
            'diamond': Qt.Key.Key_R
        }

    def generate_simple_stimulus(self, stim_type: str = "color") -> Dict[str, Any]:
        """生成简单反应时刺激物"""
        if stim_type == "color":
            color_name = random.choice(list(self.colors.keys())[:4])  # 前4种基本颜色
            return {
                'type': 'color',
                'color': self.colors[color_name],
                'name': color_name,
                'size': random.choice([60, 80, 100]),
                'shape': 'circle'
            }
        elif stim_type == "shape":
            shape = random.choice(self.shapes[:4])
            color = self.colors[random.choice(list(self.colors.keys())[:4])]
            return {
                'type': 'shape',
                'shape': shape,
                'color': color,
                'size': random.choice([60, 80, 100]),
                'filled': random.choice([True, False])
            }
        elif stim_type == "symbol":
            symbol = random.choice(self.symbols[:6])
            return {
                'type': 'symbol',
                'symbol': symbol,
                'color': self.colors['black'],
                'size': 80,
                'font_size': 48
            }
        else:  # text
            instruction = random.choice(self.instructions[:3])
            return {
                'type': 'text',
                'text': instruction,
                'color': self.colors['black'],
                'size': 80,
                'font_size': 24
            }

    def generate_choice_stimuli(self, count: int = 4) -> List[Dict[str, Any]]:
        """生成选择反应时刺激物集"""
        stimuli = []
        used_colors = []

        for i in range(count):
            # 确保每个刺激物不同
            available_colors = [c for c in list(self.colors.keys())[:4] if c not in used_colors]
            if not available_colors:
                available_colors = list(self.colors.keys())[:4]

            color_name = random.choice(available_colors)
            used_colors.append(color_name)

            stimuli.append({
                'type': 'color',
                'color': self.colors[color_name],
                'name': color_name,
                'size': 60,
                'shape': 'circle',
                'position': i,  # 0-3对应四个位置
                'key': self.key_mapping.get(color_name, Qt.Key.Key_1 + i)
            })

        return stimuli

    def generate_disjunctive_stimuli(self, target_type: str = "color") -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """生成析取反应时刺激物集"""
        # 生成目标刺激
        if target_type == "color":
            target_color = random.choice(['red', 'green', 'blue', 'yellow'])
            target = {
                'type': 'target',
                'target_type': 'color',
                'value': target_color,
                'color': self.colors[target_color],
                'shape': random.choice(self.shapes[:3]),
                'size': 60,
                'is_target': True
            }
        else:  # shape
            target_shape = random.choice(self.shapes[:4])
            target = {
                'type': 'target',
                'target_type': 'shape',
                'value': target_shape,
                'color': self.colors[random.choice(['red', 'green', 'blue', 'yellow'])],
                'shape': target_shape,
                'size': 60,
                'is_target': True
            }

        # 生成干扰刺激（3-6个）
        distractors = []
        num_distractors = random.randint(3, 6)

        for _ in range(num_distractors):
            if target_type == "color":
                # 干扰刺激使用不同的颜色但可能相同的形状
                available_colors = [c for c in ['red', 'green', 'blue', 'yellow'] if c != target['value']]
                color_name = random.choice(available_colors)
                distractor = {
                    'type': 'distractor',
                    'color': self.colors[color_name],
                    'shape': random.choice(self.shapes[:3]),
                    'size': 60,
                    'is_target': False
                }
            else:  # shape
                # 干扰刺激使用不同的形状但可能相同的颜色
                available_shapes = [s for s in self.shapes[:4] if s != target['value']]
                shape = random.choice(available_shapes)
                distractor = {
                    'type': 'distractor',
                    'color': self.colors[random.choice(['red', 'green', 'blue', 'yellow'])],
                    'shape': shape,
                    'size': 60,
                    'is_target': False
                }
            distractors.append(distractor)

        return target, distractors


class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "reaction_test.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建用户表
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

        # 创建测试记录表
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

        # 创建测试统计表
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

    def save_user(self, user_data: Dict[str, Any]) -> bool:
        """保存用户信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, name, age, gender, occupation)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_data['user_id'],
                user_data['name'],
                user_data['age'],
                user_data.get('gender', ''),
                user_data.get('occupation', '')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存用户信息失败: {e}")
            return False

    def save_test_record(self, record_data: Dict[str, Any]) -> bool:
        """保存单次测试记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO test_records 
                (user_id, test_type, stimulus_type, trial_index, 
                 stimulus_content, reaction_time, is_correct)
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

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存测试记录失败: {e}")
            return False

    def save_test_statistics(self, stat_data: Dict[str, Any]) -> bool:
        """保存测试统计结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO test_statistics 
                (user_id, test_type, stimulus_type, avg_reaction_time,
                 std_reaction_time, min_reaction_time, max_reaction_time,
                 accuracy_rate, total_trials, test_date)
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

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存统计结果失败: {e}")
            return False

    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM test_statistics 
                WHERE user_id = ? 
                ORDER BY test_date DESC, stat_id DESC 
                LIMIT ?
            ''', (user_id, limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return []

    def get_trial_details(self, user_id: str, test_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取详细测试记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if test_type:
                cursor.execute('''
                    SELECT * FROM test_records 
                    WHERE user_id = ? AND test_type = ?
                    ORDER BY trial_index 
                    LIMIT ?
                ''', (user_id, test_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM test_records 
                    WHERE user_id = ? 
                    ORDER BY test_time DESC 
                    LIMIT ?
                ''', (user_id, limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取详细记录失败: {e}")
            return []


class TestEngine(QObject):
    """测试引擎类"""

    # 定义信号
    test_started = pyqtSignal(str)
    stimulus_shown = pyqtSignal(dict)
    response_recorded = pyqtSignal(dict)
    test_completed = pyqtSignal(dict)
    test_timeout = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stimulus_generator = StimulusGenerator()
        self.db_manager = DatabaseManager()

        # 测试状态变量
        self.current_test_type = None
        self.current_stimulus_type = None
        self.reaction_times = []
        self.correct_responses = []
        self.current_trial = 0
        self.total_trials = 10
        self.stimulus_start_time = 0
        self.is_test_running = False
        self.current_stimulus = None
        self.user_data = {}

        # 定时器
        self.wait_timer = QTimer()
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self.show_stimulus)

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_timeout)

    def setup_test(self, test_type: str, stimulus_type: str, user_data: Dict[str, Any],
                   trials: int = 10):
        """设置测试参数"""
        self.current_test_type = test_type
        self.current_stimulus_type = stimulus_type
        self.user_data = user_data
        self.total_trials = trials

        # 重置状态
        self.reaction_times = []
        self.correct_responses = []
        self.current_trial = 0
        self.is_test_running = False

    def start_test(self):
        """开始测试"""
        if not self.current_test_type or not self.user_data:
            return False

        self.reaction_times = []
        self.correct_responses = []
        self.current_trial = 0
        self.is_test_running = True

        # 发出测试开始信号
        self.test_started.emit(f"{self.current_test_type}测试开始")

        # 开始第一个试次
        QTimer.singleShot(1000, self.prepare_trial)
        return True

    def prepare_trial(self):
        """准备试次"""
        if not self.is_test_running or self.current_trial >= self.total_trials:
            return

        # 随机等待时间（1-3秒）
        wait_time = random.uniform(1.0, 3.0) * 1000
        self.wait_timer.start(int(wait_time))

    def show_stimulus(self):
        """显示刺激物"""
        if not self.is_test_running:
            return

        # 生成刺激物
        if self.current_test_type == "simple":
            self.current_stimulus = self.stimulus_generator.generate_simple_stimulus(
                self.current_stimulus_type
            )
        elif self.current_test_type == "choice":
            # 选择反应时：生成4个刺激物，随机选择一个显示
            stimuli = self.stimulus_generator.generate_choice_stimuli(4)
            self.current_stimulus = random.choice(stimuli)
            self.current_stimulus['all_stimuli'] = stimuli
        elif self.current_test_type == "disjunctive":
            # 析取反应时：生成目标刺激和干扰刺激
            target_type = random.choice(['color', 'shape'])
            target, distractors = self.stimulus_generator.generate_disjunctive_stimuli(target_type)
            self.current_stimulus = {
                'target': target,
                'distractors': distractors,
                'target_type': target_type
            }

        # 记录刺激显示时间
        self.stimulus_start_time = time.time() * 1000

        # 发出刺激显示信号
        self.stimulus_shown.emit(self.current_stimulus)

        # 设置超时定时器（3秒）
        self.timeout_timer.start(3000)

    def record_response(self, key: Qt.Key = None, click_pos: QPoint = None) -> bool:
        """记录用户反应"""
        if not self.is_test_running or self.stimulus_start_time == 0:
            return False

        # 停止超时定时器
        self.timeout_timer.stop()

        # 计算反应时间
        reaction_time = time.time() * 1000 - self.stimulus_start_time

        # 判断是否正确
        is_correct = True
        correct_key = None

        if self.current_test_type == "simple":
            # 简单反应时：只要有反应就正确
            is_correct = True
            correct_key = Qt.Key.Key_Space
        elif self.current_test_type == "choice":
            # 选择反应时：检查按键是否正确
            correct_key = self.current_stimulus.get('key', Qt.Key.Key_1)
            is_correct = (key == correct_key)
        elif self.current_test_type == "disjunctive":
            # 析取反应时：检查是否点击了目标
            # 这里简化处理：只要有反应就认为正确（实际需要检查点击位置）
            is_correct = True

        # 保存记录
        self.reaction_times.append(reaction_time)
        self.correct_responses.append(is_correct)

        # 保存到数据库
        record_data = {
            'user_id': self.user_data.get('user_id', ''),
            'test_type': self.current_test_type,
            'stimulus_type': self.current_stimulus_type,
            'trial_index': self.current_trial,
            'stimulus_content': self.current_stimulus,
            'reaction_time': reaction_time,
            'is_correct': is_correct
        }
        self.db_manager.save_test_record(record_data)

        # 发出反应记录信号
        response_data = {
            'trial': self.current_trial + 1,
            'reaction_time': reaction_time,
            'is_correct': is_correct,
            'correct_key': correct_key
        }
        self.response_recorded.emit(response_data)

        # 重置刺激开始时间
        self.stimulus_start_time = 0

        # 下一个试次或结束测试
        self.current_trial += 1
        if self.current_trial < self.total_trials:
            QTimer.singleShot(1000, self.prepare_trial)
        else:
            self.complete_test()

        return True

    def handle_timeout(self):
        """处理反应超时"""
        if not self.is_test_running:
            return

        # 记录超时
        self.reaction_times.append(3000)  # 超时时间设为3秒
        self.correct_responses.append(False)

        # 保存到数据库
        record_data = {
            'user_id': self.user_data.get('user_id', ''),
            'test_type': self.current_test_type,
            'stimulus_type': self.current_stimulus_type,
            'trial_index': self.current_trial,
            'stimulus_content': self.current_stimulus,
            'reaction_time': 3000,
            'is_correct': False
        }
        self.db_manager.save_test_record(record_data)

        # 发出超时信号
        self.test_timeout.emit()

        # 下一个试次或结束测试
        self.current_trial += 1
        if self.current_trial < self.total_trials:
            QTimer.singleShot(1000, self.prepare_trial)
        else:
            self.complete_test()

    def complete_test(self):
        """完成测试"""
        self.is_test_running = False
        self.stimulus_start_time = 0

        # 计算统计结果
        statistics = self.calculate_statistics()

        # 保存统计结果
        if statistics:
            stat_data = {
                'user_id': self.user_data.get('user_id', ''),
                'test_type': self.current_test_type,
                'stimulus_type': self.current_stimulus_type,
                'avg_reaction_time': statistics['average'],
                'std_reaction_time': statistics['std'],
                'min_reaction_time': statistics['min'],
                'max_reaction_time': statistics['max'],
                'accuracy_rate': statistics['accuracy'],
                'total_trials': self.total_trials,
                'test_date': datetime.now().strftime('%Y-%m-%d')
            }
            self.db_manager.save_test_statistics(stat_data)

        # 发出测试完成信号
        self.test_completed.emit(statistics or {})

    def calculate_statistics(self) -> Optional[Dict[str, Any]]:
        """计算统计结果"""
        if not self.reaction_times:
            return None

        # 只计算正确反应的反应时
        valid_times = []
        for rt, correct in zip(self.reaction_times, self.correct_responses):
            if correct and rt < 3000:  # 排除超时
                valid_times.append(rt)

        if valid_times:
            avg_rt = np.mean(valid_times)
            std_rt = np.std(valid_times)
            min_rt = np.min(valid_times)
            max_rt = np.max(valid_times)
        else:
            avg_rt = std_rt = min_rt = max_rt = 0

        # 计算正确率（排除超时）
        total_valid = len([c for c in self.correct_responses if c is not None])
        if total_valid > 0:
            accuracy = sum(1 for c in self.correct_responses if c) / total_valid * 100
        else:
            accuracy = 0

        return {
            'average': avg_rt,
            'std': std_rt,
            'min': min_rt,
            'max': max_rt,
            'accuracy': accuracy,
            'total_trials': self.total_trials,
            'valid_trials': len(valid_times)
        }

    def stop_test(self):
        """停止测试"""
        self.is_test_running = False
        self.wait_timer.stop()
        self.timeout_timer.stop()


class StimulusDisplayWidget(QWidget):
    """刺激物显示部件"""

    def __init__(self):
        super().__init__()
        self.current_stimulus = None
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #f0f0f0; border-radius: 10px;")

    def display_stimulus(self, stimulus: Dict[str, Any]):
        """显示刺激物"""
        self.current_stimulus = stimulus
        self.update()

    def clear_stimulus(self):
        """清除刺激物"""
        self.current_stimulus = None
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # 如果没有刺激物，显示提示
        if not self.current_stimulus:
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 16))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "准备测试...")
            return

        # 获取中心点
        center = self.rect().center()

        # 根据测试类型绘制不同的刺激物
        if isinstance(self.current_stimulus, dict):
            test_type = self.current_stimulus.get('type', 'simple')

            if test_type == 'simple' or 'color' in self.current_stimulus:
                self._draw_simple_stimulus(painter, center)
            elif 'all_stimuli' in self.current_stimulus:
                self._draw_choice_stimuli(painter)
            elif 'target' in self.current_stimulus:
                self._draw_disjunctive_stimuli(painter)

    def _draw_simple_stimulus(self, painter: QPainter, center: QPoint):
        """绘制简单刺激物"""
        stimulus = self.current_stimulus

        if stimulus.get('type') == 'color' or 'color' in stimulus:
            # 绘制颜色刺激
            color = stimulus.get('color', QColor(255, 0, 0))
            size = stimulus.get('size', 80)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))

            if stimulus.get('shape', 'circle') == 'circle':
                painter.drawEllipse(center.x() - size // 2, center.y() - size // 2, size, size)
            elif stimulus.get('shape') == 'square':
                painter.drawRect(center.x() - size // 2, center.y() - size // 2, size, size)

        elif stimulus.get('type') == 'symbol':
            # 绘制符号刺激
            symbol = stimulus.get('symbol', '●')
            color = stimulus.get('color', QColor(0, 0, 0))
            font_size = stimulus.get('font_size', 48)

            painter.setPen(QPen(color))
            font = QFont("Arial", font_size)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, symbol)

        elif stimulus.get('type') == 'text':
            # 绘制文字刺激
            text = stimulus.get('text', '请按空格键')
            color = stimulus.get('color', QColor(0, 0, 0))
            font_size = stimulus.get('font_size', 24)

            painter.setPen(QPen(color))
            font = QFont("微软雅黑", font_size)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)

    def _draw_choice_stimuli(self, painter: QPainter):
        """绘制选择反应时刺激物"""
        main_stimulus = self.current_stimulus
        all_stimuli = main_stimulus.get('all_stimuli', [])

        # 计算四个位置
        width = self.width()
        height = self.height()
        positions = [
            QPoint(width // 4, height // 4),  # 左上
            QPoint(width * 3 // 4, height // 4),  # 右上
            QPoint(width // 4, height * 3 // 4),  # 左下
            QPoint(width * 3 // 4, height * 3 // 4)  # 右下
        ]

        for i, stim in enumerate(all_stimuli):
            if i >= len(positions):
                break

            pos = positions[i]
            color = stim.get('color', QColor(255, 0, 0))
            size = stim.get('size', 60)

            # 绘制刺激物
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawEllipse(pos.x() - size // 2, pos.y() - size // 2, size, size)

            # 绘制编号
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(pos.x() - 10, pos.y() + 5, str(i + 1))

            # 如果是当前刺激物，高亮显示
            if stim.get('name') == main_stimulus.get('name'):
                painter.setPen(QPen(QColor(0, 255, 0), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(pos.x() - size // 2 - 5, pos.y() - size // 2 - 5, size + 10, size + 10)

    def _draw_disjunctive_stimuli(self, painter: QPainter):
        """绘制析取反应时刺激物"""
        target = self.current_stimulus.get('target', {})
        distractors = self.current_stimulus.get('distractors', [])
        all_stimuli = [target] + distractors

        # 随机排列位置
        random.shuffle(all_stimuli)

        # 计算网格位置
        width = self.width()
        height = self.height()
        grid_size = 3  # 3x3网格

        for i, stim in enumerate(all_stimuli):
            if i >= grid_size * grid_size:
                break

            # 计算网格位置
            row = i // grid_size
            col = i % grid_size

            x = width * (col + 1) // (grid_size + 1)
            y = height * (row + 1) // (grid_size + 1)

            # 绘制刺激物
            color = stim.get('color', QColor(255, 0, 0))
            shape = stim.get('shape', 'circle')
            size = stim.get('size', 50)
            is_target = stim.get('is_target', False)

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(0, 0, 0), 2))

            if shape == 'circle':
                painter.drawEllipse(x - size // 2, y - size // 2, size, size)
            elif shape == 'triangle':
                self._draw_triangle(painter, x, y, size)
            elif shape == 'square':
                painter.drawRect(x - size // 2, y - size // 2, size, size)
            elif shape == 'diamond':
                self._draw_diamond(painter, x, y, size)

            # 如果是目标刺激，标记
            if is_target:
                painter.setPen(QPen(QColor(255, 255, 0), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(x - size // 2 - 5, y - size // 2 - 5, size + 10, size + 10)

    def _draw_triangle(self, painter: QPainter, x: int, y: int, size: int):
        """绘制三角形"""
        points = [
            QPoint(x, y - size // 2),
            QPoint(x - size // 2, y + size // 2),
            QPoint(x + size // 2, y + size // 2)
        ]
        painter.drawPolygon(QPolygonF([QPointF(p) for p in points]))

    def _draw_diamond(self, painter: QPainter, x: int, y: int, size: int):
        """绘制菱形"""
        points = [
            QPoint(x, y - size // 2),
            QPoint(x + size // 2, y),
            QPoint(x, y + size // 2),
            QPoint(x - size // 2, y)
        ]
        painter.drawPolygon(QPolygonF([QPointF(p) for p in points]))


class StatisticsWidget(QWidget):
    """统计结果显示部件"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.statistics = {}

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 标题
        title_label = QLabel("测试统计")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # 统计信息表格
        self.stats_table = QTableWidget(6, 2)
        self.stats_table.setHorizontalHeaderLabels(["指标", "数值"])
        self.stats_table.setVerticalHeaderLabels([
            "平均反应时", "反应时标准差", "最快反应时",
            "最慢反应时", "正确率", "有效试次"
        ])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.stats_table)

        # 历史记录表格
        history_label = QLabel("历史记录")
        history_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(history_label)

        self.history_table = QTableWidget(10, 4)
        self.history_table.setHorizontalHeaderLabels(["测试类型", "刺激类型", "平均反应时", "测试时间"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history_table)

        self.setLayout(layout)

    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息"""
        self.statistics = stats

        # 更新统计表格
        if stats:
            self.stats_table.setItem(0, 1, QTableWidgetItem(f"{stats.get('average', 0):.1f} ms"))
            self.stats_table.setItem(1, 1, QTableWidgetItem(f"{stats.get('std', 0):.1f} ms"))
            self.stats_table.setItem(2, 1, QTableWidgetItem(f"{stats.get('min', 0):.1f} ms"))
            self.stats_table.setItem(3, 1, QTableWidgetItem(f"{stats.get('max', 0):.1f} ms"))
            self.stats_table.setItem(4, 1, QTableWidgetItem(f"{stats.get('accuracy', 0):.1f}%"))
            self.stats_table.setItem(5, 1,
                                     QTableWidgetItem(f"{stats.get('valid_trials', 0)}/{stats.get('total_trials', 0)}"))

    def update_history(self, history_data: List[Dict[str, Any]]):
        """更新历史记录"""
        self.history_table.setRowCount(min(len(history_data), 10))

        for i, record in enumerate(history_data[:10]):
            self.history_table.setItem(i, 0, QTableWidgetItem(record.get('test_type', '')))
            self.history_table.setItem(i, 1, QTableWidgetItem(record.get('stimulus_type', '')))
            self.history_table.setItem(i, 2, QTableWidgetItem(f"{record.get('avg_reaction_time', 0):.1f} ms"))

            test_date = record.get('test_date', '')
            if isinstance(test_date, str) and len(test_date) > 10:
                test_date = test_date[:10]
            self.history_table.setItem(i, 3, QTableWidgetItem(test_date))


class ReactionTestApp(QMainWindow):
    """主应用程序类"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_test_engine()
        self.current_user = {}

        # 连接信号
        self.connect_signals()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("眼手匹配性能测试系统 - 安全人机工程课程设计")
        self.setGeometry(100, 100, 1400, 900)

        # 设置应用程序图标
        self.setWindowIcon(QIcon(self.create_app_icon()))

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧面板 - 用户信息和测试设置
        left_panel = self.create_left_panel()
        main_layout.addLayout(left_panel, 1)

        # 中间面板 - 测试显示
        center_panel = self.create_center_panel()
        main_layout.addLayout(center_panel, 2)

        # 右侧面板 - 统计结果
        right_panel = self.create_right_panel()
        main_layout.addLayout(right_panel, 1)

    def create_left_panel(self) -> QVBoxLayout:
        """创建左侧面板"""
        layout = QVBoxLayout()

        # 用户信息组
        user_group = QGroupBox("用户信息")
        user_layout = QFormLayout()

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("请输入用户ID")

        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("请输入姓名")

        self.user_age_input = QSpinBox()
        self.user_age_input.setRange(10, 80)
        self.user_age_input.setValue(25)

        self.user_gender_combo = QComboBox()
        self.user_gender_combo.addItems(["男", "女", "其他"])

        self.user_occupation_input = QLineEdit()
        self.user_occupation_input.setPlaceholderText("请输入职业")

        user_layout.addRow("用户ID:", self.user_id_input)
        user_layout.addRow("姓名:", self.user_name_input)
        user_layout.addRow("年龄:", self.user_age_input)
        user_layout.addRow("性别:", self.user_gender_combo)
        user_layout.addRow("职业:", self.user_occupation_input)

        user_group.setLayout(user_layout)
        layout.addWidget(user_group)

        # 测试设置组
        test_group = QGroupBox("测试设置")
        test_layout = QVBoxLayout()

        # 测试类型选择
        test_type_group = QGroupBox("测试类型")
        test_type_layout = QVBoxLayout()

        self.simple_test_radio = QRadioButton("简单反应时测试")
        self.choice_test_radio = QRadioButton("选择反应时测试")
        self.disjunctive_test_radio = QRadioButton("析取反应时测试")

        self.simple_test_radio.setChecked(True)

        test_type_layout.addWidget(self.simple_test_radio)
        test_type_layout.addWidget(self.choice_test_radio)
        test_type_layout.addWidget(self.disjunctive_test_radio)
        test_type_group.setLayout(test_type_layout)
        test_layout.addWidget(test_type_group)

        # 刺激类型选择
        stim_group = QGroupBox("刺激类型")
        stim_layout = QVBoxLayout()

        self.color_stim_radio = QRadioButton("颜色刺激")
        self.shape_stim_radio = QRadioButton("图形刺激")
        self.symbol_stim_radio = QRadioButton("符号刺激")
        self.text_stim_radio = QRadioButton("语言引导")

        self.color_stim_radio.setChecked(True)

        stim_layout.addWidget(self.color_stim_radio)
        stim_layout.addWidget(self.shape_stim_radio)
        stim_layout.addWidget(self.symbol_stim_radio)
        stim_layout.addWidget(self.text_stim_radio)
        stim_group.setLayout(stim_layout)
        test_layout.addWidget(stim_group)

        # 测试参数设置
        param_group = QGroupBox("测试参数")
        param_layout = QFormLayout()

        self.trial_count_spin = QSpinBox()
        self.trial_count_spin.setRange(5, 50)
        self.trial_count_spin.setValue(10)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["简单", "中等", "困难"])

        param_layout.addRow("测试次数:", self.trial_count_spin)
        param_layout.addRow("难度级别:", self.difficulty_combo)
        param_group.setLayout(param_layout)
        test_layout.addWidget(param_group)

        # 按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始测试")
        self.start_btn.clicked.connect(self.start_test)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")

        self.stop_btn = QPushButton("停止测试")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        test_layout.addLayout(button_layout)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # 操作说明
        help_group = QGroupBox("操作说明")
        help_layout = QVBoxLayout()

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setText("""
        操作指南：
        1. 填写用户信息
        2. 选择测试类型和刺激类型
        3. 点击"开始测试"
        4. 根据提示进行反应

        反应方式：
        - 简单反应时：出现刺激后按空格键
        - 选择反应时：按对应数字键（1-4）
        - 析取反应时：用鼠标点击目标刺激
        """)

        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        layout.addWidget(help_group)

        layout.addStretch()
        return layout

    def create_center_panel(self) -> QVBoxLayout:
        """创建中间面板"""
        layout = QVBoxLayout()

        # 测试状态显示
        status_group = QGroupBox("测试状态")
        status_layout = QGridLayout()

        self.test_type_label = QLabel("当前测试: 无")
        self.stim_type_label = QLabel("刺激类型: 无")
        self.trial_progress_label = QLabel("进度: 0/0")
        self.reaction_time_label = QLabel("反应时间: -- ms")
        self.accuracy_label = QLabel("准确率: --%")

        # 设置样式
        for label in [self.test_type_label, self.stim_type_label, self.trial_progress_label,
                      self.reaction_time_label, self.accuracy_label]:
            label.setStyleSheet("font-size: 14px; padding: 5px;")

        status_layout.addWidget(self.test_type_label, 0, 0)
        status_layout.addWidget(self.stim_type_label, 0, 1)
        status_layout.addWidget(self.trial_progress_label, 1, 0)
        status_layout.addWidget(self.reaction_time_label, 1, 1)
        status_layout.addWidget(self.accuracy_label, 2, 0, 1, 2)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 刺激显示区域
        self.stimulus_display = StimulusDisplayWidget()
        self.stimulus_display.setMinimumHeight(400)
        layout.addWidget(self.stimulus_display)

        # 实时反馈
        feedback_group = QGroupBox("实时反馈")
        feedback_layout = QVBoxLayout()

        self.feedback_label = QLabel("准备开始测试...")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("font-size: 16px; color: #333; padding: 10px;")

        self.last_reaction_label = QLabel("上次反应: --")
        self.last_reaction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        feedback_layout.addWidget(self.feedback_label)
        feedback_layout.addWidget(self.last_reaction_label)
        feedback_group.setLayout(feedback_layout)
        layout.addWidget(feedback_group)

        # 按键提示
        key_group = QGroupBox("按键提示")
        key_layout = QGridLayout()

        key_labels = [
            ("空格键", "简单反应"),
            ("1-4键", "选择对应刺激"),
            ("鼠标点击", "选择目标刺激")
        ]

        for i, (key, desc) in enumerate(key_labels):
            key_label = QLabel(f"<b>{key}</b>: {desc}")
            key_label.setStyleSheet("padding: 5px;")
            key_layout.addWidget(key_label, i // 2, i % 2)

        key_group.setLayout(key_layout)
        layout.addWidget(key_group)

        return layout

    def create_right_panel(self) -> QVBoxLayout:
        """创建右侧面板"""
        layout = QVBoxLayout()

        # 统计结果显示
        self.stats_widget = StatisticsWidget()
        layout.addWidget(self.stats_widget)

        # 数据导出
        export_group = QGroupBox("数据导出")
        export_layout = QVBoxLayout()

        self.export_excel_btn = QPushButton("导出为Excel")
        self.export_excel_btn.clicked.connect(self.export_to_excel)

        self.export_chart_btn = QPushButton("生成图表")
        self.export_chart_btn.clicked.connect(self.generate_chart)

        self.clear_data_btn = QPushButton("清除数据")
        self.clear_data_btn.clicked.connect(self.clear_data)

        export_layout.addWidget(self.export_excel_btn)
        export_layout.addWidget(self.export_chart_btn)
        export_layout.addWidget(self.clear_data_btn)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        # 系统信息
        info_group = QGroupBox("系统信息")
        info_layout = QVBoxLayout()

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        info_text.setText("""
        眼手匹配性能测试系统
        版本: 1.0
        作者: 安全人机工程课程设计
        功能: 测试简单/选择/析取反应时

        基于PyQt6开发
        数据存储: SQLite
        """)

        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        return layout

    def init_test_engine(self):
        """初始化测试引擎"""
        self.test_engine = TestEngine()
        self.db_manager = DatabaseManager()

    def connect_signals(self):
        """连接信号和槽"""
        # 测试引擎信号
        self.test_engine.test_started.connect(self.on_test_started)
        self.test_engine.stimulus_shown.connect(self.on_stimulus_shown)
        self.test_engine.response_recorded.connect(self.on_response_recorded)
        self.test_engine.test_completed.connect(self.on_test_completed)
        self.test_engine.test_timeout.connect(self.on_test_timeout)

    def create_app_icon(self):
        """创建应用程序图标"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(240, 240, 240))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制眼睛
        painter.setBrush(QColor(100, 150, 255))
        painter.drawEllipse(10, 15, 20, 20)
        painter.setBrush(QColor(0, 0, 0))
        painter.drawEllipse(15, 20, 10, 10)

        # 绘制手
        painter.setBrush(QColor(255, 200, 150))
        painter.drawEllipse(35, 35, 20, 25)

        painter.end()
        return pixmap

    def get_current_user_data(self) -> Dict[str, Any]:
        """获取当前用户数据"""
        user_id = self.user_id_input.text().strip()
        if not user_id:
            user_id = f"user_{int(time.time())}"
            self.user_id_input.setText(user_id)

        return {
            'user_id': user_id,
            'name': self.user_name_input.text().strip(),
            'age': self.user_age_input.value(),
            'gender': self.user_gender_combo.currentText(),
            'occupation': self.user_occupation_input.text().strip()
        }

    def get_current_test_type(self) -> str:
        """获取当前测试类型"""
        if self.simple_test_radio.isChecked():
            return "simple"
        elif self.choice_test_radio.isChecked():
            return "choice"
        else:
            return "disjunctive"

    def get_current_stimulus_type(self) -> str:
        """获取当前刺激类型"""
        if self.color_stim_radio.isChecked():
            return "color"
        elif self.shape_stim_radio.isChecked():
            return "shape"
        elif self.symbol_stim_radio.isChecked():
            return "symbol"
        else:
            return "text"

    def start_test(self):
        """开始测试"""
        # 获取用户数据
        self.current_user = self.get_current_user_data()

        # 保存用户信息到数据库
        self.db_manager.save_user(self.current_user)

        # 获取测试参数
        test_type = self.get_current_test_type()
        stimulus_type = self.get_current_stimulus_type()
        trial_count = self.trial_count_spin.value()

        # 设置测试引擎
        self.test_engine.setup_test(
            test_type=test_type,
            stimulus_type=stimulus_type,
            user_data=self.current_user,
            trials=trial_count
        )

        # 开始测试
        if self.test_engine.start_test():
            # 更新UI状态
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            # 更新状态显示
            test_type_text = {
                "simple": "简单反应时",
                "choice": "选择反应时",
                "disjunctive": "析取反应时"
            }.get(test_type, "未知")

            stim_type_text = {
                "color": "颜色刺激",
                "shape": "图形刺激",
                "symbol": "符号刺激",
                "text": "语言引导"
            }.get(stimulus_type, "未知")

            self.test_type_label.setText(f"当前测试: {test_type_text}")
            self.stim_type_label.setText(f"刺激类型: {stim_type_text}")
            self.trial_progress_label.setText(f"进度: 0/{trial_count}")
            self.feedback_label.setText("准备开始...")

            # 加载用户历史记录
            self.load_user_history()

    def stop_test(self):
        """停止测试"""
        self.test_engine.stop_test()
        self.on_test_stopped()

    def on_test_started(self, message: str):
        """测试开始槽函数"""
        self.feedback_label.setText(message)

    def on_stimulus_shown(self, stimulus: Dict[str, Any]):
        """刺激显示槽函数"""
        self.stimulus_display.display_stimulus(stimulus)
        self.feedback_label.setText("请反应！")

    def on_response_recorded(self, response: Dict[str, Any]):
        """反应记录槽函数"""
        trial = response['trial']
        reaction_time = response['reaction_time']
        is_correct = response['is_correct']

        # 更新进度
        total_trials = self.trial_count_spin.value()
        self.trial_progress_label.setText(f"进度: {trial}/{total_trials}")

        # 显示反应时间
        self.reaction_time_label.setText(f"反应时间: {reaction_time:.0f} ms")

        # 显示反馈
        if is_correct:
            feedback = f"✓ 正确！反应时间: {reaction_time:.0f} ms"
            color = "green"
        else:
            feedback = f"✗ 错误！反应时间: {reaction_time:.0f} ms"
            color = "red"

        self.last_reaction_label.setText(feedback)
        self.last_reaction_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        # 清除刺激显示
        QTimer.singleShot(500, self.stimulus_display.clear_stimulus)

    def on_test_completed(self, statistics: Dict[str, Any]):
        """测试完成槽函数"""
        self.on_test_stopped()

        # 更新统计显示
        self.stats_widget.update_statistics(statistics)

        # 更新准确率显示
        if statistics:
            accuracy = statistics.get('accuracy', 0)
            avg_rt = statistics.get('average', 0)
            self.accuracy_label.setText(f"准确率: {accuracy:.1f}%")

            # 显示完成消息
            self.feedback_label.setText(f"测试完成！平均反应时: {avg_rt:.0f} ms")
            self.feedback_label.setStyleSheet("color: green; font-weight: bold;")

            # 显示结果对话框
            self.show_result_dialog(statistics)

        # 重新加载历史记录
        self.load_user_history()

    def on_test_timeout(self):
        """测试超时槽函数"""
        self.last_reaction_label.setText("⏰ 超时！")
        self.last_reaction_label.setStyleSheet("color: orange; font-weight: bold;")

        # 清除刺激显示
        self.stimulus_display.clear_stimulus()

    def on_test_stopped(self):
        """测试停止槽函数"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # 清除刺激显示
        self.stimulus_display.clear_stimulus()

        # 重置反馈
        self.feedback_label.setText("测试已停止")
        self.feedback_label.setStyleSheet("color: gray;")

    def show_result_dialog(self, statistics: Dict[str, Any]):
        """显示结果对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("测试结果")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        # 结果标题
        title_label = QLabel("测试结果汇总")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 结果表格
        result_table = QTableWidget(6, 2)
        result_table.setHorizontalHeaderLabels(["指标", "数值"])
        result_table.setVerticalHeaderLabels([
            "测试类型", "刺激类型", "平均反应时",
            "最快反应时", "最慢反应时", "正确率"
        ])
        result_table.horizontalHeader().setStretchLastSection(True)
        result_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # 填充数据
        test_type = self.get_current_test_type()
        stim_type = self.get_current_stimulus_type()

        test_type_text = {
            "simple": "简单反应时",
            "choice": "选择反应时",
            "disjunctive": "析取反应时"
        }.get(test_type, "未知")

        stim_type_text = {
            "color": "颜色刺激",
            "shape": "图形刺激",
            "symbol": "符号刺激",
            "text": "语言引导"
        }.get(stim_type, "未知")

        result_table.setItem(0, 1, QTableWidgetItem(test_type_text))
        result_table.setItem(1, 1, QTableWidgetItem(stim_type_text))
        result_table.setItem(2, 1, QTableWidgetItem(f"{statistics.get('average', 0):.1f} ms"))
        result_table.setItem(3, 1, QTableWidgetItem(f"{statistics.get('min', 0):.1f} ms"))
        result_table.setItem(4, 1, QTableWidgetItem(f"{statistics.get('max', 0):.1f} ms"))
        result_table.setItem(5, 1, QTableWidgetItem(f"{statistics.get('accuracy', 0):.1f}%"))

        layout.addWidget(result_table)

        # 评价
        avg_rt = statistics.get('average', 0)
        accuracy = statistics.get('accuracy', 0)

        if avg_rt < 250 and accuracy > 95:
            evaluation = "优秀！反应迅速且准确。"
            color = "#27ae60"
        elif avg_rt < 400 and accuracy > 90:
            evaluation = "良好！反应速度和准确性都不错。"
            color = "#f39c12"
        else:
            evaluation = "有待提高！建议多练习。"
            color = "#e74c3c"

        eval_label = QLabel(evaluation)
        eval_label.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: bold; padding: 10px;")
        eval_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(eval_label)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def load_user_history(self):
        """加载用户历史记录"""
        user_id = self.user_id_input.text().strip()
        if user_id:
            history = self.db_manager.get_user_history(user_id, limit=10)
            self.stats_widget.update_history(history)

    def export_to_excel(self):
        """导出数据到Excel"""
        user_id = self.user_id_input.text().strip()
        if not user_id:
            QMessageBox.warning(self, "警告", "请先输入用户ID")
            return

        # 获取历史记录
        history = self.db_manager.get_user_history(user_id, limit=1000)
        trial_details = self.db_manager.get_trial_details(user_id, limit=1000)

        if not history and not trial_details:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", f"reaction_test_{user_id}.xlsx", "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        try:
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 写入统计摘要
                if history:
                    df_summary = pd.DataFrame(history)
                    df_summary.to_excel(writer, sheet_name='统计摘要', index=False)

                # 写入详细记录
                if trial_details:
                    # 解析刺激内容
                    for record in trial_details:
                        if 'stimulus_content' in record and record['stimulus_content']:
                            try:
                                content = json.loads(record['stimulus_content'])
                                record['stimulus_content'] = str(content)
                            except:
                                pass

                    df_details = pd.DataFrame(trial_details)
                    df_details.to_excel(writer, sheet_name='详细记录', index=False)

                # 写入用户信息
                user_data = [{
                    '用户ID': user_id,
                    '姓名': self.user_name_input.text().strip(),
                    '年龄': self.user_age_input.value(),
                    '性别': self.user_gender_combo.currentText(),
                    '职业': self.user_occupation_input.text().strip(),
                    '导出时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                df_user = pd.DataFrame(user_data)
                df_user.to_excel(writer, sheet_name='用户信息', index=False)

            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def generate_chart(self):
        """生成统计图表"""
        user_id = self.user_id_input.text().strip()
        if not user_id:
            QMessageBox.warning(self, "警告", "请先输入用户ID")
            return

        # 获取历史记录
        history = self.db_manager.get_user_history(user_id, limit=20)
        if not history:
            QMessageBox.warning(self, "警告", "没有足够的数据生成图表")
            return

        try:
            # 创建图表窗口
            chart_window = QDialog(self)
            chart_window.setWindowTitle("统计分析图表")
            chart_window.setMinimumSize(800, 600)

            layout = QVBoxLayout()

            # 创建Matplotlib图表
            fig, axes = plt.subplots(2, 2, figsize=(10, 8))
            fig.suptitle(f'用户 {user_id} - 反应时测试统计图表', fontsize=16)

            # 准备数据
            test_types = [h.get('test_type', '未知') for h in history]
            avg_times = [h.get('avg_reaction_time', 0) for h in history]
            dates = [h.get('test_date', '')[:10] for h in history]
            accuracy = [h.get('accuracy_rate', 0) for h in history]

            # 1. 平均反应时折线图
            axes[0, 0].plot(range(len(avg_times)), avg_times, 'b-o', linewidth=2, markersize=6)
            axes[0, 0].set_xlabel('测试序号')
            axes[0, 0].set_ylabel('平均反应时 (ms)')
            axes[0, 0].set_title('平均反应时变化趋势')
            axes[0, 0].grid(True, alpha=0.3)

            # 2. 正确率柱状图
            axes[0, 1].bar(range(len(accuracy)), accuracy, color='green', alpha=0.7)
            axes[0, 1].set_xlabel('测试序号')
            axes[0, 1].set_ylabel('正确率 (%)')
            axes[0, 1].set_title('测试正确率')
            axes[0, 1].set_ylim([0, 100])
            axes[0, 1].grid(True, alpha=0.3, axis='y')

            # 3. 测试类型分布饼图
            type_counts = {}
            for t in test_types:
                type_counts[t] = type_counts.get(t, 0) + 1

            if type_counts:
                types = list(type_counts.keys())
                counts = list(type_counts.values())
                colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
                axes[1, 0].pie(counts, labels=types, autopct='%1.1f%%', colors=colors[:len(types)])
                axes[1, 0].set_title('测试类型分布')

            # 4. 反应时箱线图
            all_times = []
            type_labels = []
            for t in set(test_types):
                times = [avg_times[i] for i in range(len(test_types)) if test_types[i] == t]
                if times:
                    all_times.append(times)
                    type_labels.append(t)

            if all_times:
                axes[1, 1].boxplot(all_times, labels=type_labels)
                axes[1, 1].set_ylabel('反应时 (ms)')
                axes[1, 1].set_title('不同测试类型反应时分布')
                axes[1, 1].grid(True, alpha=0.3, axis='y')

            plt.tight_layout()

            # 将Matplotlib图表嵌入到Qt中
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)

            # 添加保存按钮
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save |
                                          QDialogButtonBox.StandardButton.Close)
            button_box.accepted.connect(lambda: self.save_chart(fig, user_id))
            button_box.rejected.connect(chart_window.reject)
            layout.addWidget(button_box)

            chart_window.setLayout(layout)
            chart_window.exec()

            plt.close(fig)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成图表失败: {str(e)}")

    def save_chart(self, fig, user_id: str):
        """保存图表"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图表", f"reaction_chart_{user_id}.png", "PNG Files (*.png)"
        )

        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图表已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存图表失败: {str(e)}")

    def clear_data(self):
        """清除数据"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有测试数据吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 重新初始化数据库（删除所有数据）
                self.db_manager = DatabaseManager()
                self.db_manager.init_database()

                # 清空统计显示
                self.stats_widget.update_statistics({})
                self.stats_widget.update_history([])

                # 清空状态显示
                self.test_type_label.setText("当前测试: 无")
                self.stim_type_label.setText("刺激类型: 无")
                self.trial_progress_label.setText("进度: 0/0")
                self.reaction_time_label.setText("反应时间: -- ms")
                self.accuracy_label.setText("准确率: --%")
                self.feedback_label.setText("数据已清除")

                QMessageBox.information(self, "成功", "所有测试数据已清除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清除数据失败: {str(e)}")

    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if not self.test_engine.is_test_running:
            super().keyPressEvent(event)
            return

        # 处理测试中的按键
        key = event.key()

        # 简单反应时：空格键
        if self.get_current_test_type() == "simple":
            if key == Qt.Key.Key_Space:
                self.test_engine.record_response(key)

        # 选择反应时：数字键1-4
        elif self.get_current_test_type() == "choice":
            if key in [Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4]:
                self.test_engine.record_response(key)

        # 析取反应时：鼠标处理，这里不处理键盘

        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标事件处理"""
        if not self.test_engine.is_test_running:
            super().mousePressEvent(event)
            return

        # 析取反应时：鼠标点击
        if self.get_current_test_type() == "disjunctive":
            # 这里可以添加检查点击位置是否在目标上的逻辑
            # 简化处理：只要有点击就认为正确
            self.test_engine.record_response(click_pos=event.pos())

        super().mousePressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        """关闭事件处理"""
        # 停止测试引擎
        self.test_engine.stop_test()

        # 保存用户信息
        user_data = self.get_current_user_data()
        if user_data['user_id'] and user_data['name']:
            self.db_manager.save_user(user_data)

        # 确认关闭
        reply = QMessageBox.question(
            self, "退出", "确定要退出眼手匹配测试系统吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 设置全局字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)

    # 创建并显示主窗口
    window = ReactionTestApp()
    window.show()

    # 显示欢迎消息
    QTimer.singleShot(1000, lambda: QMessageBox.information(
        window, "欢迎使用",
        "欢迎使用眼手匹配性能测试系统！\n\n"
        "请先填写用户信息，然后选择测试类型开始测试。\n"
        "测试结果将自动保存到数据库中。"
    ))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()