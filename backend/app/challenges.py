"""Generate local-only visual challenges without exposing their answers."""

from base64 import b64encode
from dataclasses import dataclass
from io import BytesIO
import hashlib
import math
from pathlib import Path
import random
import secrets

from PIL import Image, ImageDraw, ImageFont, ImageOps


class _RandomSource:
    """Common ``randbelow``/``choice`` surface over either ``secrets`` (the
    default, non-reproducible) or a seeded ``random.Random`` (reproducible
    for a given challenge_rng() material). Every call site in this module
    goes through a source instance instead of the ``secrets`` module
    directly so a single optional ``rng`` parameter controls determinism
    without duplicating each function's generation logic."""

    def __init__(self, rng: random.Random | None) -> None:
        self._rng = rng

    def randbelow(self, n: int) -> int:
        return self._rng.randrange(n) if self._rng is not None else secrets.randbelow(n)

    def choice(self, sequence):
        return self._rng.choice(sequence) if self._rng is not None else secrets.choice(sequence)


def challenge_rng(seed: str, kit_root: str, config_hash: str, stage_index: int) -> random.Random:
    """Return a ``random.Random`` reproducible for one (seed, kit, config,
    stage) combination, so the same experiment condition regenerates the
    same problem and visual variant for a fresh token, without exposing the
    answer any differently than today (still checked only via
    ``secrets.compare_digest`` server-side)."""
    material = f"{seed}:{kit_root}:{config_hash}:{stage_index}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    return random.Random(digest)


@dataclass(frozen=True)
class DigitChallenge:
    answer: str
    image_data_url: str
    variant: str


@dataclass(frozen=True)
class TextChallenge:
    answer: str
    image_data_url: str
    variant: str


@dataclass(frozen=True)
class MathChallenge:
    answer: str
    prompt: str
    operator: str
    variant: str


@dataclass(frozen=True)
class ImageGridChallenge:
    answer: str
    category_label: str
    cell_image_data_urls: tuple[str, ...]
    variant: str


@dataclass(frozen=True)
class AreaSelectChallenge:
    answer: str
    category_label: str
    image_data_url: str
    columns: int
    rows: int
    variant: str


@dataclass(frozen=True)
class RotationChallenge:
    answer: str
    image_data_url: str
    step_count: int
    variant: str


PALETTES = (
    ("blue", "#eef5ff", (25, 76, 145), (73, 128, 195)),
    ("violet", "#f2efff", (83, 45, 132), (139, 92, 190)),
    ("mint", "#edf9f5", (19, 91, 76), (50, 145, 118)),
)

WATERMARK_TEXT = "AI RECOGNITION PROHIBITED"

ROTATION_SCENE_DIRECTORY = Path(__file__).parent / "assets" / "rotation"
ROTATION_SCENE_FILES = (
    "cape-romain-lighthouse.jpg",
    "hale-lighthouse.jpg",
    "house-and-trees.jpg",
    "perth-skyline.jpg",
    "philadelphia-skyline.jpg",
    "road-and-sky.jpg",
    "seattle-skyline.jpg",
    "water-horizon.jpg",
)
ROTATION_SCENE_PATHS = tuple(
    ROTATION_SCENE_DIRECTORY / file_name for file_name in ROTATION_SCENE_FILES
)


