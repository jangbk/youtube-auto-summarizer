# 📺 YouTube 자동 요약 시스템

YouTube 채널의 새 영상을 자동 감지하고, Claude AI로 요약하여 Obsidian과 Notion에 저장하는 자동화 시스템입니다.

## ✨ 주요 기능

- 🔄 **자동 모니터링**: 등록된 YouTube 채널의 새 영상 자동 감지 (30분 간격)
- 📝 **AI 요약**: Claude API를 활용한 지능형 요약
  - 핵심 포인트 (3줄 요약)
  - 타임스탬프별 상세 내용
  - 투자/학습 시사점
- 💾 **이중 저장**: Obsidian 마크다운 + Notion 데이터베이스
- 🏷️ **자동 분류**: 채널별 카테고리 및 태그 자동 적용

## 📁 파일 구조

```
youtube-summarizer/
├── youtube_summarizer.py   # 메인 스크립트
├── config.yaml             # 설정 파일 (API 키, 채널 목록)
├── requirements.txt        # Python 의존성
├── processed_videos.json   # 처리된 영상 DB
├── setup.ps1               # 초기 설정 스크립트
├── register_scheduler.ps1  # 스케줄러 등록
├── run_summarizer.bat      # 수동 실행용 배치
└── README.md               # 이 파일
```

## 🚀 설치 방법

### 1. 사전 요구사항

- Python 3.10+
- API 키:
  - [Claude API](https://console.anthropic.com/) - 요약 생성
  - [YouTube Data API v3](https://console.cloud.google.com/) - 채널 모니터링
  - [Notion API](https://developers.notion.com/) - Notion 저장

### 2. 설치

```powershell
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/youtube-auto-summarizer.git
cd youtube-auto-summarizer

# 2. 초기 설정 실행
PowerShell -ExecutionPolicy Bypass -File setup.ps1
```

### 3. 설정

`config.yaml` 파일을 열어 다음 항목을 설정:

```yaml
api_keys:
  claude: "YOUR_CLAUDE_API_KEY"
  youtube: "YOUR_YOUTUBE_DATA_API_KEY"
  notion: "YOUR_NOTION_API_KEY"

notion:
  database_id: "YOUR_NOTION_DATABASE_ID"
```

### 4. 채널 ID 설정

```powershell
# 채널 이름으로 ID 조회
python youtube_summarizer.py --setup
```

출력된 채널 ID를 `config.yaml`의 각 채널 `channel_id`에 입력

### 5. 테스트 실행

```powershell
# 전체 채널 체크
python youtube_summarizer.py

# 단일 영상 테스트
python youtube_summarizer.py --single "https://youtube.com/watch?v=VIDEO_ID"
```

### 6. 자동화 등록

```powershell
# 30분마다 자동 실행 (기본값)
.\register_scheduler.ps1

# 60분마다 실행
.\register_scheduler.ps1 -IntervalMinutes 60

# 스케줄러 삭제
.\register_scheduler.ps1 -Unregister
```

## ⚙️ 설정 상세

### config.yaml 구조

```yaml
# API 키
api_keys:
  claude: "sk-ant-..."
  youtube: "AIza..."
  notion: "secret_..."

# Notion 데이터베이스
notion:
  database_id: "abc123..."

# 저장 경로
paths:
  obsidian_vault: "C:\\Users\\...\\Obsidian Vault"
  youtube_summary_folder: "P_개인\\50_유튜브요약"

# 추적 채널
channels:
  - name: "채널명"
    channel_id: "UC..."
    category: "경제/시사"
    folder: "채널-폴더명"
    tags: ["태그1", "태그2"]
    summary_focus: "요약 시 집중할 관점"
```

### Notion 데이터베이스 속성

Notion에 다음 속성을 가진 데이터베이스 생성 필요:

| 속성명 | 타입 |
|--------|------|
| 제목 | Title |
| 채널 | Select |
| 카테고리 | Select |
| 날짜 | Date |
| URL | URL |
| 태그 | Multi-select |

## 📊 요약 출력 형식

```markdown
# 📊 영상 제목

## 📌 핵심 포인트 (3줄 요약)
1. 첫 번째 포인트
2. 두 번째 포인트
3. 세 번째 포인트

## 📝 주요 내용 (타임스탬프별)
| 시간 | 주제 | 내용 |
|------|------|------|
| 00:00 | 인트로 | ... |
| 05:30 | 본론 | ... |

## 💡 상세 내용
<details>
<summary>📖 전체 상세 내용 펼치기</summary>
...
</details>

## 💰 투자/학습 시사점
| 항목 | 방향 | 액션 | 근거 |
|------|:----:|------|------|
| 주식 | 🟢 | 매수 | ... |
```

## 🔧 트러블슈팅

### 자막 없음 오류
- 일부 영상은 자막이 비활성화되어 있음
- 자동 생성 자막도 없는 경우 스킵됨

### API 할당량 초과
- YouTube Data API: 일일 10,000 유닛 제한
- 채널당 3개 영상 × 100 유닛 = 채널당 300 유닛
- 5개 채널 × 48회/일 = 72,000 유닛 필요 → RSS 폴백 사용

### Notion 저장 실패
- 데이터베이스 속성명 확인 (한글/영문 일치)
- Integration이 데이터베이스에 연결되어 있는지 확인

## 📝 로그 확인

```powershell
# 오늘 로그
Get-Content "C:\Users\GS\.claude\logs\youtube-summary-$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50

# 실시간 모니터링
Get-Content "C:\Users\GS\.claude\logs\youtube-summary-*.log" -Tail 20 -Wait
```

## 🔄 채널 추가

1. `config.yaml`의 `channels` 섹션에 새 채널 추가
2. `python youtube_summarizer.py --setup`으로 채널 ID 확인
3. 채널 ID 입력 후 저장

## 📜 라이선스

MIT License

## 🙏 기여

이슈와 PR 환영합니다!

---

Made with ❤️ and Claude AI
