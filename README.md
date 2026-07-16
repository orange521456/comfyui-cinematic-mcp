# Cinematic MCP — 电影级五层视觉生成系统

一套面向 AI Agent 的**电影级五层视觉生成 Skill**，基于 Docker 容器化部署，通过 MCP（Model Context Protocol）协议对外提供标准化工具，支持本地 ComfyUI 出图与纯提示词输出两种模式。

五层视觉体系：**光线 LIGHT / 镜头 LENS / 色彩 COLOR / 材质 TEXTURE / 叙事 STORY**，每层独立可控，可分层精修，可自由组合，内置 36 个专业预设。

---

## 目录

- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [环境要求](#环境要求)
- [快速开始（Agent 可直接执行）](#快速开始agent-可直接执行)
- [配置详解](#配置详解)
- [MCP 工具参考](#mcp-工具参考)
- [五层视觉预设库](#五层视觉预设库)
- [使用示例](#使用示例)
- [接入 Trae / Cursor / Claude Desktop](#接入-trae--cursor--claude-desktop)
- [常见问题](#常见问题)
- [项目结构](#项目结构)
- [扩展自定义预设](#扩展自定义预设)
- [许可证](#许可证)

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **五层视觉拆解** | 光线/镜头/色彩/材质/叙事分层独立控制，匹配电影工业流程 |
| **两种输出模式** | A. 直接调用 ComfyUI 出图  B. 仅输出优化提示词文本（供 Midjourney/即梦/Flux 等使用） |
| **分层精修** | 基于上轮结果单独调整某一维度，无需重写全部提示词 |
| **MCP 标准协议** | Trae/Cursor/Claude Desktop 等客户端零障碍接入 |
| **本地离线运行** | Docker 容器化，无第三方 API 调用，无额度限制 |
| **GPU 加速** | NVIDIA GPU 直通，支持 Blackwell 架构（RTX 5060 sm_120） |
| **36 个专业预设** | 涵盖黄金时刻、青橙调色、变形宽银幕、真实皮肤质感等商业视觉风格 |
| **可复用视觉标准** | 所有参数持久化，同一套规范反复调用，保证商业项目视觉统一 |

---

## 系统架构

```
┌─────────────────┐     MCP 协议     ┌──────────────────┐    HTTP    ┌──────────────┐
│  Trae Agent     │ ◄──────────────► │  Pixelle-MCP    │ ────────► │   ComfyUI    │
│  (对话入口)      │                  │  端口 9104       │           │  端口 8188    │
│                 │                  │  (出图 MCP)      │           │  RTX 5060    │
│                 │                  └──────────────────┘           └──────────────┘
│                 │
│                 │     MCP/SSE     ┌──────────────────────────┐
│                 │ ◄──────────────► │  Prompt Composer        │
│                 │                  │  端口 9105              │
│                 │                  │  (仅输出提示词文本)      │
└─────────────────┘                  └──────────────────────────┘
```

三个 Docker 容器：

| 容器 | 端口 | 作用 | 依赖 |
|------|------|------|------|
| `comfyui` | 8188 | ComfyUI 渲染（SDXL 模型 + 5 个 SDXLPromptStyler 节点链） | NVIDIA GPU |
| `pixelle` | 9104 | 出图 MCP（Pixelle 自动把 ComfyUI 工作流转为 MCP 工具） | comfyui |
| `prompt-composer` | 9105 | 纯提示词 MCP（FastMCP，不依赖 ComfyUI） | 无 |

---

## 环境要求

### 必需

- **Docker Desktop** 4.30+（含 Docker Compose v2）
- **NVIDIA GPU 驱动** 550+（容器内 CUDA 12.8 运行时）
- **NVIDIA Container Toolkit**（Docker GPU 直通，Docker Desktop 4.30+ 已内置）
- **Git** 2.30+
- ** Trae / Cursor / Claude Desktop** 等支持 MCP 的客户端（用于接入工具）

### GPU 兼容性

| 架构 | 显卡示例 | 支持情况 |
|------|---------|---------|
| Blackwell (sm_120) | RTX 5060/5070/5080/5090 | ✅ 使用 CUDA 12.8 镜像 |
| Ada (sm_89) | RTX 4060/4070/4080/4090 | ✅ |
| Ampere (sm_86) | RTX 3060/3070/3080/3090 | ✅ |
| Turing (sm_75) | RTX 2060/2070/2080 | ✅ |

显存要求：**最低 6GB**（1024×1024 生成），**推荐 8GB+**。

### 无 GPU 方案

若无可用的 NVIDIA GPU，可：
1. 注释掉 `docker-compose.yml` 中 `comfyui` 服务的 `deploy.resources` 段（退化为 CPU 渲染，速度慢 10-20 倍）
2. 或使用云端 ComfyUI（修改 `.env` 中 `COMFYUI_BASE_URL` 指向云端实例），仅启动 `pixelle` + `prompt-composer` 两个容器

---

## 快速开始（Agent 可直接执行）

> **给 Agent 的指令**：按以下步骤顺序执行命令，全部成功后系统即可使用。每步命令都已写成可直接复制的形式。

### 步骤 0：克隆仓库

```bash
git clone https://github.com/orange521456/comfyui-cinematic-mcp.git
cd comfyui-cinematic-mcp
```

### 步骤 1：拉取 Pixelle-MCP 子项目

本项目依赖 [AIDC-AI/Pixelle-MCP](https://github.com/AIDC-AI/Pixelle-MCP) 作为出图 MCP 引擎，需单独 clone 到子目录：

```bash
git clone https://github.com/AIDC-AI/Pixelle-MCP.git Pixelle-MCP
```

若网络受限，使用镜像：

```bash
git clone https://ghproxy.com/https://github.com/AIDC-AI/Pixelle-MCP.git Pixelle-MCP
```

### 步骤 2：配置环境变量

复制示例配置并修改：

```bash
cp .env.example .env
```

编辑 `.env`，关键字段说明：

```ini
# ComfyUI 地址（Docker 容器间通信用服务名，不要用 localhost）
COMFYUI_BASE_URL=http://comfyui:8188
COMFYUI_EXECUTOR_TYPE=http

# Pixelle 服务配置
HOST=0.0.0.0
PORT=9004

# 禁用 Chainlit 认证（纯 MCP 工具模式）
CHAINLIT_AUTH_ENABLED=false
CHAINLIT_SAVE_STARTER_ENABLED=false

# CDN 策略（国内用 china，海外用 global）
CDN_STRATEGY=china

# LLM Provider 配置
# 纯 MCP 工具模式不需要 LLM，但 Pixelle 启动检查要求至少配置一个
# Ollama 未运行也不影响 MCP 工具功能
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_MODELS=qwen2.5:7b
```

### 步骤 3：准备 ComfyUI 模型

ComfyUI 容器需要 SDXL 基础模型。默认工作流使用 `sdXL_v10VAEFix.safetensors`。

**方式 A：挂载宿主机已有 ComfyUI**（推荐，省去重新下载模型）

编辑 `docker-compose.yml`，找到 `comfyui` 服务的 `volumes`，将：
```yaml
# - /path/to/your/ComfyUI:/app/ComfyUI
```
取消注释并改为你的实际路径，例如：
```yaml
- /c/Users/yourname/ComfyUI:/app/ComfyUI
```

**方式 B：容器内从零搭建**

下载 SDXL 模型到 `comfyui-data/models/checkpoints/` 目录（需自行创建）：
```bash
mkdir -p comfyui-data/models/checkpoints
# 下载 sdXL_v10VAEFix.safetensors 到上述目录
# 官方下载: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
```

然后在 `docker-compose.yml` 中挂载：
```yaml
volumes:
  - ./comfyui-data/models:/app/ComfyUI/models
```

### 步骤 4：安装 sdxl_prompt_styler 自定义节点

五层视觉的核心是 SDXL Prompt Styler 节点。在 ComfyUI 启动前安装：

```bash
# 若使用方式 A（挂载宿主机 ComfyUI）
cd /path/to/your/ComfyUI/custom_nodes
git clone https://github.com/twri/sdxl_prompt_styler.git

# 将本项目的五层预设复制到 sdxl_prompt_styler 目录
cp /path/to/comfyui-cinematic-mcp/prompt_composer/presets/cinematic_*.json /path/to/your/ComfyUI/custom_nodes/sdxl_prompt_styler/
```

预设文件位置：`prompt_composer/presets/cinematic_light.json` 等 5 个文件。

### 步骤 5：启动全部服务

```bash
docker-compose up -d
```

首次启动会拉取 PyTorch CUDA 镜像（约 5GB），需 10-30 分钟，取决于网速。

### 步骤 6：验证服务状态

```bash
# 查看容器状态，三个都应是 Up (healthy)
docker-compose ps

# 测试 ComfyUI
curl http://localhost:8188/system_stats

# 测试 Pixelle MCP
curl http://localhost:9104/health

# 测试 Prompt Composer SSE
curl http://localhost:9105/sse
```

预期输出：
- ComfyUI: 返回 JSON 含 `system` 字段
- Pixelle: 返回 `{"status":"ok"}`
- Prompt Composer: 返回 SSE 事件流

### 步骤 7：接入 MCP 客户端

在 Trae / Cursor / Claude Desktop 的 MCP 配置中添加两个服务（详见 [接入 Trae / Cursor / Claude Desktop](#接入-trae--cursor--claude-desktop)）。

### 步骤 8：首次生成测试

在对话中输入：

> 用 cinematic_visual_generate 工具生成一张黄金时刻光线的人像，85mm 镜头，青橙调色

或直接调用纯提示词工具：

> 用 cinematic_prompt_compose 合成提示词，主体是"赛博朋克武士站在霓虹小巷"

---

## 配置详解

### `.env` 文件

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `COMFYUI_BASE_URL` | `http://comfyui:8188` | ComfyUI 地址（容器间通信用服务名） |
| `COMFYUI_EXECUTOR_TYPE` | `http` | ComfyUI 调用方式（`http` 或 `websocket`） |
| `HOST` | `0.0.0.0` | Pixelle 监听地址 |
| `PORT` | `9004` | Pixelle 容器内端口（宿主映射 9104） |
| `CHAINLIT_AUTH_ENABLED` | `false` | 禁用 Web 界面认证 |
| `CDN_STRATEGY` | `china` | CDN 策略（`china` / `global` / `auto`） |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434/v1` | Ollama 地址（仅用于启动检查） |
| `OLLAMA_MODELS` | `qwen2.5:7b` | Ollama 模型名（仅用于启动检查） |

### `docker-compose.yml` 关键配置

```yaml
services:
  comfyui:
    # GPU 直通（必需，否则渲染极慢）
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # 挂载宿主机 ComfyUI（含模型 + 自定义节点）
    volumes:
      - /c/Users/yourname/ComfyUI:/app/ComfyUI
      - ./comfyui_output:/output
      - ./comfyui_input:/input

  pixelle:
    environment:
      - COMFYUI_BASE_URL=http://comfyui:8188   # 容器间用服务名通信
    depends_on:
      comfyui:
        condition: service_healthy              # 等 ComfyUI 就绪再启动
```

### 端口映射

| 宿主端口 | 容器端口 | 服务 |
|---------|---------|------|
| 8188 | 8188 | ComfyUI |
| 9104 | 9004 | Pixelle MCP |
| 9105 | 9005 | Prompt Composer MCP |

> **注意**：Windows 上 9004/9005 处于保留端口范围，故宿主用 9104/9105 映射。

---

## MCP 工具参考

### A. 出图工具（Pixelle，端口 9104）

#### `cinematic_visual_generate`

五层电影级视觉一次性生成。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | ✅ | 主体+场景+情绪描述（英文效果最佳） |
| `negative_prompt` | string | ❌ | 全局负向提示词 |
| `light_style` | string | ❌ | 光线预设名（默认 `light_soft_diffuse`） |
| `lens_style` | string | ❌ | 镜头预设名（默认 `lens_85mm_portrait`） |
| `color_style` | string | ❌ | 色彩预设名（默认 `color_teal_orange`） |
| `texture_style` | string | ❌ | 材质预设名（默认 `texture_real_skin`） |
| `story_style` | string | ❌ | 叙事预设名（默认 `story_rule_of_thirds`） |
| `width` | int | ❌ | 宽度（默认 1024） |
| `height` | int | ❌ | 高度（默认 1024） |

**返回：** 图片 URL，例如 `http://127.0.0.1:9104/files/xxx.png`

#### `layered_refine`

基于上轮图片分层精修（img2img）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `origin_image` | string | ✅ | 上轮图片路径或 URL |
| `prompt` | string | ✅ | 沿用上轮正向提示词 |
| `negative_prompt` | string | ❌ | 沿用上轮负向提示词 |
| `style` | string | ❌ | 新的预设名（任意一层） |
| `denoise` | float | ❌ | 重绘强度 0.0-1.0（默认 0.6） |

### B. 纯提示词工具（Prompt Composer，端口 9105）

#### `cinematic_prompt_compose`

五层合成提示词，仅输出文本（不生图），可喂给任意生图模型。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `subject` | string | ✅ | 主体描述（人物/建筑/物体） |
| `scene` | string | ❌ | 场景环境 |
| `mood` | string | ❌ | 情绪氛围 |
| `light_style` | string | ❌ | 光线预设名 |
| `lens_style` | string | ❌ | 镜头预设名 |
| `color_style` | string | ❌ | 色彩预设名 |
| `texture_style` | string | ❌ | 材质预设名 |
| `story_style` | string | ❌ | 叙事预设名 |
| `light_custom` | string | ❌ | 光线自定义描述（覆盖预设） |
| `lens_custom` | string | ❌ | 镜头自定义描述 |
| `color_custom` | string | ❌ | 色彩自定义描述 |
| `texture_custom` | string | ❌ | 材质自定义描述 |
| `story_custom` | string | ❌ | 叙事自定义描述 |
| `negative_prompt` | string | ❌ | 全局负向提示词 |

**返回示例：**

```json
{
  "positive_prompt": "cinematic portrait of a woman in crimson hanfu, golden hour rim lighting, 85mm portrait lens, teal and orange color grade, hyperreal skin texture, rule of thirds composition",
  "negative_prompt": "blurry, deformed, flat lighting, wide angle distortion, plastic skin",
  "layers_applied": [
    {"layer": "light", "style": "light_golden_hour", "type": "preset"},
    {"layer": "lens", "style": "lens_85mm_portrait", "type": "preset"},
    ...
  ],
  "layer_count": 5
}
```

#### `list_cinematic_presets`

列出 36 个预设。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `layer` | string | ❌ | 指定层名（`light`/`lens`/`color`/`texture`/`story`），留空返回全部 |

#### `layered_prompt_refine`

分层精修提示词文本（不生图）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `base_positive` | string | ✅ | 上一轮的正向提示词 |
| `modify_layer` | string | ✅ | 要修改的层（`light`/`lens`/`color`/`texture`/`story`） |
| `adjust_content` | string | ✅ | 修改描述，如"将平光改为日落侧逆光" |
| `base_negative` | string | ❌ | 上一轮的负向提示词 |

---

## 五层视觉预设库

### 1. 光线 LIGHT（8 个）

| 预设名 | 效果 |
|--------|------|
| `light_golden_hour` | 黄金时刻柔和侧光、暖色、长阴影 |
| `light_blue_hour` | 蓝调时刻、冷色环境光 |
| `light_rim_back` | 逆光轮廓光、边缘发亮 |
| `light_chiaroscuro` | 明暗对比强烈、单一硬光源 |
| `light_neon_noir` | 霓虹黑色电影、洋红+青色 |
| `light_soft_diffuse` | 柔光美颜、均匀肤质（默认） |
| `light_godrays` | 体积光光束、丁达尔效应 |
| `light_lowkey_candle` | 烛光暗调、温馨私密 |

### 2. 镜头 LENS（7 个）

| 预设名 | 效果 |
|--------|------|
| `lens_35mm_anamorphic` | 35mm 变形宽银幕、椭圆散景 |
| `lens_85mm_portrait` | 85mm 人像、浅景深（默认） |
| `lens_24mm_wide_env` | 24mm 广角、环境叙事 |
| `lens_macro_detail` | 微距特写、超浅景深 |
| `lens_dutch_tilt` | 倾斜构图、心理不安 |
| `lens_200mm_telephoto` | 200mm 长焦压缩感 |
| `lens_low_angle` | 仰拍英雄视角 |

### 3. 色彩 COLOR（7 个）

| 预设名 | 效果 |
|--------|------|
| `color_teal_orange` | 青橙好莱坞调色（默认） |
| `color_bleach_bypass` | 漂白旁路、低饱和高对比 |
| `color_low_sat_cold` | 低饱和冷灰、忧郁氛围 |
| `color_warm_analog` | 暖色胶片感、琥珀色 |
| `color_noir_mono` | 黑色电影黑白单色 |
| `color_pastel_dreamy` | 粉彩梦幻、柔光雾化 |
| `color_portra400` | Portra 400 胶片仿真 |

### 4. 材质 TEXTURE（6 个）

| 预设名 | 效果 |
|--------|------|
| `texture_real_skin` | 真实皮肤毛孔、次表面散射（默认） |
| `texture_film_grain` | 35mm 胶片颗粒 |
| `texture_metal_wet` | 湿润金属反光 |
| `texture_fabric_weave` | 织物纤维细节 |
| `texture_weathered_patina` | 风化岁月感 |
| `texture_glass_translucent` | 半透明玻璃折射 |

### 5. 叙事 STORY（8 个）

| 预设名 | 效果 |
|--------|------|
| `story_rule_of_thirds` | 三分法构图（默认） |
| `story_center_symmetry` | 居中对称、库布里克式 |
| `story_leading_lines` | 引导线构图 |
| `story_closeup_portrait` | 情感特写 |
| `story_environmental_wide` | 环境全景建立镜头 |
| `story_dutch_angle` | 倾斜不安感 |
| `story_over_shoulder` | 过肩镜头对话 |
| `story_low_angle_hero` | 仰拍英雄感 |

---

## 使用示例

### 示例 1：直接出图（模式 A）

调用 `cinematic_visual_generate`：

```json
{
  "prompt": "cinematic portrait of a woman in crimson hanfu, jade hairpin, porcelain skin",
  "negative_prompt": "blurry, deformed, low quality, watermark, text",
  "light_style": "light_golden_hour",
  "lens_style": "lens_85mm_portrait",
  "color_style": "color_teal_orange",
  "texture_style": "texture_real_skin",
  "story_style": "story_rule_of_thirds",
  "width": 1024,
  "height": 1024
}
```

生成耗时约 30-60 秒（RTX 5060, 25 步采样），图片保存在 `comfyui_output/`。

### 示例 2：仅输出提示词（模式 B）

调用 `cinematic_prompt_compose`：

```json
{
  "subject": "cyberpunk samurai standing in neon-lit alley",
  "scene": "rainy night, reflective wet streets, towering holographic ads",
  "mood": "ominous and mysterious",
  "light_style": "light_neon_noir",
  "lens_style": "lens_35mm_anamorphic",
  "color_style": "color_bleach_bypass",
  "texture_style": "texture_metal_wet",
  "story_style": "story_low_angle_hero"
}
```

返回的 `positive_prompt` 可直接粘贴到 Midjourney / 即梦 / Flux。

### 示例 3：自定义层（不用预设）

```json
{
  "subject": "cyberpunk samurai in neon alley",
  "light_custom": "volumetric purple backlight with flickering neon reflections",
  "color_custom": "high contrast magenta and cyan neon grade, crushed blacks",
  "lens_style": "lens_35mm_anamorphic",
  "texture_style": "texture_metal_wet",
  "story_style": "story_low_angle_hero"
}
```

### 示例 4：分层精修

基于上轮结果单独改光线层：

```json
{
  "origin_image": "http://127.0.0.1:9104/files/xxx.png",
  "prompt": "<沿用上轮>",
  "negative_prompt": "<沿用上轮>",
  "style": "light_neon_noir",
  "denoise": 0.6
}
```

### 示例 5：电影分镜一致性

固定三层（light+color+texture），只改 lens+story：

| 镜头 | lens | story |
|------|------|-------|
| 建立镜头 | `lens_24mm_wide_env` | `story_environmental_wide` |
| 主角特写 | `lens_85mm_portrait` | `story_closeup_portrait` |
| 过肩对话 | `lens_35mm_anamorphic` | `story_over_shoulder` |

---

## 接入 Trae / Cursor / Claude Desktop

### Trae

**方式 A：通过 IDE 界面添加**

设置 → MCP → 添加自定义 MCP 服务：

**服务 1（出图）：**
- 类型：`streamable`（Streamable HTTP）
- URL：`http://127.0.0.1:9104/pixelle/mcp`

**服务 2（纯提示词）：**
- 类型：`SSE`
- URL：`http://127.0.0.1:9105/sse`

**方式 B：直接编辑配置文件**

Trae 的 MCP 配置文件位置：
- Windows：`%APPDATA%\TRAE SOLO CN\User\mcp.json`
- macOS：`~/.trae/User/mcp.json`

在 `mcpServers` 下添加两个服务：

```json
{
  "mcpServers": {
    "cinematic-pixelle": {
      "type": "streamable",
      "url": "http://127.0.0.1:9104/pixelle/mcp"
    },
    "cinematic-composer": {
      "type": "sse",
      "url": "http://127.0.0.1:9105/sse"
    }
  }
}
```

> 若已有其他 MCP 服务，只需把 `cinematic-pixelle` 和 `cinematic-composer` 两个对象合并到现有 `mcpServers` 下即可。修改后需重启 Trae 或在 MCP 面板点击刷新按钮。

### Cursor

编辑 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "cinematic-pixelle": {
      "url": "http://127.0.0.1:9104/pixelle/mcp"
    },
    "cinematic-composer": {
      "url": "http://127.0.0.1:9105/sse"
    }
  }
}
```

### Claude Desktop

编辑 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "cinematic-pixelle": {
      "type": "streamable",
      "url": "http://127.0.0.1:9104/pixelle/mcp"
    },
    "cinematic-composer": {
      "type": "sse",
      "url": "http://127.0.0.1:9105/sse"
    }
  }
}
```

---

## 常见问题

### Q1：`docker-compose up` 后 ComfyUI 容器一直 unhealthy

**原因**：ComfyUI 首次启动需加载模型，可能超过默认 60 秒健康检查宽限期。

**解决**：编辑 `docker-compose.yml` 中 `comfyui` 服务的 `healthcheck.start_period`，改为 `120s` 或 `180s`。

### Q2：ComfyUI 报 `torchsde not found`

**原因**：`requirements.txt` 中 `torchsde` 被 grep 误过滤。

**解决**：`comfyui-docker/Dockerfile` 中的过滤正则已用 `\b` 边界匹配修复。若仍报错，直接在 Dockerfile 中移除 grep 过滤，改为完整安装 requirements.txt。

### Q3：GPU 未被识别（`docker-compose` 报 GPU 错误）

**原因**：未安装 NVIDIA Container Toolkit 或 Docker Desktop 未启用 GPU 支持。

**解决**：
1. Windows：更新 Docker Desktop 到 4.30+，在设置中启用 NVIDIA GPU
2. Linux：安装 `nvidia-container-toolkit`
3. 临时方案：注释 `docker-compose.yml` 中 `deploy.resources` 段，退化为 CPU 模式

### Q4：Pixelle 容器报 `Configuration is incomplete`

**原因**：Pixelle 启动检查要求至少配置一个 LLM provider。

**解决**：确保 `.env` 中配置了 `OLLAMA_MODELS=qwen2.5:7b`（即使 Ollama 未运行也能通过检查，纯 MCP 工具模式不需要 LLM）。

### Q5：Windows 端口 9004/9005 被占用

**原因**：Windows 保留端口范围。

**解决**：本项目已将宿主端口改为 9104/9105，若仍冲突，编辑 `docker-compose.yml` 的 `ports` 段改为其他端口。

### Q6：生成的图片无法保存（Permission denied）

**原因**：ComfyUI 容器对挂载目录无写入权限。

**解决**：本项目已将输出目录挂载到 `./comfyui_output/`（项目目录内），避免宿主机系统目录的权限限制。若仍报错，执行：
```bash
# Linux/macOS
chmod -R 777 comfyui_output comfyui_input

# Windows (PowerShell)
icacls comfyui_output /grant Everyone:F
```

### Q7：如何使用其他 SDXL 模型

编辑 `data/custom_workflows/cinematic_visual_generate.json` 中 `CheckpointLoaderSimple` 节点的 `ckpt_name` 字段，改为你的模型文件名（需先放入 ComfyUI 的 `models/checkpoints/` 目录）。

推荐模型：
- `sdXL_v10VAEFix.safetensors`（默认，SDXL Base）
- `realisticVisionV60.safetensors`（写实人像）
- `cinematicPhotoreal.safetensors`（电影级写实）

### Q8：如何降低显存占用

1. 减小尺寸：`width`/`height` 改为 768
2. 降低步数：编辑工作流中 `KSampler` 的 `steps` 从 25 改为 15
3. 使用 FP8 模型：选择 `*_fp8_e4m3fn.safetensors` 版本

---

## 项目结构

```
comfyui-cinematic-mcp/
├── docker-compose.yml              # 三容器编排
├── .env.example                   # 配置模板
├── .gitignore
├── README.md                      # 本文档
│
├── comfyui-docker/
│   ├── Dockerfile                  # ComfyUI 镜像（pytorch 2.7 + CUDA 12.8）
│   └── requirements.txt            # ComfyUI Python 依赖
│
├── Dockerfile.prompt_composer      # 提示词合成器镜像
│
├── prompt_composer/                # 纯提示词 MCP（不依赖 ComfyUI）
│   ├── mcp_server.py               # FastMCP 服务（3 个工具）
│   ├── composer.py                 # 五层合成核心逻辑
│   ├── requirements.txt
│   └── presets/                    # 5 个 JSON 预设文件（36 项）
│       ├── cinematic_light.json
│       ├── cinematic_lens.json
│       ├── cinematic_color.json
│       ├── cinematic_texture.json
│       └── cinematic_story.json
│
├── data/
│   └── custom_workflows/           # ComfyUI 工作流（Pixelle 自动转为 MCP 工具）
│       ├── cinematic_visual_generate.json   # 五层链式 SDXLPromptStyler
│       └── layered_refine.json              # img2img 分层精修
│
├── workflows/                      # 工作流备份
│   ├── cinematic_visual_generate.json
│   └── layered_refine.json
│
├── comfyui_output/                 # 生成图片输出目录（挂载点）
└── comfyui_input/                  # img2img 输入目录（挂载点）
```

### 子项目

- `Pixelle-MCP/` — [AIDC-AI/Pixelle-MCP](https://github.com/AIDC-AI/Pixelle-MCP)，阿里开源的 ComfyUI → MCP 转换引擎。需单独 clone，详见 [步骤 1](#步骤-1拉取-pixelle-mcp-子项目)。

---

## 扩展自定义预设

### 添加新预设

编辑 `prompt_composer/presets/cinematic_*.json`，按相同格式追加：

```json
[
  {"name":"light_my_custom","prompt":"{prompt}, my custom lighting description","negative_prompt":"something to avoid"},
  {"name":"light_another","prompt":"{prompt}, another lighting style","negative_prompt":"another negative"}
]
```

**同步更新两处**（保持一致）：
1. `prompt_composer/presets/cinematic_*.json`（Prompt Composer 使用）
2. `<ComfyUI>/custom_nodes/sdxl_prompt_styler/cinematic_*.json`（ComfyUI 出图使用）

保存后重启容器：

```bash
docker-compose restart prompt-composer comfyui
```

### 添加新工作流

在 `data/custom_workflows/` 中放入新的 ComfyUI API 格式工作流 JSON。文件名即 MCP 工具名。Pixelle 会自动加载并转为 MCP 工具。

工作流 DSL 标记规则（Pixelle 解析）：

| 标记 | 含义 | 示例 |
|------|------|------|
| `$param.field` | 参数 | `$prompt.value` |
| `$param.field!` | 必填参数 | `$prompt.value!` |
| `$param.~field` | 需上传处理的参数 | `$origin_image.~image` |
| `$output.name` | 输出标记 | `$output.result` |
| 节点标题 `MCP` | 工具描述节点 | 在 `value`/`text`/`string` 字段写描述 |

---

## 日常运维命令

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启某个服务
docker-compose restart pixelle

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f comfyui          # ComfyUI 渲染日志
docker-compose logs -f pixelle          # Pixelle MCP 日志
docker-compose logs -f prompt-composer  # 提示词合成器日志

# 重建镜像（修改 Dockerfile 后）
docker-compose build comfyui
docker-compose up -d comfyui

# 清理生成的图片
rm -f comfyui_output/*.png
```

---

## 技术栈

- **ComfyUI** — 开源 Stable Diffusion 工作流引擎
- **Pixelle-MCP** — ComfyUI → MCP 协议转换引擎（AIDC-AI 开源）
- **SDXL Prompt Styler** — ComfyUI 分层提示词节点（twri 开源）
- **FastMCP** — Python MCP 服务器框架
- **Docker** — 容器化部署
- **PyTorch 2.7 + CUDA 12.8** — GPU 加速推理（兼容 Blackwell）

---

## 许可证

本项目使用 MIT 许可证。

子项目许可证：
- [Pixelle-MCP](https://github.com/AIDC-AI/Pixelle-MCP) — MIT
- [sdxl_prompt_styler](https://github.com/twri/sdxl_prompt_styler) — MIT

---

## 致谢

- [AIDC-AI](https://github.com/AIDC-AI) — Pixelle-MCP 项目
- [twri](https://github.com/twri) — SDXL Prompt Styler 节点
- [comfyanonymous](https://github.com/comfyanonymous/ComfyUI) — ComfyUI 引擎