def create_digit_challenge(
    digit_count: int = 5,
    *,
    cell_width_px: int = 52,
    max_rotation_degrees: int = 8,
    noise_dot_count: int = 140,
    noise_line_count: int = 11,
    watermark_enabled: bool = False,
    rng: random.Random | None = None,
) -> DigitChallenge:
    """Return a randomized digit answer and a noisy PNG representation.

    Visual clutter is controlled only by concrete parameters. Pass ``rng``
    (see ``challenge_rng``) to make the answer, palette, and clutter
    reproducible for one experiment condition; omit it for the default,
    cryptographically random behavior.
    """
    source = _RandomSource(rng)
    answer = "".join(str(source.randbelow(10)) for _ in range(digit_count))
    variant, background, foreground, accent = PALETTES[source.randbelow(len(PALETTES))]
    image = Image.new("RGB", (320, 100), background)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=52)

    for _ in range(noise_dot_count):
        x = source.randbelow(image.width)
        y = source.randbelow(image.height)
        radius = 1 + source.randbelow(2)
        color = accent if source.randbelow(3) else foreground
        draw.ellipse((x, y, x + radius, y + radius), fill=color)

    for _ in range(noise_line_count):
        start = (source.randbelow(image.width), source.randbelow(image.height))
        end = (source.randbelow(image.width), source.randbelow(image.height))
        draw.line((start, end), fill=accent, width=1 + source.randbelow(3))

    left = (image.width - cell_width_px * digit_count) // 2
    for index, digit in enumerate(answer):
        glyph = Image.new("RGBA", (64, 76), (0, 0, 0, 0))
        glyph_draw = ImageDraw.Draw(glyph)
        glyph_draw.text((16, 5), digit, font=font, fill=foreground + (255,))
        angle = source.randbelow(2 * max_rotation_degrees + 1) - max_rotation_degrees
        glyph = glyph.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        image.paste(glyph, (left + index * cell_width_px, 11), glyph)

    if watermark_enabled:
        _apply_diagonal_watermark(image, accent)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    encoded = b64encode(output.getvalue()).decode("ascii")
    return DigitChallenge(
        answer=answer,
        image_data_url=f"data:image/png;base64,{encoded}",
        variant=variant,
    )


# Upper-case alphanumerics minus the visually ambiguous glyphs (I, O, 0, 1) so a
# human reading the distorted image is not penalised for an unavoidable misread.
TEXT_CHALLENGE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def create_text_challenge(
    length: int = 6,
    *,
    cell_width_px: int = 54,
    max_rotation_degrees: int = 10,
    noise_dot_count: int = 150,
    noise_line_count: int = 12,
    watermark_enabled: bool = False,
    rng: random.Random | None = None,
) -> TextChallenge:
    """Return a randomized alphanumeric answer and a noisy PNG of it.

    Mirrors ``create_digit_challenge`` but over an alphanumeric alphabet, for a
    classic text CAPTCHA. The answer is validated server-side only; pass ``rng``
    (see ``challenge_rng``) for reproducibility, omit it for the default
    cryptographically random behavior.
    """
    source = _RandomSource(rng)
    answer = "".join(source.choice(TEXT_CHALLENGE_ALPHABET) for _ in range(length))
    variant, background, foreground, accent = PALETTES[source.randbelow(len(PALETTES))]
    width = max(320, cell_width_px * length + 36)
    image = Image.new("RGB", (width, 110), background)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=46)

    for _ in range(noise_dot_count):
        x = source.randbelow(image.width)
        y = source.randbelow(image.height)
        radius = 1 + source.randbelow(2)
        color = accent if source.randbelow(3) else foreground
        draw.ellipse((x, y, x + radius, y + radius), fill=color)

    for _ in range(noise_line_count):
        start = (source.randbelow(image.width), source.randbelow(image.height))
        end = (source.randbelow(image.width), source.randbelow(image.height))
        draw.line((start, end), fill=accent, width=1 + source.randbelow(3))

    left = (image.width - cell_width_px * length) // 2
    for index, character in enumerate(answer):
        glyph = Image.new("RGBA", (64, 84), (0, 0, 0, 0))
        glyph_draw = ImageDraw.Draw(glyph)
        glyph_draw.text((12, 8), character, font=font, fill=foreground + (255,))
        angle = source.randbelow(2 * max_rotation_degrees + 1) - max_rotation_degrees
        glyph = glyph.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        image.paste(glyph, (left + index * cell_width_px, 13), glyph)

    if watermark_enabled:
        _apply_diagonal_watermark(image, accent)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    encoded = b64encode(output.getvalue()).decode("ascii")
    return TextChallenge(
        answer=answer,
        image_data_url=f"data:image/png;base64,{encoded}",
        variant=variant,
    )


