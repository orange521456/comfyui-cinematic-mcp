"""
Cinematic Prompt Composer 核心逻辑

五层视觉分层合成：
  1. LIGHT  光线 — 光源类型、方向、氛围
  2. LENS   镜头 — 焦段、机位、景深
  3. COLOR  色彩 — 调色风格、色温、饱和度
  4. TEXTURE 材质 — 表面质感、细节纹理
  5. STORY  叙事 — 构图、叙事意图

合成策略：逐层链式替换 {prompt} 占位符，等价于 SDXL Prompt Styler 连续应用 5 个风格。
负向提示词：逐层收集去重合并。
"""

import json
import os
from typing import Optional

# 五层定义：层名 → 预设文件名
LAYER_FILES = {
    "light": "cinematic_light.json",
    "lens": "cinematic_lens.json",
    "color": "cinematic_color.json",
    "texture": "cinematic_texture.json",
    "story": "cinematic_story.json",
}

# 层的默认风格（未指定时使用）
DEFAULT_STYLES = {
    "light": "light_soft_diffuse",
    "lens": "lens_85mm_portrait",
    "color": "color_teal_orange",
    "texture": "texture_real_skin",
    "story": "story_rule_of_thirds",
}

# 合成时的层顺序（影响 prompt 拼接顺序）
LAYER_ORDER = ["light", "lens", "color", "texture", "story"]

_PRESETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")


