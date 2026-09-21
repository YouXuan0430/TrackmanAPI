import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

import requests


# ============================================================
# 設定
# ============================================================

# CPBL API
BASE_URL = "https://stats.cpbl.com.tw/api/proxy/v1"

# 原始資料儲存位置
OUTPUT_DIR = Path("data/raw/games")
CSV_OUTPUT = Path("data/processed/trackman.csv")


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
# JSON -> CSV
# ============================================================

def get_value(data, *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def convert_game(data):
    game = get_value(data, "Data", "Game") or {}
    visiting = game.get("Visiting") or {}
    home = game.get("Home") or {}
    rows = []

    for log in game.get("LiveLog") or []:
        if not isinstance(log, dict) or not log.get("Trackman"):
            continue

        trackman = log["Trackman"]
        pitch_tag = get_value(trackman, "Play", "PitchTag") or {}
        release = get_value(trackman, "Pitch", "Release") or {}
        location = get_value(trackman, "Pitch", "Location") or {}
        launch = get_value(trackman, "Hit", "Launch") or {}
        landing = get_value(trackman, "Hit", "LandingFlat") or {}

        rows.append({
            "GameId": game.get("GameId"),
            "GameSno": game.get("GameSno"),
            "GameDate": game.get("PreExeDate"),
            "VisitingTeam": get_value(visiting, "Team", "Name"),
            "HomeTeam": get_value(home, "Team", "Name"),
            "Field": get_value(game, "Field", "Abbe"),
            "Year": log.get("Year"),
            "Inning": log.get("InningSeq"),
            "PitchCnt": log.get("PitchCnt"),
            "OutCnt": log.get("OutCnt"),
            "BallCnt": log.get("BallCnt"),
            "StrikeCnt": log.get("StrikeCnt"),
            "IsBall": log.get("IsBall"),
            "IsStrike": log.get("IsStrike"),
            "PitcherAcnt": log.get("PitcherAcnt"),
            "PitcherName": log.get("PitcherName"),
            "HitterAcnt": log.get("HitterAcnt"),
            "HitterName": log.get("HitterName"),
            "CatcherAcnt": log.get("CatcherAcnt"),
            "CatcherName": log.get("CatcherName"),
            "PitcherUniformNo": log.get("PitcherUniformNo"),
            "HitterUniformNo": log.get("HitterUniformNo"),
            "Content": log.get("Content"),
            "ActionName": log.get("ActionName"),
            "BattingActionName": log.get("BattingActionName"),
            "MainEventNo": log.get("MainEventNo"),
            "PitchCall": pitch_tag.get("PitchCall"),
            "AutoPitchType": pitch_tag.get("AutoPitchType"),
            "TaggedPitchType": pitch_tag.get("TaggedPitchType"),
            "RelSide": release.get("RelSide"),
            "RelSpeed": release.get("RelSpeed"),
            "SpinRate": release.get("SpinRate"),
            "Extension": release.get("Extension"),
            "RelHeight": release.get("RelHeight"),
            "ZoneTime": location.get("ZoneTime"),
            "ZoneSpeed": location.get("ZoneSpeed"),
            "PlateLocSide": location.get("PlateLocSide"),
            "PlateLocHeight": location.get("PlateLocHeight"),
            "ExitSpeed": launch.get("ExitSpeed"),
            "LaunchAngle": launch.get("Angle"),
            "HitDirection": launch.get("Direction"),
            "HitSpinRate": launch.get("HitSpinRate"),
            "LandingBearing": landing.get("Bearing"),
            "LandingDistance": landing.get("Distance"),
            "HangTime": landing.get("HangTime"),
            "LandingConfidence": landing.get("Confidence"),
        })
    return rows


def save_csv(rows, output_file):
    if not rows:
        print("沒有找到 Trackman 資料，略過 CSV 輸出")
        return
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV 完成: {output_file.resolve()} ({len(rows)} 筆)")


def parse_dates(args):
    if args.dates:
        dates = args.dates
    elif args.start_date and args.end_date:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
        if start > end:
            raise ValueError("start-date 不可晚於 end-date")
        dates = [
            (start + timedelta(days=offset)).isoformat()
            for offset in range((end - start).days + 1)
        ]
    else:
        raise ValueError("請使用 --dates，或同時使用 --start-date 和 --end-date")
    return list(dict.fromkeys(dates))


# ============================================================
# 主程式
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="取得 CPBL Trackman 資料並合併輸出 CSV"
    )
    parser.add_argument(
        "--dates", nargs="+", help="要抓取的日期，例如 2026-09-14 2026-09-15"
    )
    parser.add_argument("--start-date", help="連續日期的起始日，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", help="連續日期的結束日，格式 YYYY-MM-DD")
    parser.add_argument(
        "--output", type=Path, default=CSV_OUTPUT, help="CSV 輸出路徑"
    )
    args = parser.parse_args()

    try:
        dates = parse_dates(args)
    except ValueError as error:
        parser.error(str(error))

    all_rows = []
    downloaded = 0
    total_games = 0

    for target_date in dates:
        print(f"\n{'=' * 60}\n處理日期: {target_date}\n{'=' * 60}")
        schedule_data = fetch_schedule(target_date)
        if schedule_data is None:
            continue

        valid_games = show_schedule(extract_games(schedule_data))
        total_games += len(valid_games)
        for game_id, _ in valid_games:
            data = fetch_game(game_id)
            if data is None:
                continue
            save_game_json(data, game_id)
            all_rows.extend(convert_game(data))
            downloaded += 1

    save_csv(all_rows, args.output)
    print(f"完成：日期 {len(dates)} 天，成功取得 {downloaded}/{total_games} 場")


# ============================================================
# 程式入口
# ============================================================

if __name__ == "__main__":
    main()