def _apply_diagonal_watermark(image: Image.Image, color: tuple[int, int, int]) -> None:
    """Overlay a repeating, semi-transparent diagonal warning-text band."""
    watermark_font = ImageFont.load_default(size=16)
    band = Image.new("RGBA", (image.width * 2, 60), (0, 0, 0, 0))
    band_draw = ImageDraw.Draw(band)
    text_width = band_draw.textlength(WATERMARK_TEXT, font=watermark_font)
    x = 0
    while x < band.width:
        band_draw.text((x, 5), WATERMARK_TEXT, font=watermark_font, fill=color + (120,))
        x += int(text_width) + 40

    band = band.rotate(-18, resample=Image.Resampling.BICUBIC, expand=True)
    paste_x = (image.width - band.width) // 2
    paste_y = (image.height - band.height) // 2
    image.paste(band, (paste_x, paste_y), band)


def create_math_challenge(
    min_operand: int = 1,
    max_operand: int = 12,
    operators: tuple[str, ...] = ("addition", "subtraction", "multiplication"),
    *,
    rng: random.Random | None = None,
) -> MathChallenge:
    """Return a small randomized arithmetic problem with a non-negative answer.

    Pass ``rng`` (see ``challenge_rng``) for a reproducible problem and
    palette; omit it for the default, cryptographically random behavior.
    """
    source = _RandomSource(rng)
    operator = source.choice(operators)

    if operator == "multiplication":
        multiplication_min = max(2, min(min_operand, 9))
        multiplication_max = max(multiplication_min, min(max_operand, 9))
        operand_span = multiplication_max - multiplication_min + 1
        left = multiplication_min + source.randbelow(operand_span)
        right = multiplication_min + source.randbelow(operand_span)
        symbol = "×"
        answer = left * right
    else:
        operand_span = max_operand - min_operand + 1
        left = min_operand + source.randbelow(operand_span)
        right = min_operand + source.randbelow(operand_span)
        if operator == "subtraction":
            left, right = max(left, right), min(left, right)
            symbol = "−"
            answer = left - right
        else:
            symbol = "+"
            answer = left + right

    variant = PALETTES[source.randbelow(len(PALETTES))][0]
    return MathChallenge(
        answer=str(answer),
        prompt=f"{left} {symbol} {right} = ?",
        operator=operator,
        variant=variant,
    )


# Every icon is drawn from primitives (no photographs, no third-party assets,
# no bundled dataset) so the grid challenge needs no external CAPTCHA service
# or image library — see custom-digit's excluded_behaviors for why that
# matters here too.
ICON_CATEGORIES = (
    "car", "umbrella", "bicycle", "traffic light", "star", "tree",
    "house", "envelope", "heart", "cup", "cloud", "clock",
)


def _star_points(cx: float, cy: float, radius: float) -> list[tuple[float, float]]:
    points = []
    for index in range(10):
        angle = math.pi / 2 + index * math.pi / 5
        point_radius = radius if index % 2 == 0 else radius * 0.45
        points.append((cx + point_radius * math.cos(angle), cy - point_radius * math.sin(angle)))
    return points