def _load_layer_presets(layer: str) -> list:
    """加载某一层的所有预设"""
    filename = LAYER_FILES.get(layer)
    if not filename:
        return []
    filepath = os.path.join(_PRESETS_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _find_preset(layer: str, style_name: str) -> Optional[dict]:
    """在某一层中按名称查找预设"""
    for preset in _load_layer_presets(layer):
        if preset["name"] == style_name:
            return preset
    return None


def _dedup_tokens(*prompts: str) -> str:
    """合并多个提示词，去重逗号分隔的 token"""
    seen = []
    for p in prompts:
        if not p:
            continue
        for token in p.split(","):
            token = token.strip()
            if token and token not in seen:
                seen.append(token)
    return ", ".join(seen)


def _apply_layer(base_positive: str, base_negative: str,
                layer: str, style_name: Optional[str] = None,
                custom: Optional[str] = None) -> tuple:
    """
    应用单层风格到当前 prompt。

    - 若 custom 提供：直接追加 custom 描述（不走预设）
    - 若 style_name 提供：查找预设并替换 {prompt} 占位符
    - 若两者都未提供：使用该层默认风格
    """
    presets = _load_layer_presets(layer)
    if not presets:
        return base_positive, base_negative

    # 确定使用哪个预设
    target = None
    if custom:
        # 自定义描述：直接作为该层贡献追加
        new_positive = f"{base_positive}, {custom}" if base_positive else custom
        return new_positive, base_negative

    if not style_name:
        style_name = DEFAULT_STYLES.get(layer, "")

    target = _find_preset(layer, style_name)
    if not target:
        # 预设不存在，尝试用第一个
        target = presets[0] if presets else None
        if not target:
            return base_positive, base_negative

    # 替换 {prompt} 占位符
    template_positive = target.get("prompt", "{prompt}")
    new_positive = template_positive.replace("{prompt}", base_positive)

    # 合并负向提示词
    template_negative = target.get("negative_prompt", "")
    new_negative = _dedup_tokens(base_negative, template_negative)

    return new_positive, new_negative


class CinematicComposer:
    """五层电影级提示词合成器"""

    def __init__(self, presets_dir: Optional[str] = None):
        global _PRESETS_DIR
        if presets_dir:
            _PRESETS_DIR = presets_dir

    def list_presets(self, layer: Optional[str] = None) -> dict:
        """
        列出可用预设。

        Args:
            layer: 指定层名(light/lens/color/texture/story)，None 则返回全部
        Returns:
            {layer: [{name, prompt_preview, negative_preview}, ...]}
        """
        layers = [layer] if layer else LAYER_ORDER
        result = {}
        for ly in layers:
            presets = _load_layer_presets(ly)
            result[ly] = [
                {
                    "name": p["name"],
                    "prompt_preview": p["prompt"][:80] + "..." if len(p["prompt"]) > 80 else p["prompt"],
                    "negative_preview": p.get("negative_prompt", "")[:60],
                }
                for p in presets
            ]
        return result

    def compose(
        self,
        subject: str,
        scene: str = "",
        mood: str = "",
        light_style: Optional[str] = None,
        lens_style: Optional[str] = None,
        color_style: Optional[str] = None,
        texture_style: Optional[str] = None,
        story_style: Optional[str] = None,
        light_custom: Optional[str] = None,
        lens_custom: Optional[str] = None,
        color_custom: Optional[str] = None,
        texture_custom: Optional[str] = None,
        story_custom: Optional[str] = None,
        negative_prompt: str = "",
    ) -> dict:
        """
        合成五层电影级提示词（仅输出文本，不生图）。

        Args:
            subject: 主体描述（人物/建筑/物体）
            scene: 场景环境
            mood: 情绪氛围
            light_style: 光线层预设名（如 light_golden_hour）
            lens_style: 镜头层预设名（如 lens_35mm_anamorphic）
            color_style: 色彩层预设名（如 color_teal_orange）
            texture_style: 材质层预设名（如 texture_real_skin）
            story_style: 叙事层预设名（如 story_rule_of_thirds）
            light_custom: 光线自定义描述（覆盖预设）
            lens_custom: 镜头自定义描述
            color_custom: 色彩自定义描述
            texture_custom: 材质自定义描述
            story_custom: 叙事自定义描述
            negative_prompt: 全局负向提示词

        Returns:
            {
                "positive_prompt": str,   # 合成后的正向提示词
                "negative_prompt": str,   # 合成后的负向提示词
                "layers_applied": list,   # 已应用的层及风格
                "layer_count": int,
            }
        """
        # 1. 构建基础 prompt
        base_parts = [p.strip() for p in [subject, scene, mood] if p and p.strip()]
        positive = ", ".join(base_parts)
        negative = negative_prompt.strip()

        # 2. 逐层应用
        styles = {
            "light": light_style,
            "lens": lens_style,
            "color": color_style,
            "texture": texture_style,
            "story": story_style,
        }
        customs = {
            "light": light_custom,
            "lens": lens_custom,
            "color": color_custom,
            "texture": texture_custom,
            "story": story_custom,
        }

        layers_applied = []
        for layer in LAYER_ORDER:
            positive, negative = _apply_layer(
                positive, negative,
                layer=layer,
                style_name=styles.get(layer),
                custom=customs.get(layer),
            )
            applied_style = customs.get(layer) or styles.get(layer) or DEFAULT_STYLES.get(layer, "default")
            layers_applied.append({
                "layer": layer,
                "style": applied_style,
                "type": "custom" if customs.get(layer) else "preset",
            })

        return {
            "positive_prompt": positive,
            "negative_prompt": negative,
            "layers_applied": layers_applied,
            "layer_count": len(layers_applied),
        }

    def refine_layer(
        self,
        base_positive: str,
        base_negative: str,
        modify_layer: str,
        adjust_content: str,
    ) -> dict:
        """
        分层精修：仅修改单一维度的提示词。

        Args:
            base_positive: 上一轮的正向提示词
            base_negative: 上一轮的负向提示词
            modify_layer: 要修改的层(light/lens/color/texture/story)
            adjust_content: 修改描述

        Returns:
            {"positive_prompt": str, "negative_prompt": str}
        """
        if modify_layer not in LAYER_FILES:
            return {
                "positive_prompt": base_positive,
                "negative_prompt": base_negative,
                "error": f"Unknown layer: {modify_layer}. Valid: {list(LAYER_FILES.keys())}",
            }

        positive, negative = _apply_layer(
            base_positive, base_negative,
            layer=modify_layer,
            custom=adjust_content,
        )
        return {
            "positive_prompt": positive,
            "negative_prompt": negative,
            "modified_layer": modify_layer,
        }


def list_all_presets() -> dict:
    """快捷函数：列出全部五层预设"""
    composer = CinematicComposer()
    return composer.list_presets()
