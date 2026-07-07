"""Streamlit entry point for Repo Insight Agent."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, AuthenticationError, RateLimitError

from repo_insight.analyzer import analyze_repository
from repo_insight.config import Settings
from repo_insight.git_service import CloneError, RepositoryURLError, clone_repository
from repo_insight.models import RepositorySnapshot
from repo_insight.scanner import scan_repository

load_dotenv()
SETTINGS = Settings.from_env()

st.set_page_config(page_title="Repo Insight Agent", page_icon="🔎", layout="wide")
st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 2rem;}
      [data-testid="stMetricValue"] {font-size: 1.7rem;}
      .subtitle {color: #64748b; margin-top: -0.6rem; margin-bottom: 1.4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _remove_workspace() -> None:
    workspace = st.session_state.get("workspace")
    if workspace:
        shutil.rmtree(workspace, ignore_errors=True)
    st.session_state.pop("workspace", None)
    st.session_state.pop("snapshot", None)
    st.session_state.pop("report", None)


def _scan(url: str) -> RepositorySnapshot:
    _remove_workspace()
    workspace = Path(tempfile.mkdtemp(prefix="repo-insight-"))
    st.session_state.workspace = str(workspace)
    destination = workspace / "repository"
    normalized_url, repository_name = clone_repository(
        url, destination, SETTINGS.clone_timeout_seconds
    )
    return scan_repository(destination, normalized_url, repository_name, SETTINGS)


def _format_api_error(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return "API Key 无效或无权访问该模型，请检查后重试。"
    if isinstance(error, RateLimitError):
        return "API 请求达到速率或额度限制，请稍后重试并检查账户额度。"
    if isinstance(error, APIConnectionError):
        return "无法连接阿里云百炼 API，请检查网络、地域和 Base URL 后重试。"
    if isinstance(error, APIError):
        return f"阿里云百炼 API 返回错误：{error}"
    return str(error)


st.title("🔎 Repo Insight Agent")
st.markdown(
    '<div class="subtitle">把 GitHub 仓库变成一份可读的项目地图和学习路线。</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("分析设置")
    api_key = st.text_input(
        "阿里云百炼 API Key",
        value=os.getenv("DASHSCOPE_API_KEY", ""),
        type="password",
        help="仅用于本次服务端 API 请求，不会写入项目文件。",
    )
    model = st.text_input("模型", value=SETTINGS.default_model)
    base_url = st.text_input("API Base URL", value=SETTINGS.api_base_url)
    st.caption("默认使用 qwen3.7-plus；API Key、模型和 Base URL 必须属于同一百炼地域。")
    if st.button("清理临时仓库", use_container_width=True):
        _remove_workspace()
        st.success("临时仓库与当前结果已清理。")

with st.form("repository_form"):
    url = st.text_input(
        "GitHub 仓库 URL",
        placeholder="https://github.com/owner/repository",
        help="当前版本支持公开的 GitHub HTTPS 仓库。",
    )
    scan_clicked = st.form_submit_button("克隆并扫描", type="primary", use_container_width=True)

if scan_clicked:
    if not url.strip():
        st.warning("请先输入 GitHub 仓库 URL。")
    else:
        try:
            with st.status("正在分析仓库…", expanded=True) as status:
                st.write("正在浅克隆默认分支…")
                snapshot = _scan(url)
                st.write("正在扫描目录、README、依赖和代表性源码…")
                st.session_state.snapshot = snapshot
                st.session_state.pop("report", None)
                status.update(label="仓库扫描完成", state="complete", expanded=False)
        except (RepositoryURLError, CloneError, ValueError) as error:
            _remove_workspace()
            st.error(str(error))
        except Exception as error:  # Keep the UI useful for unexpected Git/filesystem failures.
            _remove_workspace()
            st.exception(error)

snapshot: RepositorySnapshot | None = st.session_state.get("snapshot")
if snapshot:
    st.subheader(snapshot.name)
    metric_columns = st.columns(4)
    metric_columns[0].metric("文件", snapshot.total_files)
    metric_columns[1].metric("目录", snapshot.total_directories)
    metric_columns[2].metric("依赖文件", len(snapshot.dependency_files))
    metric_columns[3].metric("源码样本", len(snapshot.source_samples))

    scan_tab, readme_tab, dependencies_tab, report_tab = st.tabs(
        ["目录结构", "README", "依赖识别", "AI 报告"]
    )
    with scan_tab:
        if snapshot.truncated_tree:
            st.info("为保持页面和模型上下文紧凑，目录树已按配置上限截断。")
        st.code(snapshot.directory_tree, language="text")
    with readme_tab:
        if snapshot.readme_content:
            st.caption(snapshot.readme_path)
            st.markdown(snapshot.readme_content)
        else:
            st.info("未发现 README。")
    with dependencies_tab:
        if snapshot.dependency_files:
            for path, content in snapshot.dependency_files.items():
                with st.expander(path):
                    st.code(content or "[文件为空或无法读取]", language="text")
        else:
            st.info("未识别到常见依赖或构建文件。")
    with report_tab:
        if st.button("生成 AI 洞察报告", type="primary", use_container_width=True):
            try:
                with st.spinner("模型正在梳理架构和学习路线…"):
                    st.session_state.report = analyze_repository(
                        snapshot, api_key, model, base_url, SETTINGS
                    )
            except Exception as error:
                st.error(_format_api_error(error))

        report = st.session_state.get("report")
        if report:
            st.markdown(report)
            st.download_button(
                "下载 Markdown 报告",
                data=report,
                file_name=f"{snapshot.name}-insight.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.info("扫描结果已就绪。填写 API Key 后点击上方按钮生成报告。")
