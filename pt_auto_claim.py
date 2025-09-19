# ==============================================================================
#  PT 自动认领小助手
#  Author: 7owel
#  Version: 1.0 (BETA)
# ==============================================================================
import pyautogui # pyright: ignore[reportMissingModuleSource]
import time
import logging
import os
import sys
import tkinter as tk
from tkinter import font
from tkinter import scrolledtext
import threading
import queue
import math
import traceback
import ctypes
from PIL import Image # pyright: ignore[reportMissingImports]
import keyboard # pyright: ignore[reportMissingModuleSource] # --- 【新增】为快捷键功能导入库 ---

# --- 【安全设置】禁用PyAutoGUI的故障安全功能 ---
pyautogui.FAILSAFE = False

# --- 1. 适配性改造：全局配置 ---
BASELINE_SCALING = 1.75
IMAGE_CACHE = {}

# --- 2. 适配性改造：检测Windows显示缩放 ---
def get_windows_scaling():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        return scale_factor / 100.0
    except (AttributeError, OSError):
        return 1.0

try:
    CURRENT_SCALING = get_windows_scaling()
    SCALE_FACTOR = CURRENT_SCALING / BASELINE_SCALING
except Exception:
    CURRENT_SCALING = 1.0
    SCALE_FACTOR = 1.0 / BASELINE_SCALING

# --- 资源路径导航函数 ---
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# --- 文件夹配置 ---
def load_images_from_folders():
    base_path = resource_path('images')
    image_categories = {
        'claim_buttons': [], 'ok_buttons': [],
        'next_page_buttons': [], 'next_page_disabled_buttons': [], 'end_markers': []
    }
    if not os.path.isdir(base_path): return None, (f"❌ 错误：未找到 '{base_path}' 文件夹！")
    for category in image_categories.keys():
        folder_path = os.path.join(base_path, category)
        if os.path.isdir(folder_path):
            image_categories[category] = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_categories['claim_buttons'] or not image_categories['end_markers']:
        return None, "❌ 错误：'claim_buttons' 或 'end_markers' 文件夹是空的！"
    return image_categories, "✅ 图片资源加载成功！"

# --- 行为配置 ---
INITIAL_DELAY = 5
TIMEOUT = 1
POST_CONFIRM_DELAY = 1.5
POST_SCROLL_DELAY = 0.5
CONFIDENCE_LEVEL = 0.8
USE_GRAYSCALE = True
PAGE_LOAD_WAIT = 0.5
DEDUPE_TOLERANCE = 15
DEBUG_MODE = True
ANIMATION_WAIT = 0.1

# --- 图像识别函数 ---
def get_scaled_image(image_path):
    if image_path in IMAGE_CACHE:
        return IMAGE_CACHE[image_path]
    try:
        img = Image.open(image_path)
        if SCALE_FACTOR != 1.0:
            new_width = int(img.width * SCALE_FACTOR)
            new_height = int(img.height * SCALE_FACTOR)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        IMAGE_CACHE[image_path] = img
        return img
    except FileNotFoundError:
        if DEBUG_MODE: print(f"   - ❌ 错误: 图片文件未找到 '{image_path}'")
        return None

def find_any_on_screen(image_paths, confidence, region=None, grayscale=USE_GRAYSCALE):
    search_region_log = str(region) if region is not None else "全屏"
    for image_path in image_paths:
        scaled_image = get_scaled_image(image_path)
        if scaled_image is None: continue
        try:
            if DEBUG_MODE: print(f"   - 🔎 调试 (find_any): 正在尝试匹配模板 '{os.path.basename(image_path)}' (conf={confidence:.2f}) in region {search_region_log}")
            location = pyautogui.locateOnScreen(scaled_image, confidence=confidence, region=region, grayscale=grayscale)
            if location:
                if DEBUG_MODE: print(f"   - ✅ 调试 (find_any): 识别成功! 模板: '{os.path.basename(image_path)}'")
                return location
        except pyautogui.ImageNotFoundException:
            if DEBUG_MODE: print(f"   - ℹ️  调试 (find_any): 未找到模板 '{os.path.basename(image_path)}'。")
            continue
        except Exception as e:
            if DEBUG_MODE:
                print(f"   - ❌ 调试 (find_any): 发生意外错误 (模板: '{os.path.basename(image_path)}'), 原因: {e}")
                print(traceback.format_exc())
            continue
    return None

