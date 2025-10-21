# 🖥️ PC 모니터링 시스템

직원 PC의 스토리지, Outlook 메일 정보를 자동으로 수집하고 웹 대시보드로 관리하는 시스템입니다.

## 📋 주요 기능

### 수집 정보
- ✅ **스토리지 정보**: 각 드라이브의 전체/사용/여유 용량 및 사용률
- ✅ **Outlook PST 파일**: PST 파일 위치, 크기, 최종 수정일
- ✅ **메일 정보**: 받은편지함 전체 메일 수, 오늘 받은 메일 수
- ✅ **기본 정보**: 컴퓨터명, 사용자명, IP 주소

### 대시보드 기능
- 📊 실시간 PC 현황 모니터링
- ⚠️ 자동 경고 알림 (스토리지 80% 이상, PST 2GB 이상)
- 📈 개별 PC 상세 정보 조회
- 🔄 자동 새로고침 (30초마다)
- 📱 반응형 디자인 (모바일/태블릿 지원)

## 🚀 설치 방법

### 1. 사전 요구사항

- **서버 PC** (관리자 컴퓨터):
  - Python 3.7 이상
  - 네트워크 접근 가능 (방화벽 5000번 포트 허용)

- **클라이언트 PC** (직원 컴퓨터):
  - Windows OS
  - PowerShell 5.0 이상
  - Outlook 설치 (메일 정보 수집용)

### 2. 서버 설치

