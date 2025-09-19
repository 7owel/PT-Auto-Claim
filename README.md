# PT 自动认领小助手 by 7owel

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

一款为PT（Private Tracker）用户设计的智能GUI工具，旨在自动化执行个人资料页面中的“认领做种”任务，解放双手。

---

## ✨ 核心特性

- **智能图像识别**: 基于`pyautogui`，精准定位并点击相关按钮，完成认领流程。
- **全自动翻页**: 能够自动检测页面底部并点击“下一页”，实现对所有页面的全覆盖。
- **动态缩放适配**: **独创的自适应缩放机制**，能够自动检测用户Windows系统的显示缩放比例（如100%, 125%, 150%, 175%），并实时缩放截图模板，从而完美适配不同分辨率（1080p, 2K, 4K）和高DPI屏幕，无需为不同环境准备多套截图。
- **健壮的逻辑**: 优化了操作时序，加入了智能的“动态等待”和UI动画延迟，有效避免了因网络延迟或页面动画导致的“抢跑”和“误判”问题。
- **友好的图形用户界面 (GUI)**:
    - 基于`tkinter`构建，界面简洁，操作直观。
    - 实时日志输出，任务进度一目了然。
    - 提供“开始”、“暂停/继续”、“停止”控制功能。
- **全局快捷键**:
    - **F6**: 快速暂停或继续任务。
    - **F7**: 快速停止任务。
- **跨平台兼容性**: 使用Python编写，核心依赖库均为跨平台，具备移植到其他操作系统的潜力。

## 🚀 如何使用

1.  **下载**: 前往 [Releases](https://github.com/7owel/PT-Auto-Claim/releases) 页面，下载最新的`.exe`可执行文件。
2.  **准备**:
    - 将下载的`.exe`文件与`images`文件夹放在**同一个目录**下。
    - 确保`images`文件夹内包含了针对你所使用PT站点的按钮截图。
3.  **运行前设置**:
    - 打开你的PT站点，并登录。
    - 导航到你的**个人资料页面** (Profile)。
    - 找到并**展开“正在做种” (Seeding)** 的列表，确保列表内容在屏幕上可见。
    - **重要**: 确保你的浏览器缩放比例为 **100%** (可通过 `Ctrl + 0` 快速重置)。
4.  **开始任务**:
    - 双击运行 `PT自动认领小助手.exe`。
    - 阅读GUI窗口上的指引。
    - 点击 **▶ 开始** 按钮，脚本将有5秒倒计时，请在此期间切换到你的浏览器窗口。
    - 现在，把手从鼠标上移开，享受自动化吧！

## 🛠️ 从源码运行 (开发者)

如果你希望从源代码运行或进行二次开发，请按以下步骤操作：

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/7owel/PT-Auto-Claim.git
    cd PT-Auto-Claim
    ```
2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **运行脚本**:
    ```bash
    python pt_auto_claim.py
    ```
4.  **打包 (使用PyInstaller)**:
    ```bash
    pyinstaller --name "PT自动认领小助手" --onefile --windowed --icon="app.ico" --add-data "images;images" pt_auto_claim.py
    ```
    
## 📄 许可 (License)

本项目采用 [MIT License](LICENSE) 开源。
