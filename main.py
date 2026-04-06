import json
import random
from typing import Dict, List, Optional

import flet as ft


JSON_FILE = "hanja_data.json"

LEVEL_ORDER = ["8급", "7급", "6급", "준5급", "5급", "준4급", "4급", "준3급", "3급"]

LEVEL_RANGE_MAP: Dict[str, List[str]] = {
    "8급": ["A-1", "A-2", "A-3"],
    "7급": ["A-4", "A-5", "A-6"],
    "6급": ["B-1", "B-2", "B-3", "B-4", "B-5", "B-6"],
    "준5급": ["C-1", "C-2", "C-3", "C-4", "C-5", "C-6"],
    "5급": ["D-1", "D-2", "D-3", "D-4", "D-5", "D-6", "E-1", "E-2", "E-3", "E-4", "E-5", "E-6"],
    "준4급": ["F-1", "F-2", "F-3", "F-4", "F-5", "F-6", "G-1", "G-2", "G-3", "G-4", "G-5", "G-6"],
    "4급": ["H-1", "H-2", "H-3", "H-4", "H-5", "H-6", "I-1", "I-2", "I-3", "I-4", "I-5", "I-6"],
    "준3급": [
        "J1-1", "J1-2", "J1-3",
        "J2-1", "J2-2", "J2-3",
        "J3-1", "J3-2", "J3-3",
        "J4-1", "J4-2", "J4-3",
        "J5-1", "J5-2", "J5-3",
    ],
    "3급": ["K-1", "K-2", "K-3", "K-4", "K-5", "K-6"],
}

BG_PINK = "#F1DADF"
CARD_WHITE = "#F4F4F4"
BLACK_BTN = "#272222"
BLUE = "#0D99FF"
SOFT_BLUE = "#3B7DE0"
DARK_BLUE = "#233D99"
TEXT_GRAY = "#9A9A9A"
BORDER = "#2A2A2A"


def safe_text(v: object) -> str:
    if v is None:
        return ""
    return str(v).strip()


def normalize_step_value(v: str) -> str:
    s = str(v).strip().upper().replace(" ", "")
    if not s:
        return ""
    if "-" in s:
        a, b = s.split("-", 1)
        if a and b:
            return f"{a}-{b}"
    return s


def compact_step_value(v: str) -> str:
    return str(v).replace("-", "").strip().upper()


