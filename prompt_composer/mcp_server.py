"""
Cinematic Prompt Composer MCP Server

仅输出提示词文本的 MCP 服务，供 Trae Agent / 其他生图模型使用。
五层视觉分层：光线 / 镜头 / 色彩 / 材质 / 叙事

启动：
    python mcp_server.py          # stdio 模式（Trae 本地 MCP）
    python mcp_server.py --http   # SSE 模式（端口 9005）
"""

import sys
import os
import json
import argparse

# 确保能 import 同级包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from composer import CinematicComposer
from mcp.server.fastmcp import FastMCP

# host/port 通过环境变量注入（容器内需 0.0.0.0）
_mcp_host = os.environ.get("FASTMCP_HOST", "127.0.0.1")
_mcp_port = int(os.environ.get("FASTMCP_PORT", "9005"))
mcp = FastMCP("cinematic_prompt_composer", host=_mcp_host, port=_mcp_port)
composer = CinematicComposer()


@mcp.tool()
def cinematic_prompt_compose(
    subject: str,
    scene: str = "",
    mood: str = "",
    light_style: str = "",
    lens_style: str = "",
    color_style: str = "",
    texture_style: str = "",
    story_style: str = "",
    light_custom: str = "",
    lens_custom: str = "",
    color_custom: str = "",
    texture_custom: str = "",
    story_custom: str = "",
    negative_prompt: str = "",
) -> str:
    """
    五层电影级提示词合成（仅输出文本，不生图）。

    将主体/场景/情绪按光线/镜头/色彩/材质/叙事五层分层优化，
    输出可直接用于任意生图模型的标准化提示词。

    Args:
        subject: 主体描述（人物/建筑/物体），必填
        scene: 场景环境（可选）
        mood: 情绪氛围（可选）
        light_style: 光线预设名（如 light_golden_hour），留空用默认
        lens_style: 镜头预设名（如 lens_35mm_anamorphic）
        color_style: 色彩预设名（如 color_teal_orange）
        texture_style: 材质预设名（如 texture_real_skin）
        story_style: 叙事预设名（如 story_rule_of_thirds）
        light_custom: 光线自定义描述（覆盖预设）
        lens_custom: 镜头自定义描述
        color_custom: 色彩自定义描述
        texture_custom: 材质自定义描述
        story_custom: 叙事自定义描述
        negative_prompt: 全局负向提示词

    Returns:
        JSON 字符串，包含 positive_prompt / negative_prompt / layers_applied
    """
    result = composer.compose(
        subject=subject, scene=scene, mood=mood,
        light_style=light_style or None,
        lens_style=lens_style or None,
        color_style=color_style or None,
        texture_style=texture_style or None,
        story_style=story_style or None,
        light_custom=light_custom or None,
        lens_custom=lens_custom or None,
        color_custom=color_custom or None,
        texture_custom=texture_custom or None,
        story_custom=story_custom or None,
        negative_prompt=negative_prompt,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def list_cinematic_presets(layer: str = "") -> str:
    """
    列出五层视觉预设库。

    Args:
        layer: 指定层名(light/lens/color/texture/story)，留空返回全部

    Returns:
        JSON 字符串，每层包含 name / prompt_preview / negative_preview
    """
    result = composer.list_presets(layer or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def layered_prompt_refine(
    base_positive: str,
    modify_layer: str,
    adjust_content: str,
    base_negative: str = "",
) -> str:
    """
    分层精修提示词：仅修改单一视觉维度，无需重写全部提示词。

    Args:
        base_positive: 上一轮的正向提示词
        modify_layer: 要修改的层(light/lens/color/texture/story)
        adjust_content: 修改描述，如"将平光改为日落侧逆光"
        base_negative: 上一轮的负向提示词（可选）

    Returns:
        JSON 字符串，包含修改后的 positive_prompt / negative_prompt
    """
    result = composer.refine_layer(
        base_positive=base_positive,
        base_negative=base_negative,
        modify_layer=modify_layer,
        adjust_content=adjust_content,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinematic Prompt Composer MCP Server")
    parser.add_argument("--http", action="store_true", help="以 SSE HTTP 模式运行（默认 stdio）")
    parser.add_argument("--port", type=int, default=9005, help="HTTP 模式端口（覆盖环境变量）")
    args = parser.parse_args()

    # 覆盖端口（若通过命令行传入）
    if args.port != _mcp_port:
        mcp.settings.port = args.port

    if args.http:
        # SSE 模式 — host/port 已在 FastMCP 构造时设置
        mcp.run(transport="sse")
    else:
        mcp.run()
