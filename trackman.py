import json
from pathlib import Path

import requests


# ============================================================
# 設定
# ============================================================

# 要抓哪一天
TARGET_DATE = "2026-09-14"

# CPBL API
BASE_URL = "https://stats.cpbl.com.tw/api/proxy/v1"

# 原始資料儲存位置
OUTPUT_DIR = Path("data/raw/games")


# ============================================================
# HTTP Headers
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://stats.cpbl.com.tw/",
}


# ============================================================
# 建立 Session
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# 取得指定日期的賽程
# ============================================================

def fetch_schedule(date):

    url = f"{BASE_URL}/games/schedule/{date}"

    print("=" * 60)
    print("取得當日賽程")
    print("=" * 60)

    print("日期:", date)
    print("URL:", url)

    try:
        response = session.get(
            url,
            timeout=30,
        )

    except requests.RequestException as e:

        print()
        print("❌ 賽程 API 請求失敗")
        print(e)

        return None

    print()
    print("Status:", response.status_code)
    print(
        "Content-Type:",
        response.headers.get("Content-Type")
    )

    if response.status_code != 200:

        print()
        print("❌ 賽程 API 回傳錯誤")
        print(response.text[:2000])

        return None

    try:
        data = response.json()

    except ValueError:

        print()
        print("❌ 賽程 API 回傳不是 JSON")
        print(response.text[:2000])

        return None

    print()
    print("✅ 成功取得賽程")

    return data


# ============================================================
# 從賽程 JSON 找出比賽
# ============================================================

def extract_games(data):

    print()
    print("=" * 60)
    print("分析賽程資料")
    print("=" * 60)

    games = []

    # --------------------------------------------------------
    # 情況 1：
    #
    # API 可能直接回傳 list
    # --------------------------------------------------------

    if isinstance(data, list):

        games = data

    # --------------------------------------------------------
    # 情況 2：
    #
    # API 回傳 dict
    # --------------------------------------------------------

    elif isinstance(data, dict):

        # 常見欄位
        possible_keys = [
            "Data",
            "Games",
            "Game",
            "Schedule",
            "data",
            "games",
        ]

        for key in possible_keys:

            value = data.get(key)

            if isinstance(value, list):

                games = value
                break

            if isinstance(value, dict):

                # 如果裡面還有 Games
                for sub_key in [
                    "Games",
                    "Game",
                    "Schedule",
                    "games",
                ]:

                    sub_value = value.get(
                        sub_key
                    )

                    if isinstance(
                        sub_value,
                        list,
                    ):

                        games = sub_value
                        break

                if games:
                    break

    # --------------------------------------------------------
    # 如果還是找不到
    # --------------------------------------------------------

    if not games:

        print()
        print("⚠️ 找不到賽程列表")

        print()
        print("API 最外層結構:")

        if isinstance(data, dict):
            print(
                list(data.keys())
            )
        else:
            print(
                type(data).__name__
            )

        return []

    print()
    print(
        "找到比賽數:",
        len(games)
    )

    return games


# ============================================================
# 從單場賽程資料取得 Game ID
# ============================================================

def get_game_id(game):

    if not isinstance(game, dict):
        return None

    possible_keys = [
        "GameId",
        "GameID",
        "gameId",
        "gameID",
        "Id",
        "ID",
        "id",
    ]

    for key in possible_keys:

        value = game.get(key)

        if value:

            return str(value)

    return None


# ============================================================
# 顯示賽程
# ============================================================

def show_schedule(games):

    print()
    print("=" * 60)
    print("當日比賽")
    print("=" * 60)

    valid_games = []

    for index, game in enumerate(games):

        game_id = get_game_id(game)

        if not game_id:
            continue

        valid_games.append(
            (
                game_id,
                game,
            )
        )

        print()
        print(
            f"[{len(valid_games)}] "
            f"Game ID: {game_id}"
        )

        # 把可能有的隊伍名稱印出來
        visiting = game.get(
            "Visiting",
            {}
        )

        home = game.get(
            "Home",
            {}
        )

        if isinstance(
            visiting,
            dict,
        ):

            visiting_team = visiting.get(
                "Team",
                {}
            )

            if isinstance(
                visiting_team,
                dict,
            ):

                print(
                    "客隊:",
                    visiting_team.get(
                        "Name"
                    )
                )

        if isinstance(
            home,
            dict,
        ):

            home_team = home.get(
                "Team",
                {}
            )

            if isinstance(
                home_team,
                dict,
            ):

                print(
                    "主隊:",
                    home_team.get(
                        "Name"
                    )
                )

    print()
    print(
        "可用 Game ID:",
        len(valid_games)
    )

    return valid_games


