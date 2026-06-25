#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 자동 요약 시스템
새 영상 감지 → 자막 추출 → Claude 요약 → 옵시디언/노션 저장
"""

import os
import sys
import json
import yaml
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# Windows 콘솔 UTF-8 인코딩 강제
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import feedparser
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import anthropic
from notion_client import Client as NotionClient
from googleapiclient.discovery import build

# ============================================================
# 설정 로드
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
PROCESSED_DB_PATH = SCRIPT_DIR / "processed_videos.json"

def load_config() -> dict:
    """설정 파일 로드 (환경 변수 우선)"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 환경 변수로 API 키 오버라이드 (보안 강화)
    env_mappings = {
        "ANTHROPIC_API_KEY": ("api_keys", "claude"),
        "YOUTUBE_API_KEY": ("api_keys", "youtube"),
        "NOTION_API_KEY": ("api_keys", "notion"),
        "NOTION_DATABASE_ID": ("notion", "database_id"),
    }

    for env_var, (section, key) in env_mappings.items():
        env_value = os.environ.get(env_var)
        if env_value:
            if section not in config:
                config[section] = {}
            config[section][key] = env_value

    return config

CONFIG = load_config()

# ============================================================
# 로깅 설정
# ============================================================

LOG_DIR = Path(CONFIG["paths"]["log_folder"])
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"youtube-summary-{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 처리된 영상 DB 관리
# ============================================================

