# Repo Insight Agent

Repo Insight Agent 是一个使用 Python、Streamlit 和通义千问构建的 GitHub 仓库阅读助手。项目通过 OpenAI Python SDK 调用阿里云百炼的 OpenAI-compatible API。输入公开 GitHub 仓库 URL 后，它会进行浅克隆，扫描目录结构，读取 README 和常见依赖文件，再结合少量代表性源码生成中文项目概览、目录解释与学习路线。

## 功能

- 校验 GitHub HTTPS URL，并使用参数化 Git 命令执行浅克隆
- 忽略 `.git`、`node_modules`、构建产物和常见缓存目录
- 展示有深度和条目上限的目录树
- 自动查找根目录优先的 README
- 识别 Python、Node.js、Go、Rust、Java、Ruby、PHP、.NET 等生态的依赖/构建文件
- 选择入口文件优先的代表性源码，构建有字符上限的模型上下文
- 使用通义千问 Chat API 生成 Markdown 洞察报告并支持下载
- 防止读取符号链接指向的仓库外文件，并在提示词中隔离仓库内的提示注入文本

## 项目结构

```text
repo-insight-agent/
├── app.py                         # Streamlit 页面与交互流程
├── repo_insight/
│   ├── __init__.py
│   ├── analyzer.py                # 上下文构建与千问调用
│   ├── config.py                  # 模型默认值、扫描上限、文件清单
│   ├── git_service.py             # URL 校验与安全浅克隆
│   ├── models.py                  # 仓库快照数据模型
│   └── scanner.py                 # 目录、README、依赖、源码扫描
├── tests/
│   ├── test_analyzer.py
│   ├── test_git_service.py
│   └── test_scanner.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

## 环境要求

- Python 3.10+
- Git
- 可用的阿里云百炼 API Key

## 本地运行

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

macOS / Linux：

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

把 `.env` 中的 `DASHSCOPE_API_KEY` 换成真实值，也可以直接在页面侧边栏临时输入。默认模型是 `qwen3.7-plus`，可通过 `QWEN_MODEL` 或页面输入框覆盖。国内按量计费默认 API 地址是 `https://dashscope.aliyuncs.com/compatible-mode/v1`；如果百炼控制台提供了业务空间专属域名，请通过 `DASHSCOPE_BASE_URL` 或页面输入框替换，并确保 API Key 与地域一致。

## 使用流程

1. 输入形如 `https://github.com/owner/repository` 的公开仓库地址。
2. 点击“克隆并扫描”，核对目录、README 和依赖识别结果。
3. 在侧边栏填写阿里云百炼 API Key，点击“生成 AI 洞察报告”。
4. 在页面阅读或下载 Markdown 报告。

## 测试与静态检查

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
```

测试不会真实克隆远程仓库，也不会调用千问 API。

## 当前边界

- 仅接受公开 GitHub HTTPS 仓库；私有仓库认证尚未加入。
- 这是面向快速理解的有界采样，不会把整个大型仓库发送给模型。
- 仓库会克隆到操作系统临时目录；再次扫描或点击“清理临时仓库”会清除当前副本。
- 扫描器不会执行目标仓库中的任何代码、脚本或安装命令。