def find_all_on_screen(image_paths, confidence, region=None, grayscale=USE_GRAYSCALE):
    search_region_log = str(region) if region is not None else "全屏"
    all_locations = []
    for image_path in image_paths:
        scaled_image = get_scaled_image(image_path)
        if scaled_image is None: continue
        try:
            if DEBUG_MODE: print(f"   - 🔎 调试 (find_all): 正在寻找所有 '{os.path.basename(image_path)}' (conf={confidence:.2f}) in region {search_region_log}")
            locations = list(pyautogui.locateAllOnScreen(scaled_image, confidence=confidence, region=region, grayscale=grayscale))
            if locations:
                if DEBUG_MODE: print(f"   - ✅ 调试 (find_all): 找到了 {len(locations)} 个 '{os.path.basename(image_path)}' 的实例。")
                all_locations.extend(locations)
        except pyautogui.ImageNotFoundException:
            if DEBUG_MODE: print(f"   - ℹ️  调试 (find_all): 未找到任何 '{os.path.basename(image_path)}' 的实例。")
            continue
        except Exception as e:
            if DEBUG_MODE:
                print(f"   - ❌ 调试 (find_all): 发生意外错误 (模板: '{os.path.basename(image_path)}'), 原因: {e}")
                print(traceback.format_exc())
            continue
    return all_locations

def click_any_image(image_paths, timeout=TIMEOUT, region=None):
    start_time = time.time()
    while time.time() - start_time < timeout:
        location = find_any_on_screen(image_paths, CONFIDENCE_LEVEL, region=region)
        if location:
            pyautogui.click(pyautogui.center(location))
            return True
        time.sleep(0.25)
    return False

# --- 核心自动化逻辑 ---
def automation_logic(log_queue, stop_event, pause_event, image_lists):
    try:
        CLAIM_BUTTON_IMAGES = image_lists['claim_buttons']
        OK_BUTTON_IMAGES = image_lists['ok_buttons']
        NEXT_PAGE_IMAGES = image_lists['next_page_buttons']
        NEXT_PAGE_DISABLED_IMAGES = image_lists['next_page_disabled_buttons']
        END_MARKER_IMAGES = image_lists['end_markers']

        successful_claims, failed_claims_limit = 0, 0
        
        log_queue.put(("🚀 倒计时 5 秒，请切换窗口...", "info"))
        time.sleep(INITIAL_DELAY)
        
        pyautogui.press('home')
        log_queue.put((f"🤖 已回到顶部, 等待 {PAGE_LOAD_WAIT} 秒...", "info"))
        time.sleep(PAGE_LOAD_WAIT)

        page_num = 1
        while not stop_event.is_set():
            log_queue.put((f"\n📖 ****** 开始扫描第 {page_num} 页 ******", "title"))
            
            while not stop_event.is_set():
                pause_event.wait()
                
                all_raw_buttons = find_all_on_screen(CLAIM_BUTTON_IMAGES, CONFIDENCE_LEVEL, region=None)
                
                buttons_to_process = []
                if all_raw_buttons:
                    unique_centers = []
                    sorted_boxes = sorted(all_raw_buttons, key=lambda box: box.top)
                    for box in sorted_boxes:
                        center = pyautogui.center(box)
                        if not any(math.dist((center.x, center.y), (uc.x, uc.y)) < DEDUPE_TOLERANCE for uc in unique_centers):
                            unique_centers.append(center)
                    buttons_to_process = unique_centers

                if buttons_to_process:
                    log_queue.put((f"👀 发现 {len(buttons_to_process)} 个可见目标...", "info"))
                    for center_point in buttons_to_process:
                        if stop_event.is_set(): break
                        pause_event.wait()
                        
                        pyautogui.click(center_point)
                        
                        if not click_any_image(OK_BUTTON_IMAGES, timeout=1.5, region=None):
                            log_queue.put((f"   - ⚠️  警告: 点击后未找到第一个确认(OK)按钮。", "fail"))
                            continue
                        
                        time.sleep(ANIMATION_WAIT)

                        start_time = time.time()
                        was_successful = True
                        
                        while time.time() - start_time < POST_CONFIRM_DELAY:
                            if find_any_on_screen(OK_BUTTON_IMAGES, CONFIDENCE_LEVEL, region=None):
                                failed_claims_limit += 1
                                log_queue.put((f"   - ❌ 失败 (已达上限): {failed_claims_limit}", "fail"))
                                log_queue.put(("   - ℹ️  检测到第二个OK按钮, 点击关闭...", "info"))
                                click_any_image(OK_BUTTON_IMAGES, timeout=1.0, region=None)
                                was_successful = False
                                break
                            time.sleep(0.1)

                        if was_successful:
                            successful_claims += 1
                            log_queue.put((f"   - ✅ 成功: {successful_claims}", "success"))
                        
                        time.sleep(ANIMATION_WAIT)
                else:
                    log_queue.put(("   - 当前视野未发现目标。", "info"))

                if find_any_on_screen(END_MARKER_IMAGES, CONFIDENCE_LEVEL, region=None):
                    log_queue.put(("🏁 本页内容扫描完毕！", "info"))
                    break

                log_queue.put(("↓  向下翻页...", "info"))
                pyautogui.press('pagedown')
                time.sleep(POST_SCROLL_DELAY)
            
            if stop_event.is_set(): break
            
            log_queue.put(("\n🧐 正在寻找翻页按钮...", "info"))
            if find_any_on_screen(NEXT_PAGE_DISABLED_IMAGES, CONFIDENCE_LEVEL, region=None):
                log_queue.put(("✋ 已到最后一页！任务结束。", "summary"))
                break
            
            if click_any_image(NEXT_PAGE_IMAGES, timeout=3.0, region=None):
                page_num += 1
                log_queue.put(("✅ 成功翻页！", "success"))
                time.sleep(PAGE_LOAD_WAIT)
                pyautogui.press('home')
                time.sleep(0.5)
            else:
                log_queue.put(("🤷‍ 未找到“下一页”按钮，任务结束。", "summary"))
                break
        
        summary = (f"\n🎉 完成！\n成功: {successful_claims} | 失败: {failed_claims_limit}", "summary")
        log_queue.put(summary)
    
    except Exception as e:
        if isinstance(e, pyautogui.FailSafeException):
            log_queue.put(("🛡️ 安全保护已触发！", "fail"))
            log_queue.put(("鼠标移动到屏幕角落时程序会自动停止。", "info"))
        else:
            logging.error(f"自动化线程出错: {traceback.format_exc()}")
            log_queue.put((f"😱 糟糕，出错了！\n{e}", "error"))

