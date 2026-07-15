"""
Cinematic Prompt Composer - 五层视觉提示词合成器
仅输出优化后的提示词文本，可供任意生图模型使用。
五层：光线 LIGHT / 镜头 LENS / 色彩 COLOR / 叙事 STORY / 材质 TEXTURE
"""
from .composer import CinematicComposer, list_all_presets

__all__ = ["CinematicComposer", "list_all_presets"]
