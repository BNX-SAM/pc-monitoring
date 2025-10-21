# 📦 클라이언트 배포 가이드

이 문서는 직원 PC에 모니터링 클라이언트를 배포하는 방법을 설명합니다.

## 🎯 배포 개요

각 직원 PC에서 매일 점심 12시에 자동으로 PC 정보를 수집하여 서버로 전송하도록 설정합니다.

## 📋 사전 준비

### 1. 서버 정보 확인

서버 PC에서 Flask 서버를 실행하면 다음과 같이 IP 주소가 표시됩니다:

```
============================================================
PC 모니터링 서버 시작
============================================================
📊 대시보드:
   - Local:   http://localhost:5000
   - Network: http://192.168.2.76:5000    ← 이 IP를 사용
```

**Network IP 주소**를 메모해두세요. (예: `192.168.2.76`)

### 2. 배포 파일 준비

프로젝트의 `client/` 폴더를 SMB 공유 또는 USB에 준비:

- ✅ `collect-info.ps1` - 정보 수집 스크립트
- ✅ `quick-install.ps1` - 원클릭 설치 스크립트 (권장)
- ✅ `install.bat` - 배치 파일 설치 스크립트
- ✅ `setup-schedule.ps1` - 수동 설정용

## 🚀 배포 방법 (권장)

### 원클릭 설치 스크립트 사용

가장 쉽고 빠른 방법입니다.

## 🚀 각 직원 PC에서 실행할 단계

### 1단계: 파일 복사

프로젝트의 `client/` 폴더에서 다음 파일들을 `C:\Scripts\`로 복사:

- `collect-info.ps1`
- `quick-install.ps1`

**복사 방법**:
- USB 드라이브 사용
- 이메일로 전달
- 네트워크 공유 폴더 사용

### 2단계: 설치 실행

PowerShell을 **관리자 권한으로 실행** 후:

```powershell
cd C:\Scripts
powershell -ExecutionPolicy Bypass -File ".\quick-install.ps1"
```

**완료!** 스크립트가 자동으로:
- ✅ 작업 스케줄러에 "PC Monitoring Collection" 작업 등록
- ✅ 매일 오후 12:00에 자동 실행 설정
- ✅ 네트워크 연결 시에만 실행
- ✅ 숨김 모드로 백그라운드 실행

### 3단계: 테스트 실행

설정 스크립트가 완료되면 테스트 실행 여부를 물어봅니다:

```
Do you want to test run now? (Y/N)
```

`Y`를 입력하면 즉시 실행되어 서버로 데이터가 전송됩니다.

### 4단계: 서버에서 확인

서버 대시보드(`http://192.168.2.76:5000`)에 접속하여 해당 PC가 나타나는지 확인합니다.

---

## 💡 참고: PowerShell 실행 정책 오류가 발생하는 경우

위의 방법을 사용하면 실행 정책 오류가 발생하지 않습니다. `-ExecutionPolicy Bypass` 옵션이 포함되어 있기 때문입니다.

## 🔧 수동 설정 (고급 사용자)

자동 설정 스크립트를 사용하지 않고 수동으로 설정하려면:

### 1. 작업 스케줄러 열기

```
Win + R → taskschd.msc
```

### 2. 작업 만들기

**일반 탭:**
- 이름: `PC Monitoring Collection`
- 설명: `Collects PC information and sends to monitoring server`
- "가장 높은 수준의 권한으로 실행" 체크
- "사용자가 로그온했는지 여부에 관계없이 실행" 선택

**트리거 탭:**
- 새로 만들기
- 작업 시작: `일정에 따라`
- 설정: `매일`
- 시작 시간: `12:00:00 PM`
- 사용: 체크

**동작 탭:**
- 새로 만들기
- 작업: `프로그램 시작`
- 프로그램/스크립트: `powershell.exe`
- 인수 추가:
  ```
  -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Scripts\collect-info.ps1" -ServerUrl "http://192.168.2.76:5000/api/report"
  ```