# --- GUI 应用程序 ---
class App:
    def __init__(self, root, image_lists):
        self.root = root
        self.image_lists = image_lists
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.automation_thread = None
        
        # --- 【新增】署名 ---
        self.root.title("PT 自动认领小助手 by 7owel")
        try:
            icon_path = resource_path("app.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"警告: 未能加载图标文件 'app.ico'。原因: {e}")
        
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#2E2E2E")

        self.title_font = font.Font(family="Microsoft YaHei", size=11, weight="bold")
        self.log_font = font.Font(family="Microsoft YaHei", size=9)
        self.button_font = font.Font(family="Microsoft YaHei", size=10, weight="bold")
        self.colors = {"info": "#D4D4D4", "success": "#6A9955", "fail": "#F44336", "error": "#F44336", "summary": "#4CAF50", "title": "#569CD6"}
        
        # --- 【新增】署名 ---
        self.title_label = tk.Label(root, text="PT 自动认领小助手 ✨ by 7owel", font=self.title_font, fg="#4CAF50", bg="#2E2E2E")
        self.title_label.pack(pady=(10, 5))

        self.log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=12, width=50, bg="#1E1E1E", fg=self.colors["info"], font=self.log_font, relief="flat", bd=5)
        self.log_area.pack(pady=5, padx=10, fill="both", expand=True)
        for tag, color in self.colors.items(): self.log_area.tag_config(tag, foreground=color)
        welcome_message = ("欢迎使用！ (F6=暂停/继续, F7=停止)\n\n【准备步骤】:\n1. 打开PT站点的个人资料页面。\n2. 找到并展开“正在做种”列表。\n3. 确保浏览器缩放为100%。\n\n点击“开始”启动任务。")
        self.log_area.insert(tk.END, welcome_message)
        self.log_area.config(state="disabled")
        
        self.button_frame_top = tk.Frame(root, bg="#2E2E2E")
        self.button_frame_top.pack(pady=(5, 2))
        self.button_frame_bottom = tk.Frame(root, bg="#2E2E2E")
        self.button_frame_bottom.pack(pady=(0, 10))

        self.start_button = tk.Button(self.button_frame_top, text="▶ 开始", command=self.start_automation, font=self.button_font, bg="#4CAF50", fg="white", relief="flat", width=12)
        self.start_button.pack(side="left", padx=5)
        self.pause_button = tk.Button(self.button_frame_top, text="⏸️ 暂停 (F6)", command=self.toggle_pause, font=self.button_font, bg="#FFC107", fg="black", relief="flat", width=12, state="disabled")
        self.pause_button.pack(side="left", padx=5)
        self.stop_button = tk.Button(self.button_frame_bottom, text="■ 停止 (F7)", command=self.stop_automation, font=self.button_font, bg="#F44336", fg="white", relief="flat", width=26, state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth(); height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}-10+40")
        self.root.resizable(False, False)
        
        # --- 【新增】设置和清理全局快捷键 ---
        self.setup_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.update_ui()

    def setup_hotkeys(self):
        keyboard.add_hotkey('f6', self.toggle_pause)
        keyboard.add_hotkey('f7', self.stop_automation)

    def on_closing(self):
        keyboard.unhook_all() # 清理快捷键监听
        self.root.destroy()

    def add_log(self, message, tag="info"):
        is_at_bottom = self.log_area.yview()[1] == 1.0
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n", tag)
        self.log_area.config(state="disabled")
        if is_at_bottom: self.log_area.see(tk.END)

    def start_automation(self):
        self.stop_event.clear(); self.pause_event.set()
        self.log_area.config(state="normal"); self.log_area.delete('1.0', tk.END); self.log_area.config(state="disabled")
        self.log_queue.put(("\n" + "="*20, "title"))
        self.log_queue.put(("🟢 任务已启动...", "info"))
        self.start_button.config(state="disabled", bg="#9E9E9E")
        self.pause_button.config(state="normal", text="⏸️ 暂停 (F6)", bg="#FFC107")
        self.stop_button.config(state="normal", bg="#F44336")
        self.automation_thread = threading.Thread(target=automation_logic, args=(self.log_queue, self.stop_event, self.pause_event, self.image_lists), daemon=True)
        self.automation_thread.start()

    def toggle_pause(self):
        if self.automation_thread and self.automation_thread.is_alive() and self.pause_button['state'] == 'normal':
            if self.pause_event.is_set():
                self.pause_event.clear(); self.add_log("⏸️ 任务已暂停... (F6)", "info"); self.pause_button.config(text="▶️ 继续 (F6)", bg="#8BC34A")
            else:
                self.pause_event.set(); self.add_log("▶️ 任务已继续！ (F6)", "info"); self.pause_button.config(text="⏸️ 暂停 (F6)", bg="#FFC107")

    def stop_automation(self):
        if self.automation_thread and self.automation_thread.is_alive() and self.stop_button['state'] == 'normal':
            self.stop_event.set(); self.pause_event.set()
            self.log_queue.put(("🔴 正在发送停止信号... (F7)", "fail"))
            self.stop_button.config(state="disabled", bg="#9E9E9E")
            self.pause_button.config(state="disabled", bg="#9E9E9E")

    def update_ui(self):
        try:
            while not self.log_queue.empty():
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple): message, tag = item
                else: message, tag = item, "info"
                self.add_log(message, tag)
        finally:
            is_running = self.automation_thread and self.automation_thread.is_alive()
            if not is_running and self.start_button["state"] == "disabled":
                self.start_button.config(state="normal", bg="#4CAF50")
                self.pause_button.config(state="disabled", text="⏸️ 暂停 (F6)", bg="#9E9E9E")
                self.stop_button.config(state="normal", bg="#F44336")
            self.root.after(200, self.update_ui)