def _draw_icon(draw: ImageDraw.ImageDraw, category: str, box: tuple[float, float, float, float], color: tuple[int, int, int]) -> None:
    """Draw one simple, hand-coded icon glyph inside ``box``."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cx, cy = x0 + w / 2, y0 + h / 2

    if category == "car":
        draw.rounded_rectangle((x0 + w * 0.08, y0 + h * 0.38, x1 - w * 0.08, y0 + h * 0.68), radius=int(h * 0.1), outline=color, width=3)
        draw.arc((x0 + w * 0.22, y0 + h * 0.16, x1 - w * 0.22, y0 + h * 0.58), start=200, end=340, fill=color, width=3)
        wheel_r = h * 0.09
        for wheel_x in (x0 + w * 0.26, x1 - w * 0.26):
            draw.ellipse((wheel_x - wheel_r, y0 + h * 0.62, wheel_x + wheel_r, y0 + h * 0.62 + 2 * wheel_r), outline=color, width=3)
    elif category == "umbrella":
        draw.arc((x0 + w * 0.14, y0 + h * 0.22, x1 - w * 0.14, y0 + h * 0.72), start=180, end=360, fill=color, width=4)
        draw.line((cx, y0 + h * 0.47, cx, y1 - h * 0.12), fill=color, width=3)
        draw.arc((cx - w * 0.1, y1 - h * 0.22, cx + w * 0.02, y1 - h * 0.06), start=0, end=180, fill=color, width=3)
    elif category == "bicycle":
        wheel_r = h * 0.17
        left_c = (x0 + w * 0.28, y1 - h * 0.28)
        right_c = (x1 - w * 0.28, y1 - h * 0.28)
        seat = (cx - w * 0.05, y0 + h * 0.32)
        draw.ellipse((left_c[0] - wheel_r, left_c[1] - wheel_r, left_c[0] + wheel_r, left_c[1] + wheel_r), outline=color, width=3)
        draw.ellipse((right_c[0] - wheel_r, right_c[1] - wheel_r, right_c[0] + wheel_r, right_c[1] + wheel_r), outline=color, width=3)
        draw.line((left_c[0], left_c[1], seat[0], seat[1]), fill=color, width=3)
        draw.line((seat[0], seat[1], right_c[0], right_c[1]), fill=color, width=3)
        draw.line((seat[0], seat[1] + h * 0.06, right_c[0], right_c[1]), fill=color, width=3)
        draw.line((left_c[0], left_c[1], seat[0] + w * 0.1, seat[1] + h * 0.02), fill=color, width=3)
    elif category == "traffic light":
        body = (cx - w * 0.13, y0 + h * 0.12, cx + w * 0.13, y1 - h * 0.12)
        draw.rounded_rectangle(body, radius=int(w * 0.06), outline=color, width=3)
        for index in range(3):
            light_y = y0 + h * 0.24 + index * h * 0.18
            draw.ellipse((cx - w * 0.07, light_y, cx + w * 0.07, light_y + h * 0.14), outline=color, width=2)
    elif category == "star":
        draw.polygon(_star_points(cx, cy, min(w, h) * 0.42), outline=color, width=3)
    elif category == "tree":
        draw.polygon(
            [(cx, y0 + h * 0.12), (x0 + w * 0.22, y0 + h * 0.52), (x1 - w * 0.22, y0 + h * 0.52)],
            outline=color, width=3,
        )
        draw.polygon(
            [(cx, y0 + h * 0.32), (x0 + w * 0.16, y0 + h * 0.68), (x1 - w * 0.16, y0 + h * 0.68)],
            outline=color, width=3,
        )
        draw.rectangle((cx - w * 0.045, y0 + h * 0.68, cx + w * 0.045, y1 - h * 0.1), outline=color, width=3)
    elif category == "house":
        draw.polygon([(cx, y0 + h * 0.14), (x0 + w * 0.14, y0 + h * 0.46), (x1 - w * 0.14, y0 + h * 0.46)], outline=color, width=3)
        draw.rectangle((x0 + w * 0.2, y0 + h * 0.46, x1 - w * 0.2, y1 - h * 0.12), outline=color, width=3)
        draw.rectangle((cx - w * 0.06, y1 - h * 0.34, cx + w * 0.06, y1 - h * 0.12), outline=color, width=2)
    elif category == "envelope":
        draw.rectangle((x0 + w * 0.12, y0 + h * 0.26, x1 - w * 0.12, y1 - h * 0.26), outline=color, width=3)
        draw.line((x0 + w * 0.12, y0 + h * 0.26, cx, cy), fill=color, width=3)
        draw.line((x1 - w * 0.12, y0 + h * 0.26, cx, cy), fill=color, width=3)
    elif category == "heart":
        lobe_r = w * 0.16
        draw.ellipse((cx - 2 * lobe_r, y0 + h * 0.24, cx, y0 + h * 0.24 + 2 * lobe_r), outline=color, width=3)
        draw.ellipse((cx, y0 + h * 0.24, cx + 2 * lobe_r, y0 + h * 0.24 + 2 * lobe_r), outline=color, width=3)
        draw.polygon([(x0 + w * 0.2, y0 + h * 0.42), (cx, y1 - h * 0.14), (x1 - w * 0.2, y0 + h * 0.42)], outline=color, width=3)
    elif category == "cup":
        draw.rounded_rectangle((x0 + w * 0.22, y0 + h * 0.2, x1 - w * 0.22, y1 - h * 0.16), radius=int(w * 0.04), outline=color, width=3)
        draw.arc((x1 - w * 0.3, y0 + h * 0.32, x1 + w * 0.06, y1 - h * 0.32), start=280, end=80, fill=color, width=3)
    elif category == "cloud":
        base_y = y0 + h * 0.64
        puffs = ((x0 + w * 0.32, 0.16), (cx + w * 0.02, 0.23), (x1 - w * 0.28, 0.18))
        for puff_x, puff_r in puffs:
            radius = h * puff_r
            draw.ellipse((puff_x - radius, base_y - 2 * radius, puff_x + radius, base_y), outline=color, width=3)
        draw.line((x0 + w * 0.16, base_y, x1 - w * 0.16, base_y), fill=color, width=3)
    elif category == "clock":
        radius = min(w, h) * 0.32
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color, width=3)
        draw.line((cx, cy, cx, cy - radius * 0.6), fill=color, width=3)
        draw.line((cx, cy, cx + radius * 0.45, cy + radius * 0.1), fill=color, width=3)


def create_image_grid_challenge(
    grid_size: int = 3, min_matches: int = 2, max_matches: int = 4, *, rng: random.Random | None = None
) -> ImageGridChallenge:
    """Return a randomized 'select every square with X' grid challenge.

    Each cell is an independently generated 100x100 PNG so the client never
    receives a combined image it would need pixel coordinates to answer;
    the submitted answer is the sorted, comma-joined set of matching cell
    indices. Icon category, palette, per-cell rotation/scale jitter, and
    which cells match are all re-rolled on every call for visual variety.
    Pass ``rng`` (see ``challenge_rng``) to make all of that reproducible
    for one experiment condition; omit it for the default, cryptographically
    random behavior.
    """
    source = _RandomSource(rng)
    cell_count = grid_size * grid_size
    target = source.choice(ICON_CATEGORIES)
    distractors = [category for category in ICON_CATEGORIES if category != target]

    match_low = max(1, min(min_matches, cell_count - 1))
    match_high = max(match_low, min(max_matches, cell_count - 1))
    match_count = match_low + source.randbelow(match_high - match_low + 1)

    categories = [target] * match_count + [
        source.choice(distractors) for _ in range(cell_count - match_count)
    ]
    for index in range(len(categories) - 1, 0, -1):
        swap_index = source.randbelow(index + 1)
        categories[index], categories[swap_index] = categories[swap_index], categories[index]

    variant, background, foreground, accent = PALETTES[source.randbelow(len(PALETTES))]
    cell_urls: list[str] = []
    for category in categories:
        cell = Image.new("RGB", (100, 100), background)
        glyph = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        glyph_draw = ImageDraw.Draw(glyph)
        icon_color = accent if source.randbelow(4) == 0 else foreground
        scale = 0.82 + source.randbelow(10) / 100
        margin = (100 - 100 * scale) / 2
        _draw_icon(glyph_draw, category, (margin, margin, 100 - margin, 100 - margin), icon_color)
        angle = source.randbelow(21) - 10
        glyph = glyph.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
        offset = (source.randbelow(7) - 3, source.randbelow(7) - 3)
        cell.paste(glyph, offset, glyph)

        output = BytesIO()
        cell.save(output, format="PNG", optimize=True)
        cell_urls.append(f"data:image/png;base64,{b64encode(output.getvalue()).decode('ascii')}")

    correct_indices = sorted(index for index, category in enumerate(categories) if category == target)
    return ImageGridChallenge(
        answer=",".join(str(index) for index in correct_indices),
        category_label=target,
        cell_image_data_urls=tuple(cell_urls),
        variant=variant,
    )


def create_rotation_challenge(
    step_count: int = 8, *, size: int = 200, rng: random.Random | None = None
) -> RotationChallenge:
    """Return a 'rotate the picture upright' challenge, validated server-side.

    The server renders an orientable scene tilted by a random non-zero number of
    discrete steps and keeps the number of forward steps that returns it upright
    as the answer; the client rotates the image by eye and submits its step
    count. The answer is derived from the server's secret tilt (never sent to the
    client), so unlike a client-side angle check it cannot be read from the page.
    Pass ``rng`` (see ``challenge_rng``) for reproducibility.
    """
    source = _RandomSource(rng)
    variant, background, _, _ = PALETTES[source.randbelow(len(PALETTES))]
    scene_path = ROTATION_SCENE_PATHS[source.randbelow(len(ROTATION_SCENE_PATHS))]
    tilt_steps = 1 + source.randbelow(step_count - 1)  # 1..step_count-1 (never already upright)
    with Image.open(scene_path) as source_image:
        scene = ImageOps.fit(
            source_image.convert("RGB"),
            (size, size),
            method=Image.Resampling.LANCZOS,
        )
    tilted = scene.rotate(
        -tilt_steps * (360 / step_count),
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor=background,
    )
    output = BytesIO()
    tilted.save(output, format="PNG", optimize=True)
    encoded = b64encode(output.getvalue()).decode("ascii")
    # Client rotates forward by k steps; upright when (tilt + k) % step_count == 0.
    answer = (step_count - tilt_steps) % step_count
    return RotationChallenge(
        answer=str(answer),
        image_data_url=f"data:image/png;base64,{encoded}",
        step_count=step_count,
        variant=variant,
    )


def create_area_select_challenge(
    columns: int = 3, rows: int = 2, *, cell_px: int = 120, rng: random.Random | None = None
) -> AreaSelectChallenge:
    """Return a 'click the X' single-scene challenge.

    One continuous image is divided into ``columns`` x ``rows`` regions, each
    holding a hand-drawn icon; exactly one region holds the target category.
    The answer is that region's index (row-major); the client maps a click
    position to a region index and submits it, so the answer stays a simple
    server-checked string (no pixel coordinates leave the client as the
    answer). Pass ``rng`` (see ``challenge_rng``) for reproducibility; omit it
    for the default cryptographically random behavior.
    """
    source = _RandomSource(rng)
    cell_count = columns * rows
    target = source.choice(ICON_CATEGORIES)
    distractor_pool = [category for category in ICON_CATEGORIES if category != target]
    # Sample distinct distractors so no second cell accidentally shows the
    # target category (which would make the answer ambiguous).
    for index in range(len(distractor_pool) - 1, 0, -1):
        swap_index = source.randbelow(index + 1)
        distractor_pool[index], distractor_pool[swap_index] = (
            distractor_pool[swap_index],
            distractor_pool[index],
        )
    categories = distractor_pool[: cell_count - 1] + [target]
    for index in range(len(categories) - 1, 0, -1):
        swap_index = source.randbelow(index + 1)
        categories[index], categories[swap_index] = categories[swap_index], categories[index]
    target_index = categories.index(target)

    variant, background, foreground, accent = PALETTES[source.randbelow(len(PALETTES))]
    image = Image.new("RGB", (columns * cell_px, rows * cell_px), background)
    draw = ImageDraw.Draw(image)
    for index, category in enumerate(categories):
        col = index % columns
        row = index // columns
        x0 = col * cell_px
        y0 = row * cell_px
        icon_color = accent if source.randbelow(4) == 0 else foreground
        scale = 0.6 + source.randbelow(12) / 100
        margin = cell_px * (1 - scale) / 2
        _draw_icon(
            draw,
            category,
            (x0 + margin, y0 + margin, x0 + cell_px - margin, y0 + cell_px - margin),
            icon_color,
        )

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    encoded = b64encode(output.getvalue()).decode("ascii")
    return AreaSelectChallenge(
        answer=str(target_index),
        category_label=target,
        image_data_url=f"data:image/png;base64,{encoded}",
        columns=columns,
        rows=rows,
        variant=variant,
    )
