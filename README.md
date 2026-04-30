# 경쟁사 뉴스 모니터링 (Fintech Competitive Monitor)

비버웍스 경영관리본부에서 운영하는 오프라인 결제·매장관리 시장 30개 경쟁사 일일 뉴스 모니터링 대시보드.

## 작동 방식

- 매일 한국 시간 기준 09/11/13/15/17/19시에 GitHub Actions가 자동 실행
- 네이버 검색 API로 30개 경쟁사 최신 뉴스(최근 14일) 수집
- `index.html` 자동 생성 후 commit/push
- GitHub Pages가 사이트 자동 갱신

## 추적 업체 (4개 카테고리, 30개)

- **POS/테이블오더/키오스크 (12)**: 티오더, 페이히어, 하나시스, 포스뱅크, 오케이포스, 캐치테이블, 메뉴잇, 한국전자금융, 씨아이테크, 니스인프라, 성신이노텍, 푸른기술
- **결제 PG/VAN (9)**: 토스플레이스, 한국신용데이터(KCD), KG이니시스, NHN한국사이버결제, 헥토파이낸셜, KICC, KPN, 나이스페이먼츠, 토스페이먼츠
- **멤버십/브랜드앱 (4)**: 발트루스트, 도도포인트, 채널톡, 리뷰노트
- **빅테크/플랫폼 (5)**: 네이버, 카카오, 토스, 배달의민족, 당근

## 파일 구성

```
fintech-monitor/
├── index.html               # 공개 대시보드 (자동 갱신됨)
├── template.html            # HTML 템플릿
├── update.py                # 뉴스 수집·HTML 생성 스크립트
├── README.md                # 이 파일
└── .github/workflows/
    └── update.yml           # GitHub Actions 워크플로우
```

## 필요한 GitHub Secrets

`Settings → Secrets and variables → Actions`에 등록:

| Secret 이름 | 값 |
|---|---|
| `NAVER_CLIENT_ID` | 네이버 개발자센터에서 발급한 Client ID |
| `NAVER_CLIENT_SECRET` | 네이버 개발자센터에서 발급한 Client Secret |

## 수동 실행 방법

1. 저장소의 `Actions` 탭 진입
2. 좌측에서 `Update Competitor News` 워크플로우 선택
3. 우측 상단 `Run workflow` 버튼 클릭

## 라이선스

내부 사용 전용.
