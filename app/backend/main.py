import asyncio
import base64
import binascii
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings
import httpx
import aiosqlite

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None
    types = None
    HAS_GOOGLE_GENAI = False

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ai-geometry-backend")

# Add file handler for persistent logs
try:
    log_file = Path(__file__).resolve().parent / "server.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(fh)
except Exception as e:
    print(f"Failed to setup file logging: {e}")


class Settings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    https_proxy: str = os.getenv("HTTPS_PROXY", "").strip()
    host: str = os.getenv("APP_BACKEND_HOST", "0.0.0.0").strip() or "0.0.0.0"
    port: int = int(os.getenv("APP_BACKEND_PORT", "8001"))
    model_provider: str = os.getenv("MODEL_PROVIDER", "gemini").strip() or "gemini"
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
    gemini_use_sdk: bool = os.getenv("GEMINI_USE_SDK", "false").strip().lower() in {"1", "true", "yes", "on"}
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    timeout_seconds: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "120"))
    allow_all_origins: bool = os.getenv("APP_ALLOW_ALL_ORIGINS", "true").strip().lower() in {"1", "true", "yes", "on"}
    allowed_origins: str = os.getenv(
        "APP_ALLOWED_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    )


settings = Settings()
allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
DEFAULT_API_BASE = "http://127.0.0.1:8001"
MAX_IMAGE_DATA_URL_LENGTH = 8_000_000
MAX_IMAGE_BYTES = 4_000_000
ALLOWED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
GEMINI_REST_API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
SUPPORTED_PROVIDERS = {"gemini", "openai_compatible"}

if settings.https_proxy:
    os.environ["HTTP_PROXY"] = settings.https_proxy
    os.environ["HTTPS_PROXY"] = settings.https_proxy


SYSTEM_PROMPT = r"""
你是一个安全的中文几何解题助手。
请根据题目文本或图片，输出一个严格的 JSON 对象。

绝对要求：
1. 只返回 JSON，不要返回 markdown 代码块和解释。
2. 所有文本内容用纯文本数组返回，不允许 HTML。
3. 不要输出 JavaScript，不要输出 drawCode。
4. 绘图信息放到 scene 字段，使用受限结构化协议。
5. 必须根据题目准确绘制几何图形，包含所有关键点和辅助线。

输出结构：
{
  "title": "题目标题",
  "analysis": ["分析段落1", "分析段落2"],
  "solution": ["步骤1", "步骤2"],
  "knowledge": ["知识点1", "知识点2"],
  "scene": {
    "mode": "plane" | "canvas",
    "viewport": {
      "width": 800,
      "height": 600,
      "origin": { "x": 400, "y": 300 },
      "scale": 40,
      "showGrid": true,
      "showAxes": true
    },
    "points": {
      "A": { "x": 0, "y": 0, "label": "A", "draggable": false, "space": "plane" },
      "P": { "x": 1, "y": 0, "label": "P", "draggable": true, "space": "plane" }
    },
    "shapes": [
      { "type": "segment", "from": "A", "to": "B", "color": "#2563eb", "width": 2 },
      { "type": "ray", "from": "A", "to": "B", "color": "#64748b", "width": 1.5, "dashed": true },
      { "type": "line", "from": "A", "to": "B", "color": "#94a3b8", "width": 1, "dashed": true },
      { "type": "polygon", "points": ["A", "B", "C"], "stroke": "#2563eb", "fill": "rgba(37,99,235,0.08)", "closed": true },
      { "type": "circle", "center": "A", "radius": 2, "radiusSpace": "plane", "stroke": "#10b981", "fill": "rgba(16,185,129,0.1)" },
      { "type": "angle", "points": ["A", "B", "C"], "radius": 0.5, "color": "#ef4444", "showValue": true },
      { "type": "perp", "points": ["A", "B", "C"], "size": 0.2, "color": "#0f172a" },
      { "type": "parabola", "vertex": "V", "a": 0.5, "width": 10, "color": "#8b5cf6" },
      { "type": "function", "fn": "x * x", "range": [-5, 5], "color": "#f59e0b" },
      { "type": "label", "text": "关键关系", "x": 2, "y": 3, "space": "plane", "color": "#111827" }
    ],
    "animations": [
      { "point": "P", "kind": "line", "from": { "x": -4, "y": 0 }, "to": { "x": 4, "y": 0 }, "space": "plane", "duration": 8 },
      { "point": "Q", "kind": "orbit", "center": { "x": 0, "y": 0 }, "radius": 3, "startAngle": 0, "duration": 10 }
    ]
  }
}

图形绘制规则：
1. mode 为 plane 时使用数学坐标系（y轴向上），canvas 时使用像素坐标（y轴向下）。
2. 必须绘制完整图形：所有题目中提到的点、线、圆都必须包含在 scene 中。
3. 对于动点问题，设置 draggable: true 并添加 animations 描述运动轨迹。
4. parabola：vertex 为顶点名称（需在 points 中定义），a 为开口系数（正向上，负向下）。
5. function：fn 为 x 的表达式字符串，如 "x*x"、"-2/x"、"Math.sin(x)"。注意：对于反比例函数等不连续函数，请输出两条 function 曲线（如 range 分别设为 [-10, -0.1] 和 [0.1, 10]）以避免零点连线。
6. 对于将军饮马等最值问题，绘制对称点和辅助线来展示解题思路。
7. 所有几何图形必须使用平面坐标系（space: "plane"），确保尺寸一致。
8. 自动视角：必须根据所有点的坐标范围，合理设置 viewport 的 origin 和 scale，确保图形在 800x600 区域内居中且清晰。
9. 标注建议：对于关键长度比例（如 PA/PB=2），请使用 type="value" 标注。
10. 动点轨迹与动画（极其重要）：
    - 如果题目涉及“动点”或“轨迹”，必须在 `points` 中定义该动点（如 P），并设置 `draggable: true`。
    - 必须在 `animations` 中添加该点的运动描述。
    - 圆周运动：使用 `kind: "orbit"`，必须提供 `center`（坐标对象）, `radius`, `duration`。
    - 直线运动：使用 `kind: "line"`，提供 `from`, `to` 坐标对象。
11. 教科书级排版（绝对要求）：
    - 所有文本中涉及的数学变量（如 $x$, $y$）、常量、几何符号（如 $\triangle ABC$, $\odot O$）、算式和方程（如 $x^2 + y^2 = r^2$）必须使用 LaTeX 格式并用单个 `$` 符号包裹。
    - 禁止使用 `x^2` 或 `PA^2` 这样的纯文本表示法。

坐标计算原则（极其重要）：
1. 严禁目测估算：对于交点、中点、垂足，必须优先使用 `formula` 字段进行逻辑定义。
2. 只有独立点（如三角形的顶点）才直接给出 `x, y`。
3. 依赖点定义：
   - 中点：`"M": { "formula": "midpoint(A,B)" }`
   - 交点（直线AB与CD的交点）：`"P": { "formula": "intersection(A,B,C,D)" }`
   - 垂足（点P到直线AB的投影）：`"D": { "formula": "projection(P,A,B)" }`
4. 解析几何：若给出函数解析式，请先在内部解出关键点坐标，再在 `points` 中通过 `x, y` 给出，或使用 `formula` 表达其相互依赖。
5. 自动校正：后端会自动根据 `formula` 修正 `x, y`，确保图形绝对符合几何定义。
"""


class BadRequestError(ValueError):
    pass


class UpstreamResponseError(RuntimeError):
    pass


class Point(BaseModel):
    x: float = 0.0
    y: float = 0.0
    label: str | None = ""
    draggable: bool = False
    space: Literal["plane", "canvas"] = "plane"
    formula: str | None = None

    @field_validator("label")
    @classmethod
    def cap_label(cls, value: str | None) -> str | None:
        if value is None: return None
        return str(value)[:12]


class GeometrySolver:
    @staticmethod
    def get_line_intersection(p1, p2, p3, p4):
        x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y
        x3, y3, x4, y4 = p3.x, p3.y, p4.x, p4.y
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if abs(denom) < 1e-9: return None
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        return x1 + ua * (x2 - x1), y1 + ua * (y2 - y1)

    @staticmethod
    def get_projection(p, a, b):
        ax, ay, bx, by, px, py = a.x, a.y, b.x, b.y, p.x, p.y
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0: return ax, ay
        t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
        return ax + t * dx, ay + t * dy

    @classmethod
    def solve(cls, points: dict[str, Point]):
        import re
        changed = True
        for _ in range(5):
            if not changed: break
            changed = False
            for p in points.values():
                if not p.formula: continue
                # midpoint(A,B)
                m = re.match(r"midpoint\((\w+),(\w+)\)", p.formula)
                if m:
                    a, b = points.get(m.group(1)), points.get(m.group(2))
                    if a and b:
                        nx, ny = (a.x + b.x) / 2, (a.y + b.y) / 2
                        if abs(p.x - nx) > 1e-6 or abs(p.y - ny) > 1e-6:
                            p.x, p.y, changed = nx, ny, True
                # intersection(A,B,C,D)
                m = re.match(r"intersection\((\w+),(\w+),(\w+),(\w+)\)", p.formula)
                if m:
                    p1, p2, p3, p4 = points.get(m.group(1)), points.get(m.group(2)), points.get(m.group(3)), points.get(m.group(4))
                    if all([p1, p2, p3, p4]):
                        res = cls.get_line_intersection(p1, p2, p3, p4)
                        if res:
                            nx, ny = res
                            if abs(p.x - nx) > 1e-6 or abs(p.y - ny) > 1e-6:
                                p.x, p.y, changed = nx, ny, True
                # projection(P,A,B)
                m = re.match(r"projection\((\w+),(\w+),(\w+)\)", p.formula)
                if m:
                    target, a, b = points.get(m.group(1)), points.get(m.group(2)), points.get(m.group(3))
                    if all([target, a, b]):
                        nx, ny = cls.get_projection(target, a, b)
                        if abs(p.x - nx) > 1e-6 or abs(p.y - ny) > 1e-6:
                            p.x, p.y, changed = nx, ny, True


class Viewport(BaseModel):
    width: int = 800
    height: int = 600
    origin: dict[str, float] = Field(default_factory=lambda: {"x": 400, "y": 300})
    scale: float = 40
    showGrid: bool = True
    showAxes: bool = True


class ValueSource(BaseModel):
    kind: Literal["distance"]
    from_: str = Field(alias="from")
    to: str


class Shape(BaseModel):
    type: Literal["segment", "ray", "line", "polygon", "polyline", "circle", "label", "value", "angle", "perp", "function", "parabola"]
    from_: str | dict[str, float] | None = Field(default=None, alias="from")
    to: str | dict[str, float] | None = None
    points: list[str] = Field(default_factory=list)
    center: str | None = None
    radius: float | None = None
    radiusSpace: Literal["plane", "canvas"] | None = None
    stroke: str | None = None
    fill: str | None = None
    color: str | None = None
    width: float | None = 2
    dashed: bool = False
    closed: bool = False
    text: str | None = None
    x: float | None = None
    y: float | None = None
    space: Literal["plane", "canvas"] | None = None
    valueFrom: ValueSource | None = None
    # For angle: points[3] (A,B,C), B is vertex. radius is arc radius.
    # For perp: points[3] (corner) or points[4] (segments). size is square size.
    size: float | None = None
    showValue: bool = False
    # For function/parabola
    fn: str | None = None
    range: list[float] | None = None
    vertex: str | None = None
    a: float | None = None


class Animation(BaseModel):
    point: str
    kind: Literal["line", "orbit"]
    from_: dict[str, float] | None = Field(default=None, alias="from")
    to: dict[str, float] | None = None
    center: dict[str, float] | None = None
    radius: float | None = None
    startAngle: float = 0
    space: Literal["plane", "canvas"] = "plane"
    duration: float = 8


class Scene(BaseModel):
    mode: Literal["plane", "canvas"] = "canvas"
    viewport: Viewport = Field(default_factory=Viewport)
    points: dict[str, Point] = Field(default_factory=dict)
    shapes: list[Shape] = Field(default_factory=list)
    animations: list[Animation] = Field(default_factory=list)


class SolveRequest(BaseModel):
    problem: str
    image: str | None = None
    provider: str | None = None
    model: str | None = None
    upstream_base_url: str | None = None

    @field_validator("image")
    @classmethod
    def validate_image_length(cls, value: str | None) -> str | None:
        if value and len(value) > MAX_IMAGE_DATA_URL_LENGTH:
            raise BadRequestError("图片过大，请压缩后重试")
        return value

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = normalize_provider(value)
        if normalized not in SUPPORTED_PROVIDERS:
            raise BadRequestError(f"暂不支持的模型供应商: {value}")
        return normalized


class SolveResponse(BaseModel):
    title: str
    analysis: list[str]
    solution: list[str]
    knowledge: list[str]
    scene: Scene


class HistoryItem(BaseModel):
    id: int
    timestamp: float
    problem: str
    image: str | None = None
    response_data: SolveResponse


app = FastAPI(title="AI Geometry Solver Backend")
DB_PATH = str(Path(__file__).resolve().parent / "history.db")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.allow_all_origins else allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
async def startup():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                problem TEXT,
                image TEXT,
                response_json TEXT
            )
            """
        )
        async with db.execute("SELECT id, response_json FROM history") as cursor:
            async for row in cursor:
                try:
                    raw = json.loads(row[1])
                    scene = raw.get("scene") or {}
                    changed = False
                    for shape in scene.get("shapes") or []:
                        if isinstance(shape, dict) and "from_" in shape and "from" not in shape:
                            shape["from"] = shape["from_"]
                            changed = True
                        value_from = shape.get("valueFrom") if isinstance(shape, dict) else None
                        if isinstance(value_from, dict) and "from_" in value_from and "from" not in value_from:
                            value_from["from"] = value_from["from_"]
                            changed = True
                    if changed:
                        normalized = SolveResponse.model_validate(raw)
                        await db.execute(
                            "UPDATE history SET response_json = ? WHERE id = ?",
                            (normalized.model_dump_json(by_alias=True), row[0])
                        )
                except Exception as exc:
                    logger.warning("Failed to migrate history row %s: %s", row[0], exc)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


def get_api_key(authorization: str | None) -> str:
    if authorization:
        match = re.match(r"Bearer\s+(.+)", authorization.strip(), re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def normalize_provider(value: str | None) -> str:
    normalized = (value or settings.model_provider or "gemini").strip().lower()
    aliases = {
        "openai": "openai_compatible",
        "openai-compatible": "openai_compatible",
        "openai_compatible": "openai_compatible",
    }
    return aliases.get(normalized, normalized)


def get_default_api_key(provider: str) -> str:
    if provider == "openai_compatible":
        return settings.openai_api_key
    return settings.gemini_api_key


def get_default_model(provider: str) -> str:
    if provider == "openai_compatible":
        return settings.openai_model
    return settings.gemini_model


def get_default_upstream_base_url(provider: str) -> str | None:
    if provider == "openai_compatible":
        return settings.openai_base_url
    return None


def is_local_base_url(url: str | None) -> bool:
    if not url:
        return False
    normalized = url.strip().lower()
    return normalized.startswith("http://127.0.0.1") or normalized.startswith("http://localhost")


def normalize_chat_completions_url(base_url: str | None) -> str:
    normalized = (base_url or settings.openai_base_url).strip().rstrip("/")
    if not normalized:
        raise BadRequestError("缺少 OpenAI 兼容接口地址")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def model_supports_images(provider: str, model_name: str | None) -> bool:
    model = (model_name or get_default_model(provider)).strip().lower()
    if provider == "gemini":
        return True
    return bool(re.search(r"(?:^|[-_/])(vl|vision)(?:[-_/]|$)|gpt-4o|gpt-4\.1|llava|qwen2\.5vl|qwen-vl|gemma3", model))


def parse_image_data_url(image_data_url: str) -> tuple[str, bytes]:
    match = re.match(r"^data:(image\/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=\s]+)$", image_data_url)
    if not match:
        raise BadRequestError("图片格式不正确，只支持 base64 data URL")
    mime_type = match.group(1)
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise BadRequestError("暂只支持 PNG、JPEG、WEBP、GIF 图片")
    encoded = re.sub(r"\s+", "", match.group(2))
    estimated_size = (len(encoded) * 3) // 4
    if estimated_size > MAX_IMAGE_BYTES:
        raise BadRequestError("图片体积过大，请压缩到 4MB 以内")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise BadRequestError("图片 base64 数据无效") from exc
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise BadRequestError("图片体积过大，请压缩到 4MB 以内")
    logger.info("image validated mime=%s bytes=%s", mime_type, len(image_bytes))
    return mime_type, image_bytes


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    decoder = json.JSONDecoder()
    required_keys = {"title", "analysis", "solution", "knowledge", "scene"}

    def extract_balanced_object(source: str) -> str | None:
        start = source.find("{")
        if start < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(source)):
            char = source[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return source[start:index + 1]
        return None

    def escape_invalid_backslashes(source: str) -> str:
        valid_escapes = {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}
        result: list[str] = []
        in_string = False
        escape = False
        for index, char in enumerate(source):
            if in_string:
                if escape:
                    result.append(char)
                    escape = False
                    continue
                if char == "\\":
                    next_char = source[index + 1] if index + 1 < len(source) else ""
                    result.append("\\")
                    if next_char not in valid_escapes:
                        result.append("\\")
                    else:
                        escape = True
                    continue
                if char == '"':
                    in_string = False
                result.append(char)
                continue
            if char == '"':
                in_string = True
            result.append(char)
        return "".join(result)

    def remove_trailing_commas(source: str) -> str:
        return re.sub(r",\s*([}\]])", r"\1", source)

    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and required_keys.issubset(candidate.keys()):
            logger.info("json extracted keys=%s", ",".join(sorted(candidate.keys())))
            return candidate

    balanced = extract_balanced_object(cleaned)
    if balanced:
        repaired = remove_trailing_commas(escape_invalid_backslashes(balanced))
        try:
            candidate = json.loads(repaired)
            if isinstance(candidate, dict) and required_keys.issubset(candidate.keys()):
                logger.info("json repaired keys=%s", ",".join(sorted(candidate.keys())))
                return candidate
            logger.warning("Repaired JSON missing keys: %s", list(candidate.keys()) if isinstance(candidate, dict) else "not a dict")
        except json.JSONDecodeError as exc:
            logger.warning("json repair failed: %s", exc)

    logger.error("Failed to extract valid JSON from model response. Raw text snippet: %s", cleaned[:500])
    raise UpstreamResponseError("模型没有返回有效 JSON，请尝试重新生成或检查题目内容。")


def build_gemini_payload(problem: str, image_part: tuple[str, bytes] | None, as_rest: bool = False) -> dict[str, Any]:
    user_text = f"题目内容：{problem.strip()}" if problem.strip() else "请根据图片识别并解析题目。"
    if HAS_GOOGLE_GENAI and not as_rest:
        contents: list[Any] = [types.Part.from_text(text=user_text)]
        if image_part:
            mime_type, image_bytes = image_part
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        return {
            "contents": contents,
            "config": types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0,
                response_mime_type="application/json",
                max_output_tokens=4096,
            ),
        }

    parts: list[dict[str, Any]] = [{"text": user_text}]
    if image_part:
        mime_type, image_bytes = image_part
        parts.append(
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            }
        )
    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
        },
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
    }


def extract_text_from_gemini(response: Any) -> str:
    if isinstance(response, dict):
        candidates = response.get("candidates") or []
        if candidates:
            parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
            if text:
                logger.info("gemini rest text chars=%s", len(text))
                return text
            finish_reason = (candidates[0] or {}).get("finishReason")
            if finish_reason:
                raise UpstreamResponseError(f"模型未返回文本结果: {finish_reason}")
        raise UpstreamResponseError("模型没有返回文本结果")

    text = str(getattr(response, "text", "") or "").strip()
    if text:
        logger.info("gemini sdk text chars=%s", len(text))
        return text

    candidates = getattr(response, "candidates", None) or []
    if candidates:
        finish_reason = getattr(candidates[0], "finish_reason", None)
        if finish_reason:
            raise UpstreamResponseError(f"模型未返回文本结果: {finish_reason}")

    raise UpstreamResponseError("模型没有返回文本结果")


async def request_gemini(api_key: str, problem: str, image_part: tuple[str, bytes] | None, model_name: str | None = None) -> Any:
    start = time.perf_counter()
    target_model = model_name or settings.gemini_model
    logger.info(
        "gemini request start model=%s sdk_enabled=%s sdk_available=%s problem_chars=%s has_image=%s timeout=%ss",
        target_model,
        settings.gemini_use_sdk,
        HAS_GOOGLE_GENAI,
        len(problem.strip()),
        bool(image_part),
        settings.timeout_seconds,
    )
    if settings.gemini_use_sdk and HAS_GOOGLE_GENAI:
        payload = build_gemini_payload(problem, image_part, as_rest=False)
        client = genai.Client(api_key=api_key)
        
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model=target_model,
                    contents=payload["contents"],
                    config=payload["config"],
                ),
                timeout=settings.timeout_seconds,
            )
            logger.info("gemini sdk response elapsed=%.2fs", time.perf_counter() - start)
            return response
        except TimeoutError:
            logger.warning("gemini sdk timed out after %ss, falling back to rest", settings.timeout_seconds)
        except Exception as sdk_exc:
            logger.warning("gemini sdk failed, falling back to rest: %s", sdk_exc)
            # Fall through to REST implementation

    payload = build_gemini_payload(problem, image_part, as_rest=True)
    async with httpx.AsyncClient(
        timeout=settings.timeout_seconds,
    ) as client:
        response = await client.post(
            f"{GEMINI_REST_API_ROOT}/models/{target_model}:generateContent",
            params={"key": api_key},
            json=payload,
        )
    logger.info("gemini rest response status=%s elapsed=%.2fs", response.status_code, time.perf_counter() - start)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text
        logger.error("Upstream API error: %s - %s", response.status_code, detail)
        raise RuntimeError(detail or str(exc)) from exc
    return response.json()


def build_openai_messages(problem: str, image_part: tuple[str, bytes] | None) -> list[dict[str, Any]]:
    user_text = f"题目内容：{problem.strip()}" if problem.strip() else "请根据图片识别并解析题目。"
    if not image_part:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

    mime_type, image_bytes = image_part
    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]


def extract_text_from_openai(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise UpstreamResponseError("模型没有返回可用结果")

    message = (choices[0] or {}).get("message") or {}
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        text = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in {"text", "output_text"}
        ).strip()
        if text:
            return text

    finish_reason = (choices[0] or {}).get("finish_reason")
    if finish_reason:
        raise UpstreamResponseError(f"模型未返回文本结果: {finish_reason}")
    raise UpstreamResponseError("模型没有返回文本结果")


async def request_openai_compatible(
    api_key: str,
    problem: str,
    image_part: tuple[str, bytes] | None,
    model_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    start = time.perf_counter()
    target_model = model_name or settings.openai_model
    request_url = normalize_chat_completions_url(base_url)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, Any] = {
        "model": target_model,
        "messages": build_openai_messages(problem, image_part),
        "temperature": 0,
        "max_tokens": 4096,
    }

    logger.info(
        "openai-compatible request start model=%s url=%s problem_chars=%s has_image=%s timeout=%ss",
        target_model,
        request_url,
        len(problem.strip()),
        bool(image_part),
        settings.timeout_seconds,
    )
    async with httpx.AsyncClient(timeout=settings.timeout_seconds) as client:
        response = await client.post(request_url, headers=headers, json=payload)

    logger.info(
        "openai-compatible response status=%s elapsed=%.2fs",
        response.status_code,
        time.perf_counter() - start,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text
        logger.error("Upstream API error: %s - %s", response.status_code, detail)
        raise RuntimeError(detail or str(exc)) from exc

    return response.json()


HTML_TAG_RE = re.compile(r"<[^>]+>")


def normalize_text_list(value: Any, fallback: str) -> list[str]:
    def clean(text: str) -> str:
        return HTML_TAG_RE.sub("", str(text).strip())

    if isinstance(value, list):
        items = [clean(item) for item in value if clean(item)]
        return items[:12] or [fallback]
    if isinstance(value, str) and value.strip():
        return [clean(value)]
    return [fallback]


def normalize_scene(raw_scene: Any) -> Scene:
    try:
        scene = Scene.model_validate(raw_scene or {})
    except ValidationError as exc:
        logger.warning("Scene validation failed. Using default empty scene. Error: %s", exc)
        scene = Scene()

    cleaned_points: dict[str, Point] = {}
    for key, point in list(scene.points.items())[:24]:
        safe_key = str(key)[:12]
        cleaned_points[safe_key] = point.model_copy(update={"label": point.label or safe_key})

    # Execute geometric formulas
    GeometrySolver.solve(cleaned_points)

    def ensure_point(p_val: str | dict[str, float] | None) -> str | None:
        if isinstance(p_val, dict):
            # Create an anonymous point without label
            anon_id = f"_anon_{len(cleaned_points)}"
            cleaned_points[anon_id] = Point(x=p_val.get("x", 0), y=p_val.get("y", 0), label=None)
            return anon_id
        return p_val

    point_names = set(cleaned_points.keys())
    cleaned_shapes: list[Shape] = []
    for shape in scene.shapes[:80]:
        # Handle dict coordinates in from/to
        if shape.type in {"segment", "ray", "line"}:
            shape = shape.model_copy(update={
                "from_": ensure_point(shape.from_),
                "to": ensure_point(shape.to)
            })
            # Refresh point names set
            point_names = set(cleaned_points.keys())

        if shape.type in {"segment", "ray", "line"}:
            if not shape.from_ or not shape.to or shape.from_ not in point_names or shape.to not in point_names:
                continue
        if shape.type in {"polygon", "polyline"}:
            names = [name for name in shape.points if name in point_names][:16]
            if len(names) < 2:
                continue
            shape = shape.model_copy(update={"points": names})
        if shape.type == "circle":
            if not shape.center or shape.center not in point_names or shape.radius is None:
                continue
        if shape.type == "value":
            if not shape.valueFrom:
                continue
            if shape.valueFrom.from_ not in point_names or shape.valueFrom.to not in point_names:
                continue
        cleaned_shapes.append(shape)

    cleaned_animations: list[Animation] = []
    for animation in scene.animations[:8]:
        if animation.point in point_names:
            cleaned_animations.append(animation)

    return scene.model_copy(
        update={
            "points": cleaned_points,
            "shapes": cleaned_shapes,
            "animations": cleaned_animations,
        }
    )


def normalize_result(raw: dict[str, Any]) -> SolveResponse:
    result = {
        "title": str(raw.get("title") or "几何题智能解析")[:60],
        "analysis": normalize_text_list(raw.get("analysis"), "暂未生成思路分析。"),
        "solution": normalize_text_list(raw.get("solution"), "暂未生成详细解答。"),
        "knowledge": normalize_text_list(raw.get("knowledge"), "暂未提取知识点。"),
        "scene": normalize_scene(raw.get("scene")),
    }
    normalized = SolveResponse.model_validate(result)
    logger.info(
        "result normalized title=%s analysis=%s solution=%s knowledge=%s points=%s shapes=%s animations=%s",
        normalized.title,
        len(normalized.analysis),
        len(normalized.solution),
        len(normalized.knowledge),
        len(normalized.scene.points),
        len(normalized.scene.shapes),
        len(normalized.scene.animations),
    )
    return normalized


@app.get("/health")
async def health() -> dict[str, Any]:
    provider = normalize_provider(settings.model_provider)
    logger.info("health check provider=%s model=%s", provider, get_default_model(provider))
    return {
        "ok": True,
        "provider": provider,
        "model": get_default_model(provider),
        "supported_providers": sorted(SUPPORTED_PROVIDERS),
    }


@app.post("/solve", response_model=SolveResponse, response_model_by_alias=True)
async def solve(request: SolveRequest, authorization: str | None = Header(default=None)) -> SolveResponse:
    request_start = time.perf_counter()
    provider = normalize_provider(request.provider)
    logger.info(
        "solve request received provider=%s problem_chars=%s has_image=%s auth_header=%s",
        provider,
        len(request.problem.strip()),
        bool(request.image),
        bool(authorization),
    )
    if not request.problem.strip() and not request.image:
        raise HTTPException(status_code=400, detail="题目文本和图片不能同时为空")

    api_key = get_api_key(authorization) or get_default_api_key(provider)
    upstream_base_url = request.upstream_base_url or get_default_upstream_base_url(provider)
    if not api_key and not (provider == "openai_compatible" and is_local_base_url(upstream_base_url)):
        raise HTTPException(status_code=400, detail="缺少 API Key，请在应用端输入或在后端环境变量中配置对应服务商的密钥")

    try:
        image_part = parse_image_data_url(request.image) if request.image else None
        target_model = request.model or get_default_model(provider)
        if image_part and not model_supports_images(provider, target_model):
            raise HTTPException(status_code=400, detail=f"当前模型不支持图片输入: {target_model}")
        if provider == "openai_compatible":
            response_obj = await request_openai_compatible(
                api_key,
                request.problem,
                image_part,
                model_name=target_model,
                base_url=upstream_base_url,
            )
            response_text = extract_text_from_openai(response_obj)
        else:
            response_obj = await request_gemini(api_key, request.problem, image_part, model_name=target_model)
            response_text = extract_text_from_gemini(response_obj)
        result = normalize_result(extract_json(response_text))
        
        # Save to history
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO history (timestamp, problem, image, response_json) VALUES (?, ?, ?, ?)",
                (time.time(), request.problem, request.image, result.model_dump_json(by_alias=True))
            )
            await db.commit()

        logger.info("solve request completed elapsed=%.2fs", time.perf_counter() - request_start)
        return result
    except BadRequestError as exc:
        logger.warning("solve bad request elapsed=%.2fs error=%s", time.perf_counter() - request_start, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValidationError as exc:
        logger.exception("solve validation error elapsed=%.2fs", time.perf_counter() - request_start)
        raise HTTPException(status_code=502, detail=f"模型响应结构不符合要求: {exc}") from exc
    except UpstreamResponseError as exc:
        logger.warning("solve upstream response error elapsed=%.2fs error=%s", time.perf_counter() - request_start, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except (httpx.RequestError, Exception) as exc:
        elapsed = time.perf_counter() - request_start
        error_msg = str(exc)
        lc_msg = error_msg.lower()
        
        # 统一处理已知且不需要堆栈打印的网络波动或模型繁忙问题
        if any(k in lc_msg for k in ["503", "high demand", "disconnected", "sending a response", "connection"]):
            logger.warning("solve network/busy error elapsed=%.2fs error=%s", elapsed, error_msg)
            raise HTTPException(status_code=503, detail="网络连接波动或模型当前负载过高，请 10 秒后重试。")
        
        if "429" in lc_msg or "quota" in lc_msg:
            logger.warning("solve quota exceeded elapsed=%.2fs error=429 Too Many Requests", elapsed)
            raise HTTPException(status_code=429, detail="API 额度已用尽或请求过于频繁（429）。")
            
        if "401" in lc_msg or "key" in lc_msg or "permission" in lc_msg:
            logger.warning("solve auth failed elapsed=%.2fs error=401 Unauthorized", elapsed)
            raise HTTPException(status_code=401, detail="API Key 无效、已过期或无权使用该模型。")

        # 对于未识别的真正致命错误，保留详细记录
        logger.exception("solve unexpected exception elapsed=%.2fs", elapsed)
        raise HTTPException(status_code=502, detail=f"服务暂时不可用: {error_msg}")


@app.get("/history", response_model=list[HistoryItem], response_model_by_alias=True)
async def get_history(limit: int = 20) -> list[HistoryItem]:
    limit = min(max(limit, 1), 100)
    items = []
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, timestamp, problem, image, response_json FROM history ORDER BY id DESC LIMIT ?",
            (limit,)
        ) as cursor:
            async for row in cursor:
                try:
                    items.append(
                        HistoryItem(
                            id=row["id"],
                            timestamp=row["timestamp"],
                            problem=row["problem"],
                            image=row["image"],
                            response_data=SolveResponse.model_validate_json(row["response_json"])
                        )
                    )
                except Exception as e:
                    logger.warning("Failed to parse history row %s: %s", row["id"], e)
    return items


@app.delete("/history")
async def clear_history():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM history")
        await db.commit()
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
