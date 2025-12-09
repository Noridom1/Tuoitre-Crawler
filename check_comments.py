import os
import json

DATA_DIR = "crawled_data"   # <-- change this to your folder path
COMMENT_THRESHOLD = 20

def count_comments_recursive(comments, current_depth=1):
    total = 0
    max_depth = current_depth

    for comment in comments:
        total += 1  # count this comment

        replies = comment.get("replies", [])
        if isinstance(replies, list) and replies:
            cnt, child_depth = count_comments_recursive(replies, current_depth + 1)
            total += cnt

            # ✅ track the deepest level
            max_depth = max(max_depth, child_depth)

    return total, max_depth


def main():
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(DATA_DIR, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read {filename}: {e}")
            continue

        comments = data.get("comments", [])
        if not isinstance(comments, list):
            continue

        total_comments, max_depth = count_comments_recursive(comments)

        if total_comments > COMMENT_THRESHOLD:
            url = data.get("url", "UNKNOWN_URL")
            category = data.get("category", "UNKNOWN_CATEGORY")

            print(f"[MATCH] {total_comments} comments | {max_depth} depth | {category} | {url}")


if __name__ == "__main__":
    main()