# ============================================================
# 取得單場比賽
# ============================================================

def fetch_game(game_id):

    url = (
        f"{BASE_URL}/games/{game_id}"
    )

    print()
    print("=" * 60)
    print(
        f"取得比賽: {game_id}"
    )
    print("=" * 60)

    print("URL:", url)

    try:

        response = session.get(
            url,
            timeout=30,
        )

    except requests.RequestException as e:

        print()
        print("❌ HTTP 請求失敗")
        print(e)

        return None

    print()
    print(
        "Status:",
        response.status_code
    )

    if response.status_code != 200:

        print()
        print("❌ API 錯誤")
        print(
            response.text[:1000]
        )

        return None

    try:

        data = response.json()

    except ValueError:

        print()
        print("❌ 回傳不是 JSON")

        return None

    print(
        "✅ 成功取得比賽 JSON"
    )

    return data


# ============================================================
# 儲存比賽 JSON
# ============================================================

def save_game_json(data, game_id):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / f"{game_id}.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(
        "✅ 已儲存:"
    )

    print(
        output_file.resolve()
    )


# ============================================================
# 分析比賽
# ============================================================

def analyze_game(data, game_id):

    print()
    print("=" * 60)
    print(
        f"分析比賽: {game_id}"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # 找 Game
    # --------------------------------------------------------

    if not isinstance(
        data,
        dict,
    ):

        print(
            "❌ JSON 不是 dict"
        )

        return

    if "Data" not in data:

        print(
            "❌ 找不到 Data"
        )

        return

    data_section = data["Data"]

    if not isinstance(
        data_section,
        dict,
    ):

        print(
            "❌ Data 不是 dict"
        )

        return

    if "Game" not in data_section:

        print(
            "❌ 找不到 Game"
        )

        return

    game = data_section["Game"]

    if not isinstance(
        game,
        dict,
    ):

        print(
            "❌ Game 不是 dict"
        )

        return

    # --------------------------------------------------------
    # 基本資料
    # --------------------------------------------------------

    print()
    print("GameId:", game.get("GameId"))
    print(
        "GameStatus:",
        game.get("GameStatus")
    )
    print(
        "SkipTrackman:",
        game.get("SkipTrackman")
    )
    print(
        "KindCode:",
        game.get("KindCode")
    )
    print(
        "GameSno:",
        game.get("GameSno")
    )
    print(
        "InningSeq:",
        game.get("InningSeq")
    )

    # --------------------------------------------------------
    # 球隊
    # --------------------------------------------------------

    visiting = game.get(
        "Visiting",
        {}
    )

    home = game.get(
        "Home",
        {}
    )

    print()

    if isinstance(
        visiting,
        dict,
    ):

        visiting_team = visiting.get(
            "Team",
            {}
        )

        if isinstance(
            visiting_team,
            dict,
        ):

            print(
                "客隊:",
                visiting_team.get(
                    "Name"
                )
            )

        print(
            "客隊分數:",
            visiting.get("Score")
        )

    if isinstance(
        home,
        dict,
    ):

        home_team = home.get(
            "Team",
            {}
        )

        if isinstance(
            home_team,
            dict,
        ):

            print(
                "主隊:",
                home_team.get(
                    "Name"
                )
            )

        print(
            "主隊分數:",
            home.get("Score")
        )

    # --------------------------------------------------------
    # LiveLog
    # --------------------------------------------------------

    live_logs = game.get(
        "LiveLog",
        []
    )

    print()
    print(
        "LiveLog 筆數:",
        len(live_logs)
    )

    # --------------------------------------------------------
    # Trackman
    # --------------------------------------------------------

    trackman_count = 0
    trackman_non_null = 0

    for log in live_logs:

        if not isinstance(
            log,
            dict,
        ):
            continue

        if "Trackman" not in log:
            continue

        trackman_count += 1

        if log.get(
            "Trackman"
        ) is not None:

            trackman_non_null += 1

    print()
    print(
        "Trackman 欄位數:",
        trackman_count
    )

    print(
        "Trackman 非 None:",
        trackman_non_null
    )

    if trackman_non_null > 0:

        print()
        print(
            "🎯 找到 Trackman 資料！"
        )

        for index, log in enumerate(
            live_logs
        ):

            if not isinstance(
                log,
                dict,
            ):
                continue

            trackman = log.get(
                "Trackman"
            )

            if trackman is None:
                continue

            print()
            print(
                f"LiveLog[{index}]"
            )

            print(
                json.dumps(
                    trackman,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )

            # 只顯示第一筆
            break

    else:

        print()
        print(
            "⚠️ 這場 /games/{gameId} "
            "回傳的 Trackman 仍然是 None"
        )

    # --------------------------------------------------------
    # 找可能的 Pitch / Trackman 欄位
    # --------------------------------------------------------

    print()
    print(
        "正在搜尋其他投球資料欄位..."
    )

    keywords = [
        "pitchspeed",
        "pitchtype",
        "spinrate",
        "spinaxis",
        "velocity",
        "release",
        "platex",
        "platez",
        "trackman",
    ]

    found = []

    def recursive_search(
        obj,
        path="root",
    ):

        if isinstance(
            obj,
            dict,
        ):

            for key, value in obj.items():

                current_path = (
                    f"{path}.{key}"
                )

                key_lower = str(
                    key
                ).lower()

                if any(
                    keyword in key_lower
                    for keyword in keywords
                ):

                    if value is not None:

                        found.append(
                            (
                                current_path,
                                type(value).__name__,
                                value,
                            )
                        )

                recursive_search(
                    value,
                    current_path,
                )

        elif isinstance(
            obj,
            list,
        ):

            for index, value in enumerate(
                obj
            ):

                recursive_search(
                    value,
                    f"{path}[{index}]",
                )

    recursive_search(
        game,
        "Game",
    )

    # --------------------------------------------------------
    # 去除重複
    # --------------------------------------------------------

    unique = []

    seen = set()

    for path, value_type, value in found:

        if path in seen:
            continue

        seen.add(path)

        unique.append(
            (
                path,
                value_type,
                value,
            )
        )

    print()
    print(
        "找到相關欄位:",
        len(unique)
    )

    # --------------------------------------------------------
    # 只顯示真正有價值的欄位
    # --------------------------------------------------------

    for path, value_type, value in unique[:50]:

        print()
        print(
            "Path:",
            path
        )

        print(
            "Type:",
            value_type
        )

        if isinstance(
            value,
            (dict, list),
        ):

            text = json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            if len(text) > 1000:

                text = (
                    text[:1000]
                    + "\n..."
                )

            print(
                "Value:"
            )

            print(text)

        else:

            print(
                "Value:",
                repr(value)
            )


# ============================================================
# 主程式
# ============================================================

def main():

    print()
    print("=" * 60)
    print("CPBL 2026/09/14 Trackman 測試")
    print("=" * 60)

    print()
    print(
        "目標日期:",
        TARGET_DATE
    )

    # ========================================================
    # 1. 取得當天賽程
    # ========================================================

    schedule_data = fetch_schedule(
        TARGET_DATE
    )

    if schedule_data is None:
        return

    # ========================================================
    # 2. 找比賽
    # ========================================================

    games = extract_games(
        schedule_data
    )

    if not games:

        print()
        print(
            "❌ 這一天沒有找到比賽"
        )

        return

    # ========================================================
    # 3. 顯示比賽
    # ========================================================

    valid_games = show_schedule(
        games
    )

    if not valid_games:

        print()
        print(
            "❌ 沒有找到有效 Game ID"
        )

        return

    # ========================================================
    # 4. 一場一場抓
    # ========================================================

    success_count = 0

    for game_id, schedule_game in valid_games:

        print()
        print()
        print("#" * 60)
        print(
            f"開始處理 {game_id}"
        )
        print("#" * 60)

        data = fetch_game(
            game_id
        )

        if data is None:

            print(
                f"❌ {game_id} 取得失敗"
            )

            continue

        # ----------------------------------------------------
        # 儲存
        # ----------------------------------------------------

        save_game_json(
            data,
            game_id
        )

        # ----------------------------------------------------
        # 分析
        # ----------------------------------------------------

        analyze_game(
            data,
            game_id
        )

        success_count += 1

    # ========================================================
    # 完成
    # ========================================================

    print()
    print()
    print("=" * 60)
    print("全部完成")
    print("=" * 60)

    print()
    print(
        "成功取得:",
        success_count,
        "/",
        len(valid_games),
        "場"
    )

    print()
    print(
        "JSON 儲存位置:"
    )

    print(
        OUTPUT_DIR.resolve()
    )


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":
    main()