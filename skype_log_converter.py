import json
import os
import argparse
from datetime import datetime

def sanitize_filename(name):
    """ファイル名に使用できない文字を置換"""
    if not name:  # Noneや空文字チェック
        return ""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

def convert_skype_log(input_file, output_folder, max_file_size_kb=1000):
    """SkypeのJSONログを会話ごとに分割して出力 (FESS向け)"""
    os.makedirs(output_folder, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conversations = data.get("conversations", [])
    
    for i, conv in enumerate(conversations):
        messages = conv.get("MessageList", [])
        if not messages:
            continue  # 空の会話はスキップ

        # `displayName` が `None` の場合、デフォルトの名前を付ける
        conv_name = conv.get("displayName")
        if not conv_name:
            conv_name = f"conversation_{i}"

        # 会話のフォルダを作成
        conv_name = conv.get("displayName", f"chat_{i}")
        safe_name = sanitize_filename(conv_name) or f"conversation_{i}"
        conv_folder = os.path.join(output_folder, safe_name)
        os.makedirs(conv_folder, exist_ok=True)

        # メッセージを時系列でソート
        messages.sort(key=lambda msg: msg.get("originalarrivaltime", ""))

        # メッセージを月ごとに分割して保存
        file_content = []
        current_month = None
        current_year = None
        current_file_size = 0
        file_index = 1  # 1ヶ月内で複数ファイルに分割するためのインデックス

        def save_current_log():
            """現在のメッセージリストをファイルに書き出す"""
            nonlocal file_content, current_year, current_month, file_index, current_file_size
            if not file_content:
                return

            file_suffix = f"_{file_index}" if file_index > 1 else ""
            output_file = os.path.join(conv_folder, f"{current_year}_{current_month:02d}{file_suffix}.txt")

            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.writelines(file_content)

            print(f"✅ {output_file} を作成しました。")
            file_content = []
            file_index += 1
            current_file_size = 0

        for msg in messages:
            timestamp = msg.get("originalarrivaltime", "Unknown Time")
            sender = msg.get("displayName", "Unknown Sender")
            text = msg.get("content", "").replace("\n", " ")  # 改行をスペースに

            try:
                msg_date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                year, month = msg_date.year, msg_date.month
                timestamp = msg_date.strftime("%Y-%m-%d %H:%M:%S")
            except:
                year, month = 9999, 99  # 不明な場合

            message_line = f"[{timestamp}] {sender}: {text}\n"
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Skype JSON logs into FESS-friendly text files.")
    parser.add_argument("input", help="Input Skype JSON log file (messages.json)")
    parser.add_argument("output_folder", help="Output folder for conversation text files")
    parser.add_argument("--max_size", type=int, default=1000, help="Max file size in KB (default: 1000KB)")

    args = parser.parse_args()
    convert_skype_log(args.input, args.output_folder, args.max_size)


# 使用例：
# python skype_log_converter.py messages.json skype_logs --max_size 1000