if __name__ == "__main__":
    try:
        # --- 【新增】署名 ---
        print("="*60 + "\n      欢迎使用 PT 自动认领小助手 ✨ by 7owel\n" + "="*60)
        print("\n【准备步骤】:\n  1. 打开PT站点的个人资料页面。\n  2. 找到并展开“正在做种”列表，确保列表内容可见。\n  3. 确保你的浏览器缩放比例设置为 100%。\n     (可以在浏览器设置中查找“缩放”或使用 Ctrl+0 重置)\n\n" + "-"*60)
        print(f"检测到当前系统缩放为: {int(CURRENT_SCALING * 100)}%")
        print(f"基准截图缩放设定为: {int(BASELINE_SCALING * 100)}%")
        print(f"运行时图片缩放因子: {SCALE_FACTOR:.2f}")
        print("-"*60 + "\n")
        image_lists, msg = load_images_from_folders()
        print(msg)
        if image_lists:
            print("\n【✅ 准备就绪】\n  请在弹出的GUI窗口上操作【开始/暂停/停止】。\n  本窗口将同步显示详细调试日志。")
            root = tk.Tk()
            app = App(root, image_lists)
            root.mainloop()
        else: 
            print("\n程序无法启动。请检查 'images' 文件夹和其中的图片是否完整。")
            input("按 Enter 键退出...")
    except Exception as e:
        logging.critical(f"脚本发生了一个意料之外的严重错误: {e}\n{traceback.format_exc()}")
        input(f"\n😱 啊哦！脚本遇到了一点麻烦: {e}")