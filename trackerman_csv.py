import json
import csv
from pathlib import Path


# ============================================================
# 設定
# ============================================================

INPUT_FILE = Path("data/raw/games/2026-A-280.json")

OUTPUT_FILE = Path(
    "data/processed/trackman_2026-A-280.csv"
)


# ============================================================
# 取得安全的巢狀資料
# ============================================================

def get_value(data, *keys):

    current = data

    for key in keys:

        if not isinstance(current, dict):
            return None

        current = current.get(key)

        if current is None:
            return None

    return current


# ============================================================
# 轉換單場比賽
# ============================================================

def convert_game(data):

    game = data["Data"]["Game"]

    game_id = game.get("GameId")

    visiting = game.get("Visiting", {})
    home = game.get("Home", {})

    visiting_team = get_value(
        visiting,
        "Team",
        "Name"
    )

    home_team = get_value(
        home,
        "Team",
        "Name"
    )

    rows = []

    live_logs = game.get(
        "LiveLog",
        []
    )

    for log in live_logs:

        if not isinstance(log, dict):
            continue

        trackman = log.get("Trackman")

        # 沒有 Trackman 就跳過
        if not trackman:
            continue

        # ----------------------------------------------------
        # Trackman / Play
        # ----------------------------------------------------

        pitch_tag = get_value(
            trackman,
            "Play",
            "PitchTag"
        ) or {}

        pitch_call = pitch_tag.get(
            "PitchCall"
        )

        auto_pitch_type = pitch_tag.get(
            "AutoPitchType"
        )

        tagged_pitch_type = pitch_tag.get(
            "TaggedPitchType"
        )

        # ----------------------------------------------------
        # Trackman / Pitch / Release
        # ----------------------------------------------------

        release = get_value(
            trackman,
            "Pitch",
            "Release"
        ) or {}

        # ----------------------------------------------------
        # Trackman / Pitch / Location
        # ----------------------------------------------------

        location = get_value(
            trackman,
            "Pitch",
            "Location"
        ) or {}

        # ----------------------------------------------------
        # Trackman / Hit
        # ----------------------------------------------------

        hit = trackman.get("Hit") or {}

        launch = hit.get(
            "Launch"
        ) or {}

        landing = hit.get(
            "LandingFlat"
        ) or {}

        # ----------------------------------------------------
        # 建立一球資料
        # ----------------------------------------------------

        row = {

            # ==============================
            # 比賽資訊
            # ==============================

            "GameId": game_id,

            "GameSno": game.get(
                "GameSno"
            ),

            "GameDate": game.get(
                "PreExeDate"
            ),

            "VisitingTeam": visiting_team,

            "HomeTeam": home_team,

            "Field": get_value(
                game,
                "Field",
                "Abbe"
            ),

            # ==============================
            # 投球基本資訊
            # ==============================

            "Year": log.get(
                "Year"
            ),

            "Inning": log.get(
                "InningSeq"
            ),

            "PitchCnt": log.get(
                "PitchCnt"
            ),

            "OutCnt": log.get(
                "OutCnt"
            ),

            "BallCnt": log.get(
                "BallCnt"
            ),

            "StrikeCnt": log.get(
                "StrikeCnt"
            ),

            "IsBall": log.get(
                "IsBall"
            ),

            "IsStrike": log.get(
                "IsStrike"
            ),

            # ==============================
            # 球員
            # ==============================

            "PitcherAcnt": log.get(
                "PitcherAcnt"
            ),

            "PitcherName": log.get(
                "PitcherName"
            ),

            "HitterAcnt": log.get(
                "HitterAcnt"
            ),

            "HitterName": log.get(
                "HitterName"
            ),

            "CatcherAcnt": log.get(
                "CatcherAcnt"
            ),

            "CatcherName": log.get(
                "CatcherName"
            ),

            "PitcherUniformNo": log.get(
                "PitcherUniformNo"
            ),

            "HitterUniformNo": log.get(
                "HitterUniformNo"
            ),

            # ==============================
            # 比賽結果
            # ==============================

            "Content": log.get(
                "Content"
            ),

            "ActionName": log.get(
                "ActionName"
            ),

            "BattingActionName": log.get(
                "BattingActionName"
            ),

            "MainEventNo": log.get(
                "MainEventNo"
            ),

            # ==============================
            # Trackman PitchTag
            # ==============================

            "PitchCall": pitch_call,

            "AutoPitchType": auto_pitch_type,

            "TaggedPitchType": tagged_pitch_type,

            # ==============================
            # Release
            # ==============================

            "RelSide": release.get(
                "RelSide"
            ),

            "RelSpeed": release.get(
                "RelSpeed"
            ),

            "SpinRate": release.get(
                "SpinRate"
            ),

            "Extension": release.get(
                "Extension"
            ),

            "RelHeight": release.get(
                "RelHeight"
            ),

            # ==============================
            # Location
            # ==============================

            "ZoneTime": location.get(
                "ZoneTime"
            ),

            "ZoneSpeed": location.get(
                "ZoneSpeed"
            ),

            "PlateLocSide": location.get(
                "PlateLocSide"
            ),

            "PlateLocHeight": location.get(
                "PlateLocHeight"
            ),

            # ==============================
            # Hit / Launch
            # ==============================

            "ExitSpeed": launch.get(
                "ExitSpeed"
            ),

            "LaunchAngle": launch.get(
                "Angle"
            ),

            "HitDirection": launch.get(
                "Direction"
            ),

            "HitSpinRate": launch.get(
                "HitSpinRate"
            ),

            # ==============================
            # Hit / Landing
            # ==============================

            "LandingBearing": landing.get(
                "Bearing"
            ),

            "LandingDistance": landing.get(
                "Distance"
            ),

            "HangTime": landing.get(
                "HangTime"
            ),

            "LandingConfidence": landing.get(
                "Confidence"
            ),
        }

        rows.append(row)

    return rows


# ============================================================
# 寫入 CSV
# ============================================================

def save_csv(rows):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not rows:

        print("❌ 沒有找到 Trackman 資料")
        return

    fieldnames = list(
        rows[0].keys()
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)

    print()
    print("=" * 60)
    print("CSV 轉換完成")
    print("=" * 60)

    print()
    print("資料筆數:", len(rows))

    print()
    print("輸出檔案:")
    print(
        OUTPUT_FILE.resolve()
    )


# ============================================================
# 主程式
# ============================================================

def main():

    print("=" * 60)
    print("CPBL Trackman JSON → CSV")
    print("=" * 60)

    print()
    print("讀取:")
    print(
        INPUT_FILE.resolve()
    )

    if not INPUT_FILE.exists():

        print()
        print("❌ 找不到 JSON 檔案")

        return

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    rows = convert_game(
        data
    )

    save_csv(
        rows
    )


if __name__ == "__main__":
    main()