#### (1) Python 설치
Python이 설치되어 있지 않다면 [python.org](https://www.python.org/downloads/)에서 다운로드하여 설치합니다.

#### (2) 필요한 패키지 설치
```bash
pip install flask
```

#### (3) 서버 실행
```bash
cd pc-monitoring/server
python app.py
```

서버가 성공적으로 실행되면 다음과 같은 메시지가 표시됩니다:
```
============================================================
PC 모니터링 서버 시작
============================================================
📊 대시보드: http://localhost:5000
🔌 API 엔드포인트:
   - POST   /api/report                : 리포트 수신
   - GET    /api/reports/latest        : 최신 리포트 조회
   - GET    /api/reports/history/<pc>  : PC 히스토리 조회
   - GET    /api/statistics            : 통계 조회
   - GET    /api/alerts                : 경고 조회
   - POST   /api/cleanup               : 데이터 정리
============================================================
```

#### (4) 대시보드 접속
웹 브라우저에서 `http://localhost:5000` 접속

같은 네트워크의 다른 PC에서 접속하려면:
`http://서버IP주소:5000` (예: `http://192.168.1.100:5000`)

### 3. 클라이언트 배포

직원 PC에서 정보를 수집하는 방법은 3가지가 있습니다:

#### 방법 1: 로그인 스크립트 (권장)

1. `collect-info.ps1` 파일을 각 PC의 다음 위치에 복사:
   ```
   C:\Scripts\collect-info.ps1
   ```

2. PowerShell 스크립트 생성 (`C:\Scripts\startup.ps1`):
   ```powershell
   # 서버 IP 주소를 실제 서버 IP로 변경
   $serverUrl = "http://192.168.1.100:5000/api/report"

   # 정보 수집 스크립트 실행
   PowerShell.exe -ExecutionPolicy Bypass -File "C:\Scripts\collect-info.ps1" -ServerUrl $serverUrl
   ```

3. 시작 프로그램 폴더에 바로가기 생성:
   - `Win + R` → `shell:startup` 입력
   - 위에서 만든 `startup.ps1`의 바로가기를 이 폴더에 생성

#### 방법 2: 작업 스케줄러 사용

1. 작업 스케줄러 실행 (`taskschd.msc`)

2. "작업 만들기" 클릭

3. 설정:
   - **일반** 탭:
     - 이름: "PC 정보 수집"
     - "가장 높은 수준의 권한으로 실행" 체크

   - **트리거** 탭:
     - "새로 만들기" → "로그온할 때" 또는 "매일 오전 9시" 등 설정

   - **동작** 탭:
     - 프로그램: `PowerShell.exe`
     - 인수 추가:
       ```
       -ExecutionPolicy Bypass -File "C:\Scripts\collect-info.ps1" -ServerUrl "http://192.168.1.100:5000/api/report"
       ```

#### 방법 3: 수동 실행

PowerShell을 관리자 권한으로 실행 후:
```powershell
cd C:\Scripts
.\collect-info.ps1 -ServerUrl "http://192.168.1.100:5000/api/report"
```

## 📊 사용 방법

### 대시보드 화면 구성

1. **통계 카드**
   - 총 PC 수
   - 오늘 리포트 수
   - 경고 개수
   - 마지막 리포트 시간

2. **경고 알림**
   - 스토리지 부족 (80% 이상)
   - PST 파일 크기 과다 (2GB 이상)
   - 오래된 리포트 (24시간 이상)

3. **PC 목록**
   - 각 PC의 현재 상태 표시
   - 카드 클릭 시 상세 정보 확인

### 경고 레벨

- 🟢 **정상**: 모든 지표가 정상 범위
- 🟡 **경고**: 스토리지 80-90% 또는 PST 2-5GB
- 🔴 **위험**: 스토리지 90% 이상 또는 PST 5GB 이상

## 🔧 고급 설정

### 포트 변경

`server/app.py` 파일의 마지막 줄 수정:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # 5000을 원하는 포트로 변경
```

### 자동 새로고침 주기 변경

`server/static/script.js` 파일에서:
```javascript
refreshInterval = setInterval(loadDashboardData, 30000);  // 30000 = 30초
```

### 오래된 데이터 자동 삭제

서버 실행 시 또는 API 호출로 30일 이상 된 데이터 삭제:
```bash
curl -X POST http://localhost:5000/api/cleanup?days=30
```

## 📁 프로젝트 구조

```
pc-monitoring/
├── client/
│   └── collect-info.ps1        # PowerShell 정보 수집 스크립트
│
└── server/
    ├── app.py                  # Flask 웹 서버
    ├── database.py             # SQLite 데이터베이스 관리
    ├── pc_monitoring.db        # SQLite 데이터베이스 파일 (자동 생성)
    ├── templates/
    │   └── dashboard.html      # 대시보드 HTML
    └── static/
        ├── style.css           # 스타일시트
        └── script.js           # JavaScript 로직
```

## 🐛 문제 해결

### 클라이언트 스크립트가 실행되지 않음

**증상**: PowerShell 스크립트 실행 시 보안 오류
**해결**: PowerShell을 관리자 권한으로 실행 후:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Outlook 정보를 가져올 수 없음

**증상**: 메일 정보가 "not_available"로 표시됨
**원인**:
- Outlook이 설치되지 않음
- Outlook이 실행 중이지 않음
- POP3/IMAP 계정이라 COM 객체 접근 제한

**해결**:
1. Outlook을 먼저 실행
2. 스크립트를 관리자 권한으로 실행
3. PST 파일 정보는 정상적으로 수집됨

### 서버 접속 불가

**증상**: 클라이언트에서 서버로 데이터 전송 실패
**해결**:
1. 서버 PC 방화벽에서 5000번 포트 허용:
   ```
   제어판 → Windows Defender 방화벽 → 고급 설정 → 인바운드 규칙
   새 규칙 → 포트 → TCP 5000
   ```

2. 서버 IP 주소 확인:
   ```powershell
   ipconfig
   ```

3. 클라이언트에서 연결 테스트:
   ```powershell
   Test-NetConnection -ComputerName 서버IP -Port 5000
   ```

### 데이터베이스 초기화

문제 발생 시 데이터베이스를 초기화하려면:
```bash
# server 폴더에서
del pc_monitoring.db
python app.py  # 자동으로 새 DB 생성
```

## 📝 API 문서

### POST /api/report
클라이언트로부터 PC 정보 수신

**요청 본문**:
```json
{
  "computer_name": "DESKTOP-ABC123",
  "user_name": "hong.gildong",
  "ip_address": "192.168.1.50",
  "timestamp": "2025-01-15 09:30:00",
  "drives": [
    {
      "drive": "C:",
      "total_gb": 500,
      "used_gb": 350,
      "free_gb": 150,
      "used_percent": 70
    }
  ],
  "pst_files": [
    {
      "name": "Outlook.pst",
      "path": "C:\\Users\\...\\Outlook.pst",
      "size_gb": 1.5,
      "last_modified": "2025-01-15 09:00:00"
    }
  ],
  "total_pst_size_gb": 1.5,
  "mail_info": {
    "total_emails": 5000,
    "today_emails": 15,
    "inbox_size_mb": 250,
    "status": "success"
  }
}
```

### GET /api/reports/latest
각 PC의 최신 리포트 조회

### GET /api/reports/history/<computer_name>?days=7
특정 PC의 히스토리 조회 (기본 7일)

### GET /api/statistics
전체 통계 조회

### GET /api/alerts
경고 목록 조회

### POST /api/cleanup?days=30
오래된 데이터 삭제 (기본 30일)

## 🔒 보안 고려사항

- ⚠️ 현재 버전은 인증 없이 누구나 대시보드에 접속 가능
- 외부 네트워크 노출을 피하고 내부 네트워크에서만 사용
- 민감한 정보는 수집하지 않도록 스크립트 수정 가능
- HTTPS를 사용하려면 Flask SSL 설정 추가 필요

## 📮 추가 개선 사항

- [ ] 사용자 인증 추가 (로그인 기능)
- [ ] 이메일/SMS 경고 알림
- [ ] Excel 리포트 내보내기
- [ ] 더 다양한 차트/그래프
- [ ] 원격 명령 실행 (디스크 정리 등)

## 📄 라이선스

이 프로젝트는 내부 사용을 목적으로 제작되었습니다.

## 💬 문의

문제가 발생하거나 개선 사항이 있으면 관리자에게 문의하세요.
