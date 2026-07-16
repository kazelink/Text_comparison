# 📝 文本对比工具 (Text Comparison Tool)

一款轻量级的字符级文本对比工具，基于 Python + Tkinter 构建。无需安装任何第三方依赖，支持打包为单文件 EXE 直接运行。

适用于文档校对、文案审核、翻译对照等场景。

---

## ✨ 功能特性

- **字符级对比** — 基于 `difflib.SequenceMatcher`，精确到每个字符的差异检测
- **差异可视化** — 新增内容以 🟢 绿色加粗显示，删除内容以 🔴 红色删除线显示
- **逐项导航** — 通过「上一项 / 下一项」按钮逐个浏览差异
- **接受 / 拒绝** — 对每处差异可选择接受修订或保留原文
- **源文定位** — 点击「定位」按钮，在原始文本和修订文本中高亮对应位置
- **点击跳转** — 在差异预览区点击任意差异项即可跳转选中
- **鼠标拖选** — 差异预览区支持鼠标滑选，选中部分蓝色高亮
- **一键粘贴** — 每个输入框提供「粘贴」按钮，快速从剪贴板导入文本
- **高 DPI 适配** — 自动适配高分辨率屏幕
- **零依赖** — 仅使用 Python 标准库，无需安装第三方包

---

## 🚀 快速开始

### 直接运行

确保系统已安装 Python 3.8+：

```bash
python src/main.py
```

### 使用打包好的 EXE

从 [Releases](../../releases) 下载最新的 `文本校对.exe`，双击即可运行，无需 Python 环境。

---

## 📖 使用方法

1. 在左侧 **「原始文本」** 框中输入或粘贴原始内容
2. 在右侧 **「修订文本」** 框中输入或粘贴修改后的内容
3. 点击 **「开始对比」**，差异预览区将展示所有差异
4. 使用 **「上一项 / 下一项」** 逐个浏览差异
5. 对每处差异选择 **「接受」**（采用修订版）或 **「拒绝」**（保留原文）
6. 点击 **「定位」** 可在原始/修订文本框中高亮定位当前差异
7. 处理完毕后，状态栏显示处理结果

---

## 🔧 打包构建

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 安装 PyInstaller
pip install pyinstaller
```

### 执行打包

```bash
pyinstaller --clean 文本校对.spec
```

打包完成后，EXE 文件位于 `dist/文本校对.exe`。

### 打包优化

当前 spec 文件已包含以下优化措施以减小体积：

- 排除未使用的标准库模块（`unittest`、`email`、`http`、`asyncio` 等）
- 字节码优化级别设为 2（移除 docstring 和 assert）
- 开启 `strip` 去除调试符号
- 开启 `upx` 压缩（需系统安装 [UPX](https://github.com/upx/upx/releases)）

---

## 📁 项目结构

```
Text_comparison/
├── src/
│   ├── main.py          # 主程序
│   └── hook.py          # PyInstaller 运行时钩子
├── assets/
│   └── 文档对比.ico      # 应用图标
├── 文本校对.spec          # PyInstaller 打包配置
├── pyinstaller.txt       # 打包命令参考
└── README.md
```

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| GUI | Tkinter / ttk |
| 对比算法 | difflib.SequenceMatcher |
| 打包工具 | PyInstaller |

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。