def load_json_items(page: ft.Page) -> List[Dict[str, str]]:
    data = None
    candidate_paths: List[str] = []

    try:
        candidate_paths.append(page.get_asset_path(JSON_FILE))
    except Exception:
        pass

    candidate_paths.extend(
        [
            JSON_FILE,
            f"assets/{JSON_FILE}",
            f"/{JSON_FILE}",
            f"/assets/{JSON_FILE}",
        ]
    )

    seen = set()
    unique_paths: List[str] = []
    for path in candidate_paths:
        if path and path not in seen:
            unique_paths.append(path)
            seen.add(path)

    for path in unique_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            break
        except Exception:
            continue

    if not isinstance(data, list):
        return []

    cleaned: List[Dict[str, str]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        item = {
            "번호": safe_text(row.get("번호", "")),
            "한자": safe_text(row.get("한자", "")),
            "뜻": safe_text(row.get("뜻", "")),
            "독음": safe_text(row.get("독음", "")),
            "급수": safe_text(row.get("급수", "")),
            "단계": normalize_step_value(safe_text(row.get("단계", ""))),
            "타입": safe_text(row.get("타입", "")),
            "표시단계": compact_step_value(safe_text(row.get("표시단계", row.get("단계", "")))),
        }
        cleaned.append(item)
    return cleaned


def main(page: ft.Page):
    page.title = "한자 공부"
    page.bgcolor = BG_PINK
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    all_items = load_json_items(page)

    state = {
        "screen": "home",
        "selected_level": None,
        "selected_ranges": [],
        "selected_category": None,
        "selected_mode": None,
        "random_order": False,
        "quiz_direction": "한자→뜻",
        "items": [],
        "current_index": 0,
        "show_card_back": False,
        "quiz_selected_index": None,
        "quiz_checked": False,
        "quiz_choices": [],
        "quiz_item_key": None,
        "correct_count": 0,
        "wrong_count": 0,
        "error_message": "",
        "is_finished": False,
        "quiz_result_message": "",
        "wrong_items": [],
        "wrong_note_items": [],
        "unanswered_items": [],
        "review_wrong_mode": False,
        "card_finish_message": "끝났습니다.\n다시 반복 할까요?",
        "last_main_screen": "study_type",
        "wrong_note_back_screen": "home",
    }

    def vw(ratio: float, min_v: Optional[int] = None, max_v: Optional[int] = None) -> int:
        pw = page.width if page.width and page.width > 0 else 390
        base = int(pw * ratio)
        if min_v is not None:
            base = max(base, min_v)
        if max_v is not None:
            base = min(base, max_v)
        return base

    def is_mobile_narrow() -> bool:
        pw = page.width if page.width and page.width > 0 else 390
        return pw <= 430

    def card_w() -> int:
        pw = page.width if page.width and page.width > 0 else 390
        if is_mobile_narrow():
            return int(pw * 0.96)
        return min(int(pw * 0.92), 430)

    def card_h() -> int:
        ph = page.height if page.height and page.height > 0 else 844
        if is_mobile_narrow():
            return int(ph * 0.90)
        return min(int(ph * 0.88), 840)

    def title_size() -> int:
        return vw(0.102, 30, 44)

    def top_label(title_top: str) -> ft.Control:
        return ft.Container(
            width=card_w(),
            padding=ft.padding.only(left=8, top=4, bottom=6),
            content=ft.Text(title_top, size=14, color=TEXT_GRAY),
        )

    def black_button(
        text: str,
        on_click=None,
        disabled: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        font_size: int = 22,
    ):
        return ft.Container(
            width=width or 132,
            height=height or 58,
            border_radius=22,
            bgcolor=BLACK_BTN if not disabled else "#CEC6C6",
            alignment=ft.Alignment(0, 0),
            ink=not disabled,
            on_click=None if disabled else on_click,
            content=ft.Text(
                text,
                size=font_size,
                weight=ft.FontWeight.BOLD,
                color="white" if not disabled else "#9F8F8F",
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def back_button(on_click=None):
        return ft.Container(
            width=58,
            height=46,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=on_click,
            content=ft.Text("|◁", size=34, weight=ft.FontWeight.BOLD, color="black"),
        )

    def arrow_button(icon_name: str, on_click=None, disabled: bool = False):
        btn = 76 if is_mobile_narrow() else 88
        icon = 54 if is_mobile_narrow() else 66
        return ft.Container(
            width=btn,
            height=btn,
            border_radius=btn // 2,
            alignment=ft.Alignment(0, 0),
            ink=not disabled,
            on_click=None if disabled else on_click,
            content=ft.Icon(icon_name, size=icon, color="#D7D7D7" if disabled else BLUE),
        )

    def center_circle_button(text: str, on_click=None):
        outer = 76 if is_mobile_narrow() else 88
        inner = 62 if is_mobile_narrow() else 72
        font_size = 28 if text == "?" else 20 if text == "정답" else 28
        if not is_mobile_narrow():
            font_size = 34 if text == "?" else 24 if text == "정답" else 34

        return ft.Container(
            width=outer,
            height=outer,
            border_radius=outer // 2,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=on_click,
            content=ft.Container(
                width=inner,
                height=inner,
                border_radius=inner // 2,
                border=ft.border.all(4, BLUE),
                alignment=ft.Alignment(0, 0),
                content=ft.Text(text, size=font_size, weight=ft.FontWeight.BOLD, color=BLUE),
            ),
        )

    def page_shell(title_top: str, content: ft.Control, back_click=None, back_left: int = 16, back_bottom: int = 50) -> ft.Control:
        return ft.Column(
            [
                top_label(title_top),
                ft.Container(
                    width=card_w(),
                    height=card_h(),
                    bgcolor=CARD_WHITE,
                    border_radius=18,
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                left=0,
                                top=0,
                                right=0,
                                bottom=0,
                                padding=ft.padding.only(left=16, right=16, top=16, bottom=16),
                                content=content,
                            ),
                            ft.Container(
                                left=back_left,
                                bottom=back_bottom,
                                content=back_button(back_click) if back_click else ft.Container(),
                            ),
                        ]
                    ),
                ),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def level_badge(level: str):
        return ft.Container(
            border=ft.border.all(2, BLUE),
            border_radius=ft.border_radius.only(top_left=20, top_right=20, bottom_left=20, bottom_right=0),
            padding=ft.padding.symmetric(horizontal=10, vertical=7),
            content=ft.Row(
                [
                    ft.Text(level, size=15, weight=ft.FontWeight.BOLD, color="black"),
                    ft.Text("+", size=22, weight=ft.FontWeight.BOLD, color=BLUE),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def split_page_title(level: str, text: str, badge_left: int = 4, badge_top: int = 14, title_top: int = 18):
        return ft.Container(
            width=card_w() - 30,
            height=120,
            content=ft.Stack(
                controls=[
                    ft.Container(left=badge_left, top=badge_top, content=level_badge(level)),
                    ft.Container(
                        left=0,
                        right=0,
                        top=title_top,
                        alignment=ft.Alignment(0, -1),
                        content=ft.Text(
                            text,
                            size=title_size(),
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                ]
            ),
        )

    def level_button(label: str, selected: bool, on_click=None):
        return ft.Container(
            width=74,
            height=74,
            border_radius=18,
            bgcolor="#F2E8B8" if selected else SOFT_BLUE,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=on_click,
            content=ft.Text(
                label,
                size=20,
                weight=ft.FontWeight.BOLD,
                color="black" if selected else "white",
            ),
        )

    def range_button(label: str, selected: bool, on_click=None):
        return ft.Container(
            width=82 if len(label) >= 4 else 78,
            height=62,
            border_radius=10,
            bgcolor=DARK_BLUE if selected else SOFT_BLUE,
            alignment=ft.Alignment(0, 0),
            ink=True,
            on_click=on_click,
            content=ft.Text(
                label,
                size=18,
                weight=ft.FontWeight.BOLD,
                color="white",
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def type_block(title: str, card_selected: bool, quiz_selected: bool, on_card=None, on_quiz=None):
        return ft.Container(
            width=card_w() - 50,
            height=156,
            border=ft.border.all(1.4, BLUE),
            border_radius=18,
            padding=ft.padding.only(left=14, right=14, top=20, bottom=14),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.EDIT_OUTLINED, size=22, color="black"),
                            ft.Text(title, size=17, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            ft.Container(
                                expand=True,
                                height=86,
                                border_radius=14,
                                bgcolor=SOFT_BLUE,
                                border=ft.border.all(3, "#18358E") if card_selected else None,
                                alignment=ft.Alignment(0, 0),
                                ink=True,
                                on_click=on_card,
                                content=ft.Text(
                                    "카드\n외우기",
                                    size=19,
                                    weight=ft.FontWeight.BOLD,
                                    color="white",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ),
                            ft.Container(width=16),
                            ft.Container(
                                expand=True,
                                height=86,
                                border_radius=14,
                                bgcolor=SOFT_BLUE,
                                border=ft.border.all(3, "#18358E") if quiz_selected else None,
                                alignment=ft.Alignment(0, 0),
                                ink=True,
                                on_click=on_quiz,
                                content=ft.Text(
                                    "퀴즈",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color="white",
                                ),
                            ),
                        ]
                    ),
                ],
                spacing=0,
            ),
        )

    def group_steps_for_ui(level: str, steps: List[str]) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {}
        if level == "준3급":
            groups["J"] = [normalize_step_value(x) for x in steps]
            return groups

        for step in steps:
            norm = normalize_step_value(step)
            if not norm:
                continue
            prefix = norm.split("-")[0]
            head = prefix[0]
            groups.setdefault(head, []).append(norm)
        return groups

    def filter_items(target_type: str) -> List[Dict[str, str]]:
        compact_ranges = [compact_step_value(x) for x in state["selected_ranges"]]
        out: List[Dict[str, str]] = []
        for item in all_items:
            if item.get("급수") != state["selected_level"]:
                continue
            if item.get("표시단계") not in compact_ranges:
                continue
            if target_type not in item.get("타입", ""):
                continue
            out.append(item.copy())
        return out

    def build_items() -> List[Dict[str, str]]:
        if not state["selected_level"] or not state["selected_ranges"] or not state["selected_category"]:
            return []
        target_type = "선정" if state["selected_category"] == "선정 한자" else "교과서"
        items = filter_items(target_type)
        if state["random_order"]:
            random.shuffle(items)
        else:
            items.sort(key=lambda x: (x.get("단계", ""), x.get("번호", "")))
        return items

    def current_item() -> Optional[Dict[str, str]]:
        if not state["items"]:
            return None
        idx = state["current_index"]
        if idx < 0 or idx >= len(state["items"]):
            return None
        return state["items"][idx]

    def get_item_key(item: Dict[str, str]) -> str:
        return f'{item.get("급수","")}_{item.get("단계","")}_{item.get("번호","")}_{item.get("타입","")}'

    def append_unique_item(target_list: List[Dict[str, str]], item: Dict[str, str]):
        key = get_item_key(item)
        if not any(get_item_key(x) == key for x in target_list):
            target_list.append(item.copy())

    def build_quiz_choices(item: Dict[str, str]) -> List[str]:
        target_type = "선정" if state["selected_category"] == "선정 한자" else "교과서"
        pool = [x for x in all_items if target_type in x.get("타입", "")]

        if state["quiz_direction"] == "한자→뜻":
            if target_type == "선정":
                correct = f"{item['뜻']} {item['독음']}".strip()
                candidates = [
                    f"{x.get('뜻', '')} {x.get('독음', '')}".strip()
                    for x in pool
                    if f"{x.get('뜻', '')} {x.get('독음', '')}".strip() != correct
                ]
            else:
                correct = item["독음"]
                candidates = [x.get("독음", "") for x in pool if x.get("독음", "") != correct]
        else:
            correct = item["한자"]
            candidates = [x.get("한자", "") for x in pool if x.get("한자", "") != correct]

        candidates = [x for x in candidates if x]
        random.shuffle(candidates)
        choices = [correct] + candidates[:3]
        while len(choices) < 4:
            choices.append(correct)
        random.shuffle(choices)
        return choices[:4]

    def refresh_quiz_choices():
        item = current_item()
        if item is None:
            state["quiz_choices"] = []
            state["quiz_item_key"] = None
            return
        key = get_item_key(item)
        if state["quiz_item_key"] != key:
            state["quiz_item_key"] = key
            state["quiz_choices"] = build_quiz_choices(item)
            state["quiz_selected_index"] = None
            state["quiz_checked"] = False
            state["quiz_result_message"] = ""

    def sort_items_for_review(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        copied = [x.copy() for x in items]
        if state["random_order"]:
            random.shuffle(copied)
            return copied
        return sorted(copied, key=lambda x: (x.get("급수", ""), x.get("단계", ""), x.get("번호", "")))

    def reset_quiz_ui_only():
        state["show_card_back"] = False
        state["quiz_selected_index"] = None
        state["quiz_checked"] = False
        state["quiz_choices"] = []
        state["quiz_item_key"] = None
        state["quiz_result_message"] = ""

    def go(screen_name: str):
        state["screen"] = screen_name
        render()

    def go_home(_=None):
        state["screen"] = "home"
        state["is_finished"] = False
        state["review_wrong_mode"] = False
        reset_quiz_ui_only()
        render()

    def open_wrong_note(back_screen: str = "home"):
        state["wrong_note_back_screen"] = back_screen
        state["screen"] = "wrong_note"
        render()

    def start_study(_=None):
        state["items"] = build_items()
        state["current_index"] = 0
        reset_quiz_ui_only()
        state["correct_count"] = 0
        state["wrong_count"] = 0
        state["error_message"] = ""
        state["is_finished"] = False
        state["wrong_items"] = []
        state["unanswered_items"] = []
        state["review_wrong_mode"] = False
        state["card_finish_message"] = "끝났습니다.\n다시 반복 할까요?"
        state["last_main_screen"] = "study_type"

        if not state["items"]:
            state["error_message"] = "데이터를 찾지 못했습니다. JSON 파일을 확인해 주세요."
            render()
            return

        state["screen"] = "card" if state["selected_mode"] == "카드 외우기" else "quiz"
        render()

    def restart_study(_=None):
        state["items"] = build_items()
        state["current_index"] = 0
        state["is_finished"] = False
        reset_quiz_ui_only()
        state["correct_count"] = 0
        state["wrong_count"] = 0
        state["wrong_items"] = []
        state["unanswered_items"] = []
        state["review_wrong_mode"] = False
        state["card_finish_message"] = "끝났습니다.\n다시 반복 할까요?"
        render()

    def exit_study(_=None):
        state["is_finished"] = False
        state["review_wrong_mode"] = False
        go(state["last_main_screen"])

    def prev_item(_=None):
        if not state["items"]:
            return
        if state["current_index"] > 0:
            state["current_index"] -= 1
            reset_quiz_ui_only()
            render()

    def next_item(_=None):
        if not state["items"]:
            return

        if state["screen"] == "quiz" and not state["quiz_checked"]:
            item = current_item()
            if item is not None:
                append_unique_item(state["unanswered_items"], item)

        if state["current_index"] < len(state["items"]) - 1:
            state["current_index"] += 1
            reset_quiz_ui_only()
        else:
            state["is_finished"] = True

        render()

    def toggle_random(_=None):
        state["random_order"] = not state["random_order"]

        if state["review_wrong_mode"]:
            state["items"] = sort_items_for_review(state["items"])
        else:
            state["items"] = build_items()

        state["current_index"] = 0
        state["is_finished"] = False
        reset_quiz_ui_only()
        render()

    def toggle_quiz_direction(_=None):
        state["quiz_direction"] = "뜻→한자" if state["quiz_direction"] == "한자→뜻" else "한자→뜻"
        reset_quiz_ui_only()
        render()

    def start_retry_incomplete_quiz(_=None):
        retry_items: List[Dict[str, str]] = []
        for x in state["wrong_items"]:
            append_unique_item(retry_items, x)
        for x in state["unanswered_items"]:
            append_unique_item(retry_items, x)

        if not retry_items:
            state["error_message"] = "오답/미응답 문제가 없습니다."
            render()
            return

        state["items"] = sort_items_for_review(retry_items)
        state["current_index"] = 0
        state["review_wrong_mode"] = True
        state["is_finished"] = False
        reset_quiz_ui_only()
        state["correct_count"] = 0
        state["wrong_count"] = 0
        state["wrong_items"] = []
        state["unanswered_items"] = []
        state["last_main_screen"] = "quiz"
        state["screen"] = "quiz"
        render()

    def clear_wrong_note(_=None):
        state["wrong_note_items"] = []
        state["error_message"] = "오답 노트를 비웠습니다."
        render()

    def start_wrong_note_card(_=None):
        if not state["wrong_note_items"]:
            state["error_message"] = "오답 노트가 비어 있습니다."
            render()
            return

        state["items"] = sort_items_for_review(state["wrong_note_items"])
        state["current_index"] = 0
        state["review_wrong_mode"] = True
        state["is_finished"] = False
        reset_quiz_ui_only()
        state["card_finish_message"] = "오답 노트 카드가 끝났습니다.\n다시 볼까요?"
        state["last_main_screen"] = "wrong_note"
        state["screen"] = "card"
        render()

    def start_wrong_note_quiz(_=None):
        if not state["wrong_note_items"]:
            state["error_message"] = "오답 노트가 비어 있습니다."
            render()
            return

        state["items"] = sort_items_for_review(state["wrong_note_items"])
        state["current_index"] = 0
        state["review_wrong_mode"] = True
        state["is_finished"] = False
        reset_quiz_ui_only()
        state["correct_count"] = 0
        state["wrong_count"] = 0
        state["wrong_items"] = []
        state["unanswered_items"] = []
        state["last_main_screen"] = "wrong_note"
        state["screen"] = "quiz"
        render()

    def big_display_text_size(text: str, mode: str) -> int:
        compact = str(text).replace(" ", "").replace("\n", "")
        length = len(compact)

        if mode == "hanja":
            if length <= 1:
                return vw(0.30, 108, 132)
            if length == 2:
                return vw(0.24, 90, 112)
            if length == 3:
                return vw(0.205, 76, 92)
            return vw(0.175, 62, 80)

        if length <= 2:
            return vw(0.19, 64, 82)
        if length <= 4:
            return vw(0.16, 52, 68)
        if length <= 6:
            return vw(0.135, 42, 56)
        return vw(0.115, 34, 48)

    def fixed_problem_box(text: str, mode: str, height: int = 210, y: float = -0.08):
        use_text_size = mode.endswith("_textsize")
        base_mode = mode.replace("_textsize", "")
        text_size_mode = "text" if use_text_size else base_mode

        return ft.Container(
            height=height,
            alignment=ft.Alignment(0, y),
            content=ft.Text(
                text,
                size=big_display_text_size(text, text_size_mode),
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def wrong_note_row(item: Dict[str, str], idx: int) -> ft.Control:
        desc = f"{item.get('뜻', '')} {item.get('독음', '')}".strip()
        return ft.Container(
            width=card_w() - 52,
            bgcolor="#FFFFFF",
            border=ft.border.all(1.2, "#D8D8D8"),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            content=ft.Row(
                [
                    ft.Container(
                        width=28,
                        alignment=ft.Alignment(0, -1),
                        content=ft.Text(str(idx), size=16, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(item.get("한자", ""), size=30, weight=ft.FontWeight.BOLD),
                                    ft.Container(width=8),
                                    ft.Text(desc, size=16, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=0,
                                wrap=True,
                            ),
                            ft.Container(height=3),
                            ft.Text(
                                f'{item.get("급수", "")} / {item.get("단계", "")} / {item.get("타입", "")}',
                                size=13,
                                color=TEXT_GRAY,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

    def render_home():
        return ft.Container(
            width=card_w(),
            height=card_h(),
            bgcolor=CARD_WHITE,
            border_radius=18,
            padding=ft.padding.all(24),
            content=ft.Column(
                [
                    ft.Container(expand=1),
                    ft.Text("한자 공부", size=title_size(), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=18),
                    black_button("입장 하기", lambda e: go("level"), width=144),
                    ft.Container(height=12),
                    black_button("오답 노트", lambda e: open_wrong_note("home"), width=144, disabled=len(state["wrong_note_items"]) == 0),
                    ft.Container(expand=1),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def render_level():
        def make_handler(level: str):
            def handler(_):
                state["selected_level"] = level
                state["selected_ranges"] = []
                render()
            return handler

        rows = []
        idx = 0
        for _ in range(3):
            row_controls = []
            for _ in range(3):
                level = LEVEL_ORDER[idx]
                idx += 1
                row_controls.append(level_button(level, state["selected_level"] == level, make_handler(level)))
            rows.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=18))

        content = ft.Column(
            [
                ft.Container(height=40),
                ft.Text("급수 선택하기", size=title_size(), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=50),
                ft.Column(rows, spacing=18, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=38),
                ft.Row([black_button("다음", lambda e: go("range"), disabled=state["selected_level"] is None, width=132)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=12),
                ft.Row([black_button("오답 노트", lambda e: open_wrong_note("level"), width=132, disabled=len(state["wrong_note_items"]) == 0)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=80),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("급수 선택", content, lambda e: go("home"), 16, 50)

    def render_range():
        level = state["selected_level"] or "?"
        steps = LEVEL_RANGE_MAP.get(level, [])

        def make_step_handler(step_value: str):
            def handler(_):
                norm = normalize_step_value(step_value)
                if norm in state["selected_ranges"]:
                    state["selected_ranges"].remove(norm)
                else:
                    state["selected_ranges"].append(norm)
                render()
            return handler

        panels = []

        if level == "준3급":
            row_controls_all = []
            for step in steps:
                selected = normalize_step_value(step) in state["selected_ranges"]
                row_controls_all.append(range_button(step, selected, make_step_handler(step)))

            rows = []
            for i in range(0, len(row_controls_all), 3):
                rows.append(ft.Row(row_controls_all[i:i + 3], alignment=ft.MainAxisAlignment.CENTER, spacing=22))

            panels.append(
                ft.Container(
                    width=card_w() - 48,
                    border=ft.border.all(1.3, BORDER),
                    border_radius=12,
                    padding=ft.padding.only(left=14, right=14, top=12, bottom=18),
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.EDIT_OUTLINED, size=22, color="black"),
                                    ft.Text("파트 J", size=18, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            ),
                            ft.Container(height=12),
                            *rows,
                        ],
                        spacing=14,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        else:
            groups = group_steps_for_ui(level, steps)
            for part, part_steps in groups.items():
                rows = []
                for i in range(0, len(part_steps), 3):
                    row_controls = []
                    for step in part_steps[i:i + 3]:
                        selected = normalize_step_value(step) in state["selected_ranges"]
                        row_controls.append(range_button(step, selected, make_step_handler(step)))
                    rows.append(ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=18))

                panels.append(
                    ft.Container(
                        width=card_w() - 48,
                        border=ft.border.all(1.2, BORDER),
                        border_radius=12,
                        padding=ft.padding.only(left=12, right=12, top=10, bottom=12),
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=20, color="black"),
                                        ft.Text(f"파트 {part}", size=18, weight=ft.FontWeight.BOLD),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                ft.Container(height=8),
                                *rows,
                            ],
                            spacing=10,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    )
                )

        content = ft.Column(
            [
                split_page_title(level, "범위 지정", badge_left=20, badge_top=15, title_top=14),
                ft.Container(height=-6),
                ft.Column(panels, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=12),
                ft.Row([black_button("시작", lambda e: go("study_type"), disabled=len(state["selected_ranges"]) == 0, width=132)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=72),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("범위 선택", content, lambda e: go("level"), 16, 50)

    def render_study_type():
        level = state["selected_level"] or "?"

        def set_selection(category: str, mode: str):
            def handler(_):
                state["selected_category"] = category
                state["selected_mode"] = mode
                render()
            return handler

        content = ft.Column(
            [
                split_page_title(level, "공부 유형"),
                ft.Container(height=18),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        [
                            type_block(
                                "선정 한자",
                                state["selected_category"] == "선정 한자" and state["selected_mode"] == "카드 외우기",
                                state["selected_category"] == "선정 한자" and state["selected_mode"] == "퀴즈",
                                set_selection("선정 한자", "카드 외우기"),
                                set_selection("선정 한자", "퀴즈"),
                            ),
                            type_block(
                                "교과서 한자",
                                state["selected_category"] == "교과서 한자" and state["selected_mode"] == "카드 외우기",
                                state["selected_category"] == "교과서 한자" and state["selected_mode"] == "퀴즈",
                                set_selection("교과서 한자", "카드 외우기"),
                                set_selection("교과서 한자", "퀴즈"),
                            ),
                        ],
                        spacing=26,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Row([black_button("시작", start_study, disabled=not (state["selected_category"] and state["selected_mode"]), width=132)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Row([black_button("오답 노트", lambda e: open_wrong_note("study_type"), width=132, disabled=len(state["wrong_note_items"]) == 0)], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=64),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("공부 유형", content, lambda e: go("range"), 16, 50)

    def render_wrong_note():
        items = state["wrong_note_items"]

        if not items:
            body = ft.Column(
                [
                    ft.Container(height=40),
                    ft.Text("오답 노트", size=title_size(), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=24),
                    ft.Text("저장된 오답이 없습니다.", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=18),
                    ft.Text("퀴즈에서 틀린 문제가 여기에 쌓입니다.", size=15, color=TEXT_GRAY, text_align=ft.TextAlign.CENTER),
                    ft.Container(expand=True),
                    ft.Row([black_button("홈으로", go_home, width=140)], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=80),
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return page_shell("오답 노트", body, lambda e: go(state["wrong_note_back_screen"]), 16, 50)

        list_view = ft.ListView(
            expand=True,
            spacing=10,
            padding=0,
            controls=[wrong_note_row(item, i + 1) for i, item in enumerate(items)],
        )

        body = ft.Column(
            [
                ft.Container(height=6),
                ft.Text("오답 노트", size=title_size(), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                ft.Text(f"저장된 오답 {len(items)}개", size=17, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
                ft.Container(height=10),
                ft.Container(expand=True, width=card_w() - 34, content=list_view),
                ft.Container(height=10),
                ft.Row(
                    [
                        black_button("카드 보기", start_wrong_note_card, width=126, height=52, font_size=18),
                        ft.Container(width=10),
                        black_button("퀴즈 풀기", start_wrong_note_quiz, width=126, height=52, font_size=18),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=10),
                ft.Row(
                    [
                        black_button("홈으로", go_home, width=126, height=52, font_size=18),
                        ft.Container(width=10),
                        black_button("전체 비우기", clear_wrong_note, width=126, height=52, font_size=18),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=72),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("오답 노트", body, lambda e: go(state["wrong_note_back_screen"]), 16, 50)

    def render_card():
        item = current_item()
        if item is None:
            return page_shell(
                "낱말카드",
                ft.Column(
                    [
                        ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("데이터가 없습니다.", size=18)),
                        ft.Row([black_button("뒤로", lambda e: go(state["last_main_screen"]))], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    expand=True,
                ),
                lambda e: go(state["last_main_screen"]),
                16,
                50,
            )

        level = item.get("급수", state["selected_level"] or "?")
        idx = state["current_index"] + 1
        total = len(state["items"])

        back_text = item["독음"] if item.get("타입", "").startswith("교과서") else f"{item['뜻']} {item['독음']}".strip()

        if state["is_finished"]:
            body = ft.Column(
                [
                    ft.Row(
                        [
                            level_badge(level),
                            ft.Container(expand=True),
                            ft.Text("랜덤", size=16, weight=ft.FontWeight.BOLD),
                            ft.Switch(value=state["random_order"], on_change=toggle_random),
                        ]
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        [
                            ft.Text(f"{idx}", size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(f"/{total}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    ft.Container(expand=True),
                    fixed_problem_box(item["한자"], "hanja", 150, -0.12),
                    ft.Container(height=4),
                    fixed_problem_box(back_text, "text", 150, -0.10),
                    ft.Container(height=7),
                    ft.Text(state["card_finish_message"], size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=12),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text("네", size=30, color=SOFT_BLUE, weight=ft.FontWeight.BOLD),
                                ink=True,
                                on_click=lambda e: (state.update({"current_index": 0, "is_finished": False, "show_card_back": False}), render()),
                            ),
                            ft.Container(width=28),
                            ft.Container(
                                content=ft.Text("홈으로", size=30, color=SOFT_BLUE, weight=ft.FontWeight.BOLD),
                                ink=True,
                                on_click=go_home,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=84),
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return page_shell("낱말카드", body, lambda e: go(state["last_main_screen"]), 16, 50)

        body = ft.Column(
            [
                ft.Row(
                    [
                        level_badge(level),
                        ft.Container(expand=True),
                        ft.Text("랜덤", size=16, weight=ft.FontWeight.BOLD),
                        ft.Switch(value=state["random_order"], on_change=toggle_random),
                    ]
                ),
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.Text(f"{idx}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"/{total}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                ft.Container(height=8),
                fixed_problem_box(item["한자"], "hanja", 200, -0.16),
                ft.Container(
                    height=100,
                    alignment=ft.Alignment(0, -1),
                    content=ft.Text(
                        back_text if state["show_card_back"] else "",
                        size=big_display_text_size(back_text, "text"),
                        color="#1A73E8",
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                ft.Container(height=30),
                ft.Row(
                    [
                        arrow_button(ft.Icons.ARROW_BACK, on_click=prev_item, disabled=state["current_index"] == 0),
                        center_circle_button("?", on_click=lambda e: (state.update({"show_card_back": not state["show_card_back"]}), render())),
                        arrow_button(ft.Icons.ARROW_FORWARD, on_click=next_item),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=18,
                ),
                ft.Container(height=58),
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("낱말카드", body, lambda e: go(state["last_main_screen"]), 16, 50)

    def render_quiz():
        item = current_item()
        if item is None:
            return page_shell(
                "퀴즈",
                ft.Column(
                    [
                        ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=ft.Text("데이터가 없습니다.", size=18)),
                        ft.Row([black_button("뒤로", lambda e: go(state["last_main_screen"]))], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    expand=True,
                ),
                lambda e: go(state["last_main_screen"]),
                16,
                58,
            )

        level = item.get("급수", state["selected_level"] or "?")
        idx = state["current_index"] + 1
        total = len(state["items"])

        if state["quiz_direction"] == "한자→뜻":
            question_text = item["한자"]
            question_mode = "hanja"
            answer_text = f"{item['뜻']} {item['독음']}".strip() if ("선정" in item.get("타입", "")) else item["독음"]
        else:
            question_text = f"{item['뜻']} {item['독음']}".strip() if ("선정" in item.get("타입", "")) else item["독음"]
            question_mode = "text"
            answer_text = item["한자"]

        refresh_quiz_choices()
        choices = state["quiz_choices"]

        def choose(index: int):
            def handler(_):
                if not state["quiz_checked"]:
                    state["quiz_selected_index"] = index
                    render()
            return handler

        def check_answer(_):
            if state["quiz_selected_index"] is None or state["quiz_checked"]:
                return

            if not choices:
                state["error_message"] = "보기 생성에 실패했습니다."
                render()
                return

            state["quiz_checked"] = True

            if choices[state["quiz_selected_index"]] == answer_text:
                state["correct_count"] += 1
                state["quiz_result_message"] = "정답입니다."
            else:
                state["wrong_count"] += 1
                state["quiz_result_message"] = f'틀렸습니다.\n정답은 "{answer_text}"'
                append_unique_item(state["wrong_items"], item)
                append_unique_item(state["wrong_note_items"], item)

            render()

        option_controls = []
        option_width = card_w() - 36

        for i, choice in enumerate(choices):
            selected = state["quiz_selected_index"] == i
            bg = "#EFEFEF"
            border_color = "#999999"

            if selected and not state["quiz_checked"]:
                bg = "#DDE8FB"
                border_color = "#2C77E6"

            if state["quiz_checked"]:
                if choice == answer_text:
                    bg = "#DCEAD8"
                    border_color = "#43A047"

            option_controls.append(
                ft.Container(
                    width=option_width,
                    height=54 if is_mobile_narrow() else 46,
                    border_radius=5,
                    bgcolor=bg,
                    border=ft.border.all(1, border_color),
                    alignment=ft.Alignment(0, 0),
                    ink=True,
                    on_click=choose(i),
                    content=ft.Stack(
                        controls=[
                            ft.Container(
                                left=14,
                                top=0,
                                bottom=0,
                                width=34,
                                alignment=ft.Alignment(-1, 0),
                                content=ft.Text(f"{i+1}.", size=17, weight=ft.FontWeight.BOLD),
                            ),
                            ft.Container(
                                left=0,
                                right=0,
                                top=0,
                                bottom=0,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text(
                                    choice,
                                    size=22 if is_mobile_narrow() else 26,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ),
                        ]
                    ),
                )
            )

        if state["is_finished"]:
            body = ft.Column(
                [
                    ft.Container(height=30),
                    ft.Text("끝났습니다.", size=28, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Text(
                        f'정답 {state["correct_count"]} / 오답 {state["wrong_count"]} / 미응답 {len(state["unanswered_items"])}',
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=26),
                    ft.Text("어떻게 할까요?", size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=22),
                    ft.Row(
                        [
                            black_button("전체 다시", restart_study, width=126, height=52, font_size=18),
                            ft.Container(width=10),
                            black_button(
                                "오답+미응답\n다시",
                                start_retry_incomplete_quiz,
                                width=126,
                                height=58,
                                font_size=16,
                                disabled=(len(state["wrong_items"]) + len(state["unanswered_items"]) == 0),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        [
                            black_button("홈으로", go_home, width=126, height=52, font_size=18),
                            ft.Container(width=10),
                            black_button("나가기", exit_study, width=126, height=52, font_size=18),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    ft.Container(height=78),
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            return page_shell("퀴즈", body, lambda e: go(state["last_main_screen"]), 16, 58)

        body = ft.Column(
            [
                ft.Row(
                    [
                        level_badge(level),
                        ft.Container(expand=True),
                        ft.Text("랜덤", size=16, weight=ft.FontWeight.BOLD),
                        ft.Switch(value=state["random_order"], on_change=toggle_random),
                    ]
                ),
                ft.Container(height=-2),
                ft.Row(
                    [
                        ft.Text(f"{idx}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"/{total}", size=18, weight=ft.FontWeight.BOLD, color=TEXT_GRAY),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                ft.Container(height=-8),
                ft.Row(
                    [
                        ft.Text("✅", size=15),
                        ft.Text(str(state["correct_count"]), size=17),
                        ft.Text("❌", size=15),
                        ft.Text(str(state["wrong_count"]), size=17),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
                fixed_problem_box(question_text, "hanja_textsize" if question_mode == "hanja" else "text", 110, -0.90),
                ft.Container(
                    height=54,
                    alignment=ft.Alignment(0, -0.65),
                    content=ft.Text(
                        state["quiz_result_message"],
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color="#C62828" if state["quiz_result_message"].startswith("틀렸습니다") else "#2E7D32",
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                ft.Column([ft.Row([opt], alignment=ft.MainAxisAlignment.CENTER) for opt in option_controls], spacing=6),
                ft.Container(height=20),
                ft.Row(
                    [
                        arrow_button(ft.Icons.ARROW_BACK, on_click=prev_item, disabled=state["current_index"] == 0),
                        center_circle_button("정답", on_click=check_answer),
                        arrow_button(ft.Icons.ARROW_FORWARD, on_click=next_item),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
                ft.Container(height=20),
                ft.Container(
                    width=card_w() - 120,
                    bgcolor="#EDEDED",
                    border_radius=18,
                    padding=ft.padding.symmetric(horizontal=14, vertical=7),
                    content=ft.Row(
                        [
                            ft.Container(
                                bgcolor="white" if state["quiz_direction"] == "한자→뜻" else None,
                                border_radius=14,
                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                content=ft.Text("한자 > 뜻", size=14, weight=ft.FontWeight.W_500),
                            ),
                            ft.Container(
                                bgcolor="white" if state["quiz_direction"] == "뜻→한자" else None,
                                border_radius=14,
                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                content=ft.Text("뜻 > 한자", size=14, weight=ft.FontWeight.W_500),
                            ),
                        ],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ink=True,
                    on_click=toggle_quiz_direction,
                ),
                ft.Container(height=42),
            ],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return page_shell("퀴즈", body, lambda e: go(state["last_main_screen"]), 16, 58)

    def render():
        page.clean()

        if state["error_message"]:
            page.snack_bar = ft.SnackBar(content=ft.Text(state["error_message"]))
            page.snack_bar.open = True
            state["error_message"] = ""

        if state["screen"] == "home":
            root = render_home()
        elif state["screen"] == "level":
            root = render_level()
        elif state["screen"] == "range":
            root = render_range()
        elif state["screen"] == "study_type":
            root = render_study_type()
        elif state["screen"] == "card":
            root = render_card()
        elif state["screen"] == "quiz":
            root = render_quiz()
        elif state["screen"] == "wrong_note":
            root = render_wrong_note()
        else:
            root = render_home()

        page.add(ft.Container(padding=ft.padding.symmetric(horizontal=6, vertical=8), content=root))
        page.update()

    def on_resize(_):
        render()

    page.on_resize = on_resize
    render()


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets"
    )