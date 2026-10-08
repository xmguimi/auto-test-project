import pyautogui
import pyperclip
import time
import subprocess
import os

# ==========================================
# 帧境AI 画布生成与移动测试脚本 (V2.2 顺序优化版)
# ==========================================

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.0

COORD_NEW_PROJECT_BUTTON = (1117, 503)
COORD_PROJECT_NAME_INPUT = (1112, 662)
COORD_CREATE_BTN = (1355, 817)
COORD_PROMPT_INPUT = (690, 1123)
COORD_SEND_BTN = (1762, 1238)
COORD_GENERATED_CANVAS = (1105, 702)
COORD_FOLDER_BTN = (59, 269)
COORD_EXPORT_BTN = (243, 393)
COORD_SAVE_BTN = (839, 655)

COORD_DRAG_START = (1100, 700)
COORD_DRAG_END = (400, 400)

app_path = r"F:\zhenjing\framerealm-canvas\帧境.exe"

# 0. 启动软件
if os.path.exists(app_path):
    print("🚀 正在自动打开【帧境】软件...")
    subprocess.Popen(app_path)
    print("等待软件首页完全加载...")
    time.sleep(8)
else:
    print("错误：未找到软件，请检查路径。")
    exit()

# 1. 最大化窗口
print("正在通过快捷键最大化窗口...")
pyautogui.hotkey('win', 'up')
time.sleep(2)

# 2. 新建项目
print("点击【新建项目】按钮...")
pyautogui.moveTo(COORD_NEW_PROJECT_BUTTON, duration=0.5)
pyautogui.click()
time.sleep(2)

# 3. 输入画布名称并创建
print("输入画布名称...")
pyautogui.moveTo(COORD_PROJECT_NAME_INPUT, duration=0.5)
pyautogui.click()
time.sleep(0.5)

project_name = "自动化测试项目_v4"
pyperclip.copy(project_name)
pyautogui.hotkey("ctrl", "v")
print(f"画布名称已填写：{project_name}")
time.sleep(1)

print("点击弹窗中的【创建】按钮...")
pyautogui.moveTo(COORD_CREATE_BTN, duration=0.5)
pyautogui.click()
print("等待画布工作区加载...")
time.sleep(6)

# 4. 输入提示词
print("在画布提示词输入框中输入场景描述...")
pyautogui.moveTo(COORD_PROMPT_INPUT, duration=0.5)
time.sleep(0.5)
pyautogui.click()
time.sleep(0.5)

prompt_text = "我想要生成一个蓝天白云下一群小羊的场景"
pyperclip.copy(prompt_text)
pyautogui.hotkey("ctrl", "v")
print(f"已粘贴提示词：{prompt_text}")
time.sleep(1)

# 5. 发送生成
print("点击【发送】按钮，开始AI生成...")
pyautogui.moveTo(COORD_SEND_BTN, duration=0.5)
pyautogui.click()

# 6. 等待生成完成
print("🤖 正在等待AI生成图片（通常需要30-60秒，请耐心等待）...")
time.sleep(45)

print("正在验证画布生成结果...")
pyautogui.moveTo(COORD_GENERATED_CANVAS, duration=0.5)
time.sleep(1)

# ==========================================
# 画布视角移动与缩放测试
# 放在生成完成之后，避免影响提示词输入和发送按钮点击
# ==========================================
print("🖱️ 开始测试【画布视角移动与缩放】...")

print("正在向左上方拖拽移动画布...")
pyautogui.moveTo(COORD_DRAG_START, duration=0.5)
pyautogui.mouseDown()
time.sleep(0.5)
pyautogui.moveTo(COORD_DRAG_END, duration=1.0)
pyautogui.mouseUp()
print("画布移动操作完成。")
time.sleep(1.5)

print("正在执行鼠标滚轮缩放画布...")
pyautogui.scroll(-10)
time.sleep(1)
pyautogui.scroll(10)
print("画布缩放操作完成。")
time.sleep(1)

# 7. 导出图片
print("准备导出图片...")
pyautogui.moveTo(COORD_FOLDER_BTN, duration=0.5)
pyautogui.click()
print("点击导出项目按钮...")
time.sleep(1)

pyautogui.moveTo(COORD_EXPORT_BTN, duration=0.5)
pyautogui.click()
time.sleep(2)

print("点击系统保存窗口的【保存】按钮...")
pyautogui.moveTo(COORD_SAVE_BTN, duration=0.5)
pyautogui.click()

# 8. 结束
print("\n" + "="*50)
print("✅ 【帧境AI】画布生成、移动、缩放及导出全流程成功！")
print("="*50)
time.sleep(3)