def load_processed_videos() -> Dict[str, dict]:
    """처리된 영상 목록 로드"""
    if PROCESSED_DB_PATH.exists():
        with open(PROCESSED_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_processed_videos(data: Dict[str, dict]):
    """처리된 영상 목록 저장"""
    with open(PROCESSED_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_video_processed(video_id: str) -> bool:
    """영상이 이미 처리되었는지 확인"""
    processed = load_processed_videos()
    return video_id in processed

def mark_video_processed(video_id: str, video_info: dict):
    """영상을 처리됨으로 표시"""
    processed = load_processed_videos()
    processed[video_id] = {
        **video_info,
        "processed_at": datetime.now().isoformat()
    }
    save_processed_videos(processed)

# ============================================================
# YouTube 채널 모니터링
# ============================================================

def get_channel_id_from_name(channel_name: str, api_key: str) -> Optional[str]:
    """채널 이름으로 채널 ID 조회"""
    youtube = build("youtube", "v3", developerKey=api_key)

    request = youtube.search().list(
        part="snippet",
        q=channel_name,
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if response.get("items"):
        return response["items"][0]["snippet"]["channelId"]
    return None

def get_latest_videos_rss(channel_id: str, max_results: int = 5) -> List[dict]:
    """RSS 피드로 최신 영상 가져오기"""
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)

    videos = []
    for entry in feed.entries[:max_results]:
        video_id = entry.yt_videoid
        videos.append({
            "video_id": video_id,
            "title": entry.title,
            "published": entry.published,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": entry.author
        })

    return videos

def get_latest_videos_api(channel_id: str, api_key: str, max_results: int = 5) -> List[dict]:
    """YouTube Data API로 최신 영상 가져오기"""
    youtube = build("youtube", "v3", developerKey=api_key)

    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        type="video",
        maxResults=max_results
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        videos.append({
            "video_id": video_id,
            "title": snippet["title"],
            "published": snippet["publishedAt"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": snippet["channelTitle"],
            "description": snippet.get("description", ""),
            "thumbnail": snippet["thumbnails"]["high"]["url"]
        })

    return videos

# ============================================================
# 자막 추출
# ============================================================

def get_transcript(video_id: str) -> Optional[dict]:
    """영상 자막 추출 (youtube-transcript-api v1.x)"""
    try:
        # API 인스턴스 생성
        api = YouTubeTranscriptApi()

        # 사용 가능한 자막 목록 조회
        transcript_list = api.list(video_id)

        # 한국어 자막 우선 탐색
        selected_transcript = None
        for transcript in transcript_list:
            if transcript.language_code == 'ko':
                selected_transcript = transcript
                break

        # 한국어 없으면 영어
        if not selected_transcript:
            for transcript in transcript_list:
                if transcript.language_code == 'en':
                    selected_transcript = transcript
                    break

        # 둘 다 없으면 첫 번째 사용 가능한 자막
        if not selected_transcript:
            for transcript in transcript_list:
                selected_transcript = transcript
                break

        if not selected_transcript:
            logger.warning(f"자막 없음: {video_id}")
            return None

        # 자막 데이터 가져오기
        transcript_data = selected_transcript.fetch()

        # 타임스탬프와 텍스트 결합
        full_text = []
        timestamped_text = []

        for entry in transcript_data:
            start_time = int(entry.start)
            minutes = start_time // 60
            seconds = start_time % 60
            timestamp = f"{minutes:02d}:{seconds:02d}"

            text = entry.text.strip()
            full_text.append(text)
            timestamped_text.append(f"[{timestamp}] {text}")

        return {
            "full_text": " ".join(full_text),
            "timestamped": "\n".join(timestamped_text),
            "segments": transcript_data
        }

    except TranscriptsDisabled:
        logger.warning(f"자막 비활성화됨: {video_id}")
        return None
    except NoTranscriptFound:
        logger.warning(f"자막 없음: {video_id}")
        return None
    except Exception as e:
        logger.error(f"자막 추출 실패: {video_id} - {e}")
        return None

# ============================================================
# Claude 요약 생성
# ============================================================

def generate_summary(
    video_info: dict,
    transcript: dict,
    channel_config: dict
) -> str:
    """Claude API로 요약 생성"""

    client = anthropic.Anthropic(api_key=CONFIG["api_keys"]["claude"])

    category = channel_config.get("category", "일반")
    summary_focus = channel_config.get("summary_focus", "핵심 내용 요약")
    tags = channel_config.get("tags", [])

    prompt = f"""다음 YouTube 영상의 자막을 분석하여 요약해주세요.

## 영상 정보
- 채널: {video_info['channel']}
- 제목: {video_info['title']}
- 카테고리: {category}
- 요약 관점: {summary_focus}

## 자막 내용
{transcript['full_text'][:15000]}

## 요약 형식

다음 형식으로 정확하게 작성해주세요:

### 📌 핵심 포인트 (3줄 요약)
1. [첫 번째 핵심 포인트]
2. [두 번째 핵심 포인트]
3. [세 번째 핵심 포인트]

### 📝 주요 내용 (타임스탬프별)

| 시간 | 주제 | 내용 |
|------|------|------|
| 00:00 | [주제] | [1-2문장 요약] |
| ... | ... | ... |

(주요 구간 5-10개 정리)

### 💡 상세 내용

<details>
<summary>📖 전체 상세 내용 펼치기</summary>

#### [첫 번째 섹션 제목]
- 상세 내용 1
- 상세 내용 2

#### [두 번째 섹션 제목]
- 상세 내용 1
- 상세 내용 2

(영상 흐름에 따라 섹션 구분)

</details>

### 💰 투자/학습 시사점

| 항목 | 방향 | 액션 | 근거 |
|------|:----:|------|------|
| [관련 자산/주제] | 🟢/🟡/🔴 | [구체적 액션] | [근거] |

(카테고리가 경제/투자면 투자 시사점, 인문/교양이면 학습 시사점으로)

### 🔑 핵심 키워드
`키워드1` `키워드2` `키워드3` `키워드4` `키워드5`

### 💬 인상적인 문장
> "[영상에서 인상적인 문장 1-2개 인용]"
"""

    message = client.messages.create(
        model=CONFIG["summary"]["model"],
        max_tokens=CONFIG["summary"]["max_tokens"],
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

# ============================================================
# 옵시디언 저장
# ============================================================

def save_to_obsidian(
    video_info: dict,
    summary: str,
    channel_config: dict
) -> Path:
    """옵시디언에 마크다운 파일 저장"""

    vault_path = Path(CONFIG["paths"]["obsidian_vault"])
    summary_folder = CONFIG["paths"]["youtube_summary_folder"]
    channel_folder = channel_config["folder"]

    # 폴더 경로
    folder_path = vault_path / summary_folder / channel_folder
    folder_path.mkdir(parents=True, exist_ok=True)

    # 파일명 생성 (날짜-제목)
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[<>:"/\\|?*]', '', video_info['title'])[:50]
    filename = f"{date_str}-{safe_title}.md"
    file_path = folder_path / filename

    # 카테고리 이모지
    category = channel_config.get("category", "일반")
    emoji = CONFIG["category_emoji"].get(category, "📺")

    # 프론트매터 + 내용
    tags_str = "\n".join([f"  - {tag}" for tag in channel_config.get("tags", [])])

    content = f"""---
유형: 유튜브요약
채널: {video_info['channel']}
제목: "{video_info['title']}"
카테고리: {category}
날짜: {date_str}
URL: {video_info['url']}
태그:
{tags_str}
요약완료: true
---

# {emoji} {video_info['title']}

> **채널**: [[{channel_config['folder']}|{video_info['channel']}]]
> **날짜**: {video_info.get('published', date_str)[:10]}
> **링크**: [YouTube에서 보기]({video_info['url']})

---

{summary}

---

## 🔗 관련 자료

- [[_{channel_config['folder']}|{video_info['channel']} MOC]]
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"옵시디언 저장 완료: {file_path}")
    return file_path

# ============================================================
# 노션 저장
# ============================================================

def save_to_notion(
    video_info: dict,
    summary: str,
    channel_config: dict
) -> Optional[str]:
    """노션 데이터베이스에 저장"""

    try:
        notion = NotionClient(auth=CONFIG["api_keys"]["notion"])
        database_id = CONFIG["notion"]["database_id"]

        category = channel_config.get("category", "일반")
        emoji = CONFIG["category_emoji"].get(category, "📺")

        # 요약에서 핵심 포인트만 추출
        core_summary = summary.split("### 📝")[0] if "### 📝" in summary else summary[:1000]

        # 페이지 생성
        new_page = notion.pages.create(
            parent={"database_id": database_id},
            icon={"type": "emoji", "emoji": emoji},
            properties={
                "제목": {
                    "title": [{"text": {"content": video_info['title'][:100]}}]
                },
                "채널": {
                    "select": {"name": video_info['channel']}
                },
                "카테고리": {
                    "select": {"name": category}
                },
                "날짜": {
                    "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                },
                "URL": {
                    "url": video_info['url']
                },
                "태그": {
                    "multi_select": [{"name": tag} for tag in channel_config.get("tags", [])[:5]]
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📌 핵심 포인트"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": core_summary[:2000]}}]
                    }
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📝 상세 요약"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": summary[len(core_summary):4000] if len(summary) > len(core_summary) else "옵시디언에서 전체 내용 확인"}}]
                    }
                }
            ]
        )

        page_url = new_page.get("url", "")
        logger.info(f"노션 저장 완료: {page_url}")
        return page_url

    except Exception as e:
        logger.error(f"노션 저장 실패: {e}")
        return None

# ============================================================
# 메인 프로세스
# ============================================================

def process_video(video_info: dict, channel_config: dict) -> bool:
    """단일 영상 처리"""
    video_id = video_info['video_id']

    logger.info(f"처리 시작: {video_info['title']}")

    # 1. 자막 추출
    transcript = get_transcript(video_id)
    if not transcript:
        logger.warning(f"자막 없음, 스킵: {video_info['title']}")
        return False

    # 2. 요약 생성
    try:
        summary = generate_summary(video_info, transcript, channel_config)
    except Exception as e:
        logger.error(f"요약 생성 실패: {e}")
        return False

    # 3. 옵시디언 저장
    try:
        obsidian_path = save_to_obsidian(video_info, summary, channel_config)
    except Exception as e:
        logger.error(f"옵시디언 저장 실패: {e}")
        return False

    # 4. 노션 저장
    notion_url = save_to_notion(video_info, summary, channel_config)

    # 5. 처리 완료 표시
    mark_video_processed(video_id, {
        "title": video_info['title'],
        "channel": video_info['channel'],
        "url": video_info['url'],
        "obsidian_path": str(obsidian_path),
        "notion_url": notion_url
    })

    logger.info(f"처리 완료: {video_info['title']}")
    return True

def check_all_channels():
    """모든 채널의 새 영상 체크 및 처리"""
    logger.info("=" * 50)
    logger.info("YouTube 자동 요약 시작")
    logger.info("=" * 50)

    api_key = CONFIG["api_keys"]["youtube"]
    processed_count = 0

    for channel_config in CONFIG["channels"]:
        channel_name = channel_config["name"]
        channel_id = channel_config.get("channel_id", "")

        logger.info(f"\n채널 체크: {channel_name}")

        # 채널 ID가 없으면 조회
        if not channel_id:
            channel_id = get_channel_id_from_name(channel_name, api_key)
            if channel_id:
                logger.info(f"채널 ID 발견: {channel_id}")
            else:
                logger.warning(f"채널 ID 찾기 실패: {channel_name}")
                continue

        # 최신 영상 가져오기
        try:
            videos = get_latest_videos_api(channel_id, api_key, max_results=3)
        except Exception as e:
            logger.error(f"영상 목록 조회 실패: {e}")
            # RSS 폴백
            try:
                videos = get_latest_videos_rss(channel_id, max_results=3)
            except:
                continue

        # 새 영상 처리
        for video in videos:
            video_id = video['video_id']

            if is_video_processed(video_id):
                logger.info(f"이미 처리됨: {video['title'][:30]}...")
                continue

            # 처리
            success = process_video(video, channel_config)
            if success:
                processed_count += 1

    logger.info("=" * 50)
    logger.info(f"완료! 처리된 영상: {processed_count}개")
    logger.info("=" * 50)

    return processed_count

# ============================================================
# 엔트리 포인트
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube 자동 요약 시스템")
    parser.add_argument("--single", type=str, help="단일 영상 URL 처리")
    parser.add_argument("--channel", type=str, help="특정 채널만 체크")
    parser.add_argument("--setup", action="store_true", help="채널 ID 설정 도우미")

    args = parser.parse_args()

    if args.setup:
        # 채널 ID 설정 도우미
        print("\n=== 채널 ID 설정 도우미 ===\n")
        api_key = CONFIG["api_keys"]["youtube"]

        for channel_config in CONFIG["channels"]:
            name = channel_config["name"]
            existing_id = channel_config.get("channel_id", "")

            if existing_id:
                print(f"✅ {name}: {existing_id}")
            else:
                channel_id = get_channel_id_from_name(name, api_key)
                if channel_id:
                    print(f"🔍 {name}: {channel_id}")
                else:
                    print(f"❌ {name}: 찾을 수 없음")

        print("\n위 채널 ID를 config.yaml에 복사하세요.")

    elif args.single:
        # 단일 영상 처리
        video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', args.single)
        if video_id_match:
            video_id = video_id_match.group(1)
            # 기본 설정으로 처리
            video_info = {
                "video_id": video_id,
                "title": "Manual Video",
                "url": args.single,
                "channel": "Unknown"
            }
            # 첫 번째 채널 설정 사용
            process_video(video_info, CONFIG["channels"][0])
        else:
            print("올바른 YouTube URL이 아닙니다.")

    else:
        # 전체 채널 체크
        check_all_channels()
