import os
import sqlite3
import argparse
from datetime import datetime

def sanitize_filename(name, max_length=100):
    """ファイル名に使用できない文字を置換し、長すぎる場合は短縮"""
    if not name:
        return "Unknown_Chat"

    # 不正な文字を置換（Windowsに使えない文字: \ / : * ? " < > |）
    sanitized = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

    # ✅ 末尾の `.` や ` ` は `_` に変換（削除ではなく置換）
    while sanitized.endswith(".") or sanitized.endswith(" "):
        sanitized = sanitized[:-1] + "_"

    # 長すぎる場合は短縮
    return sanitized[:max_length]


def extract_skype_logs(db_file, output_folder, max_file_size_kb=1000):
    """SkypeのSQLiteログを会話ごとに分割して出力 (FESS向け)"""
    os.makedirs(output_folder, exist_ok=True)

    # データベース接続
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # すべての会話を取得
    cursor.execute("SELECT DISTINCT convo_id FROM Messages;")
    conversations = cursor.fetchall()

    for conv in conversations:
        convo_id = conv[0]

        # 会話名を取得
        cursor.execute("SELECT displayname FROM Conversations WHERE id = ?", (convo_id,))
        result = cursor.fetchone()
        conv_name = result[0] if result else convo_id  # 取得できなければ convo_id を使用

        safe_name = sanitize_filename(conv_name)
        conv_folder = os.path.join(output_folder, safe_name)
        os.makedirs(conv_folder, exist_ok=True)  

        # メッセージを取得（時系列順）
        cursor.execute("""
            SELECT timestamp, author, body_xml FROM Messages 
            WHERE convo_id = ? ORDER BY timestamp ASC;
        """, (convo_id,))
        messages = cursor.fetchall()

        file_content = []
        current_year, current_month = None, None
        current_file_size = 0
        file_index = 1  # 1ヶ月内で複数ファイルに分割するためのインデックス

        def save_current_log():
            """現在のメッセージリストをファイルに書き出す"""
            nonlocal file_content, current_year, current_month, file_index, current_file_size

            if not file_content or current_year is None or current_month is None:
                return  

            os.makedirs(conv_folder, exist_ok=True)  

            file_suffix = f"_{file_index}" if file_index > 1 else ""
            output_file = os.path.join(conv_folder, f"{current_year}_{current_month:02d}{file_suffix}.txt")

            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.writelines(file_content)

            print(f"✅ {output_file} を作成しました。")
            file_content = []
            file_index += 1
            current_file_size = 0

        for msg in messages:
            timestamp, sender, text = msg
            text = text.replace("\n", " ") if text else "(No message)"

            try:
                msg_date = datetime.utcfromtimestamp(timestamp)
                year, month = msg_date.year, msg_date.month
                timestamp_str = msg_date.strftime("%Y-%m-%d %H:%M:%S")
            except:
                year, month, timestamp_str = 9999, 99, "Unknown Time"

            if current_year is None or current_month is None:
                current_year, current_month = year, month

            message_line = f"[{timestamp_str}] {sender}: {text}\n"
            message_size = len(message_line.encode('utf-8')) / 1024  # KB単位

            # 月が変わったら保存
            if (current_year, current_month) != (year, month):
                save_current_log()
                current_year, current_month = year, month
                file_index = 1  # 月ごとにリセット

            # ファイルサイズが上限を超えたら保存
            if current_file_size + message_size > max_file_size_kb:
                save_current_log()

            file_content.append(message_line)
            current_file_size += message_size

        # 最後のファイルを保存
        save_current_log()

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Skype SQLite logs into FESS-friendly text files.")
    parser.add_argument("db", help="Input Skype SQLite database file (main.db)")
    parser.add_argument("output_folder", help="Output folder for conversation text files")
    parser.add_argument("--max_size", type=int, default=1000, help="Max file size in KB (default: 1000KB)")

    args = parser.parse_args()
    extract_skype_logs(args.db, args.output_folder, args.max_size)

# 使用例:
# python skype_db_converter.py main.db output_folder --max_size 1000