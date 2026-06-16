"""為既有影片設定自訂縮圖（頻道需已通過手機驗證）。

用法:
    python set_thumbnail.py <videoId> <thumbnail.png>
"""
import os
import sys

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from upload_youtube import get_credentials


def main():
    video_id, thumb = sys.argv[1], sys.argv[2]
    if not os.path.exists(thumb):
        sys.exit(f"找不到縮圖檔：{thumb}")
    yt = build("youtube", "v3", credentials=get_credentials())
    yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb)).execute()
    print(f"OK: 已設定縮圖 → https://youtu.be/{video_id}")


if __name__ == "__main__":
    main()