**설정 탭:**
- ✅ "배터리 사용 시 작업 중지" 해제
- ✅ "AC 전원 사용 시에만 시작" 해제
- ✅ "네트워크 연결 시에만 시작" 체크
- ✅ "작업이 이미 실행 중이면 다음 규칙 적용" → "새 인스턴스 무시"

## 📊 확인 방법

### 작업이 정상 등록되었는지 확인

```powershell
# PowerShell에서 확인
Get-ScheduledTask -TaskName "PC Monitoring Collection"
```

### 작업 수동 실행 (테스트)

```powershell
Start-ScheduledTask -TaskName "PC Monitoring Collection"
```

### 작업 실행 기록 확인

작업 스케줄러에서:
1. "작업 스케줄러 라이브러리" → "PC Monitoring Collection" 선택
2. 하단 "기록" 탭에서 실행 결과 확인

### 로그 파일 확인

실패 시 로컬에 저장된 JSON 확인:

```powershell
Get-Content "$env:TEMP\pc-info-report.json"
```

## 🐛 문제 해결

### PowerShell 실행 정책 오류

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

### 작업이 실행되지 않음

1. **네트워크 연결 확인**
   ```powershell
   Test-NetConnection -ComputerName 192.168.2.76 -Port 5000
   ```

2. **서버 접근 테스트**
   ```powershell
   Invoke-WebRequest -Uri "http://192.168.2.76:5000" -UseBasicParsing
   ```

3. **수동으로 스크립트 실행 테스트**
   ```powershell
   cd C:\Scripts
   .\collect-info.ps1 -ServerUrl "http://192.168.2.76:5000/api/report"
   ```

### Outlook 정보를 가져올 수 없음

- Outlook이 설치되어 있는지 확인
- Outlook을 한 번 실행하여 프로필 설정
- 스크립트를 관리자 권한으로 실행

## 🔄 업데이트 방법

스크립트를 업데이트해야 할 경우:

1. 새 버전의 `collect-info.ps1`을 `C:\Scripts\`에 복사 (덮어쓰기)
2. 작업 스케줄러 설정은 그대로 유지됨
3. 다음 예약 시간에 자동으로 새 버전 실행

## 📝 대량 배포 (고급)

### GPO (Group Policy) 사용

Active Directory 환경에서는 GPO를 통해 일괄 배포 가능:

1. 공유 폴더에 스크립트 배치
2. GPO에서 로그온 스크립트로 설정
3. 또는 GPO에서 예약된 작업으로 배포

### PowerShell 원격 실행

관리자가 원격으로 여러 PC에 배포:

```powershell
# 대상 PC 목록
$computers = @("PC01", "PC02", "PC03")

foreach ($pc in $computers) {
    Invoke-Command -ComputerName $pc -ScriptBlock {
        # Scripts 폴더 생성
        New-Item -Path "C:\Scripts" -ItemType Directory -Force

        # 파일 복사
        Copy-Item "\\ServerPC\share\client\*.ps1" -Destination "C:\Scripts\"

        # 작업 스케줄러 등록
        & "C:\Scripts\setup-schedule.ps1"
    }
}
```

## ✅ 체크리스트

배포 완료 후 확인:

- [ ] `C:\Scripts\` 폴더에 두 개의 .ps1 파일 존재
- [ ] `setup-schedule.ps1`에서 서버 URL이 올바르게 설정됨
- [ ] 작업 스케줄러에 "PC Monitoring Collection" 작업 등록됨
- [ ] 작업이 "준비"(Ready) 상태
- [ ] 테스트 실행 시 서버 대시보드에 PC 정보 표시됨
- [ ] 다음 예약 실행 시간이 오늘 12:00 PM으로 설정됨

## 📞 지원

문제가 발생하면:
1. 서버 대시보드에서 PC 상태 확인
2. `$env:TEMP\pc-info-report.json` 로그 확인
3. 작업 스케줄러 기록 탭 확인
4. IT 관리자에게 문의
