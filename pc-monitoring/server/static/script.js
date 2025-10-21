// 전역 변수
let pcReports = [];
let alerts = [];
let refreshInterval;

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentTime();
    loadDashboardData();

    // 30초마다 자동 새로고침
    refreshInterval = setInterval(loadDashboardData, 30000);

    // 1초마다 시계 업데이트
    setInterval(updateCurrentTime, 1000);
});

// 현재 시간 업데이트
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// 대시보드 데이터 로드
async function loadDashboardData() {
    try {
        // 병렬로 데이터 가져오기
        const [statsRes, reportsRes, alertsRes] = await Promise.all([
            fetch('/api/statistics'),
            fetch('/api/reports/latest'),
            fetch('/api/alerts')
        ]);

        const statsData = await statsRes.json();
        const reportsData = await reportsRes.json();
        const alertsData = await alertsRes.json();

        if (statsData.status === 'success') {
            updateStatistics(statsData.data);
        }

        if (reportsData.status === 'success') {
            pcReports = reportsData.data;
            updatePCList(pcReports);
        }

        if (alertsData.status === 'success') {
            alerts = alertsData.data;
            updateAlerts(alerts);
        }

    } catch (error) {
        console.error('데이터 로드 실패:', error);
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
    }
}

// 통계 업데이트
function updateStatistics(stats) {
    document.getElementById('total-pcs').textContent = stats.total_pcs || 0;
    document.getElementById('today-reports').textContent = stats.today_reports || 0;
    document.getElementById('total-alerts').textContent = alerts.length;

    if (stats.last_report_time) {
        const lastTime = new Date(stats.last_report_time);
        const now = new Date();
        const diffMinutes = Math.floor((now - lastTime) / 1000 / 60);

        let timeText;
        if (diffMinutes < 1) {
            timeText = '방금 전';
        } else if (diffMinutes < 60) {
            timeText = `${diffMinutes}분 전`;
        } else if (diffMinutes < 1440) {
            timeText = `${Math.floor(diffMinutes / 60)}시간 전`;
        } else {
            timeText = `${Math.floor(diffMinutes / 1440)}일 전`;
        }

        document.getElementById('last-report-time').textContent = timeText;
    } else {
        document.getElementById('last-report-time').textContent = '-';
    }
}

// 경고 업데이트
function updateAlerts(alertsList) {
    const alertsSection = document.getElementById('alerts-section');
    const alertsContainer = document.getElementById('alerts-container');

    if (alertsList.length === 0) {
        alertsSection.style.display = 'none';
        return;
    }

    alertsSection.style.display = 'block';
    alertsContainer.innerHTML = '';

    alertsList.forEach(alert => {
        const alertItem = document.createElement('div');
        alertItem.className = `alert-item ${alert.severity}`;

        alertItem.innerHTML = `
            <div class="alert-content">
                <div class="alert-computer">💻 ${alert.computer_name}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
            <div class="alert-time">${formatDateTime(alert.timestamp)}</div>
        `;

        alertsContainer.appendChild(alertItem);
    });
}

// PC 목록 업데이트
function updatePCList(reports) {
    const pcList = document.getElementById('pc-list');

    if (reports.length === 0) {
        pcList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-text">아직 리포트가 없습니다.</div>
            </div>
        `;
        return;
    }

    pcList.innerHTML = '';

    reports.forEach(report => {
        const pcCard = createPCCard(report);
        pcList.appendChild(pcCard);
    });
}

// PC 카드 생성
function createPCCard(report) {
    const card = document.createElement('div');
    card.className = 'pc-card';
    card.onclick = () => showPCDetail(report);

    // 상태 판단
    const now = new Date();
    const reportTime = new Date(report.timestamp);
    const hoursAgo = (now - reportTime) / 1000 / 60 / 60;

    let status = 'online';
    let statusText = '정상';

    if (hoursAgo > 24) {
        status = 'offline';
        statusText = '오래됨';
    } else if (hasWarnings(report)) {
        status = 'warning';
        statusText = '경고';
    }

    // 드라이브 정보 생성
    let drivesHTML = '';
    if (report.drives && report.drives.length > 0) {
        drivesHTML = report.drives.map(drive => {
            const usedPercent = drive.used_percent || 0;
            let progressClass = 'normal';
            if (usedPercent >= 90) progressClass = 'danger';
            else if (usedPercent >= 80) progressClass = 'warning';

            return `
                <div class="drive-item">
                    <div class="drive-label">
                        <span>${drive.drive} 드라이브</span>
                        <span>${usedPercent}% (${drive.free_gb}GB 여유)</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill ${progressClass}" style="width: ${usedPercent}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    const displayName = report.display_name || report.user_name;
    const primaryEmail = report.active_email_accounts && report.active_email_accounts.length > 0
        ? report.active_email_accounts[0].email_address
        : '-';

    // 아카이브 날짜 표시 및 경고
    let archiveDateHTML = '';
    if (report.last_archive_date) {
        const archiveDate = new Date(report.last_archive_date);
        const daysSince = Math.floor((new Date() - archiveDate) / (1000 * 60 * 60 * 24));
        let archiveColor = '#4caf50'; // 녹색
        if (daysSince >= 180) archiveColor = '#f44336'; // 빨강 (6개월+)
        else if (daysSince >= 90) archiveColor = '#ff9800'; // 주황 (3개월+)

        archiveDateHTML = `
            <span class="editable-archive" onclick="editArchiveDate(event, '${report.computer_name}', '${report.last_archive_date}')"
                  title="클릭하여 수정" style="color: ${archiveColor}">
                ${report.last_archive_date} (${daysSince}일 전)
                <span style="font-size: 12px; color: #999; margin-left: 5px;">✏️</span>
            </span>
        `;
    } else {
        archiveDateHTML = `
            <span class="editable-archive" onclick="editArchiveDate(event, '${report.computer_name}', null)"
                  title="클릭하여 설정" style="color: #999;">
                미설정
                <span style="font-size: 12px; color: #999; margin-left: 5px;">✏️</span>
            </span>
        `;
    }

    card.innerHTML = `
        <div class="pc-card-header">
            <div class="pc-name">💻 ${report.computer_name}</div>
            <div class="pc-status ${status}">${statusText}</div>
        </div>
        <div class="pc-info">
            <div class="pc-info-row">
                <span class="pc-info-label">👤 사용자:</span>
                <span class="editable-user" onclick="editUserName(event, '${report.computer_name}', '${report.user_name}', '${displayName}')" title="클릭하여 수정">
                    ${displayName}
                    <span style="font-size: 12px; color: #999; margin-left: 5px;">✏️</span>
                </span>
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">📧 메일 계정:</span>
                <span title="${primaryEmail}">${primaryEmail.length > 25 ? primaryEmail.substring(0, 22) + '...' : primaryEmail}</span>
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">📅 마지막 아카이브:</span>
                ${archiveDateHTML}
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">🌐 IP:</span>
                <span>${report.ip_address || '-'}</span>
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">📧 기간 메일:</span>
                <span>${report.mail_info.period_emails || report.mail_info.today_emails || 0}개</span>
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">📦 PST 크기:</span>
                <span>${report.total_pst_size_gb || 0}GB</span>
            </div>
            <div class="pc-info-row">
                <span class="pc-info-label">🕐 마지막 리포트:</span>
                <span>${formatDateTime(report.timestamp)}</span>
            </div>
        </div>
        <div class="drive-info">
            ${drivesHTML}
        </div>
    `;

    return card;
}

// 경고 여부 확인
function hasWarnings(report) {
    // 스토리지 경고
    if (report.drives) {
        for (const drive of report.drives) {
            if (drive.used_percent >= 80) return true;
        }
    }

    // PST 크기 경고
    if (report.total_pst_size_gb >= 2) return true;

    return false;
}

// PC 상세 정보 표시
function showPCDetail(report) {
    const modal = document.getElementById('detail-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modalTitle.textContent = `💻 ${report.computer_name} - 상세 정보`;

    let detailHTML = `
        <div class="detail-section">
            <h3>📋 기본 정보</h3>
            <table class="detail-table">
                <tr>
                    <th>컴퓨터명</th>
                    <td>${report.computer_name}</td>
                </tr>
                <tr>
                    <th>사용자명</th>
                    <td>${report.user_name}</td>
                </tr>
                <tr>
                    <th>IP 주소</th>
                    <td>${report.ip_address || '-'}</td>
                </tr>
                <tr>
                    <th>리포트 시간</th>
                    <td>${formatDateTime(report.timestamp)}</td>
                </tr>
            </table>
        </div>
    `;

    // 드라이브 정보
    if (report.drives && report.drives.length > 0) {
        detailHTML += `
            <div class="detail-section">
                <h3>💾 스토리지 정보</h3>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>드라이브</th>
                            <th>전체 용량</th>
                            <th>사용 용량</th>
                            <th>여유 공간</th>
                            <th>사용률</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.drives.map(drive => `
                            <tr>
                                <td>${drive.drive}</td>
                                <td>${drive.total_gb} GB</td>
                                <td>${drive.used_gb} GB</td>
                                <td>${drive.free_gb} GB</td>
                                <td>
                                    <span style="color: ${drive.used_percent >= 90 ? '#f44336' : drive.used_percent >= 80 ? '#ff9800' : '#4caf50'}">
                                        ${drive.used_percent}%
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // PST 파일 정보
    if (report.pst_files && report.pst_files.length > 0) {
        detailHTML += `
            <div class="detail-section">
                <h3>📧 Outlook PST 파일</h3>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>파일명</th>
                            <th>크기</th>
                            <th>최종 수정</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.pst_files.map(pst => `
                            <tr>
                                <td>${pst.name}</td>
                                <td>${pst.size_gb} GB</td>
                                <td>${pst.last_modified}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <p style="margin-top: 10px; color: #666;">
                    <strong>총 PST 크기:</strong> ${report.total_pst_size_gb} GB
                </p>
            </div>
        `;
    }

    // Active Email Accounts
    if (report.active_email_accounts && report.active_email_accounts.length > 0) {
        detailHTML += `
            <div class="detail-section">
                <h3>📧 활성 이메일 계정</h3>
                <table class="detail-table">
                    <thead>
                        <tr>
                            <th>표시 이름</th>
                            <th>이메일 주소</th>
                            <th>계정 유형</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${report.active_email_accounts.map(account => `
                            <tr>
                                <td>${account.display_name || '-'}</td>
                                <td>${account.email_address || '-'}</td>
                                <td>${account.account_type || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // 메일 정보
    if (report.mail_info && report.mail_info.status === 'success') {
        detailHTML += `
            <div class="detail-section">
                <h3>✉️ 메일 정보</h3>
                <table class="detail-table">
                    <tr>
                        <th>전체 메일 수</th>
                        <td>${report.mail_info.total_emails || 0}개</td>
                    </tr>
                    <tr>
                        <th>기간 메일 수 (Toronto 어제 7PM - 오늘 8AM)</th>
                        <td>${report.mail_info.period_emails || report.mail_info.today_emails || 0}개</td>
                    </tr>
                    <tr>
                        <th>받은편지함 크기 (예상)</th>
                        <td>${report.mail_info.inbox_size_mb || 0} MB</td>
                    </tr>
                </table>
            </div>
        `;
    } else {
        detailHTML += `
            <div class="detail-section">
                <h3>✉️ 메일 정보</h3>
                <p style="color: #999;">Outlook 정보를 가져올 수 없습니다.</p>
            </div>
        `;
    }

    modalBody.innerHTML = detailHTML;
    modal.style.display = 'block';
}

// 모달 닫기
function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        closeModal();
    }
}

// 날짜/시간 포맷팅
function formatDateTime(dateString) {
    if (!dateString) return '-';

    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 데이터 새로고침
function refreshData() {
    loadDashboardData();
}

// 에러 표시
function showError(message) {
    alert(message);
}

// 사용자 이름 편집
function editUserName(event, computerName, windowsUser, currentDisplayName) {
    event.stopPropagation(); // PC 카드 클릭 이벤트 방지

    const newName = prompt('새 사용자 이름을 입력하세요:', currentDisplayName);

    if (newName && newName !== currentDisplayName) {
        updateUserName(computerName, windowsUser, newName);
    }
}

// 사용자 이름 업데이트 API 호출
async function updateUserName(computerName, windowsUser, displayName) {
    try {
        const response = await fetch(`/api/user-mappings/${computerName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                windows_user: windowsUser,
                display_name: displayName
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // 성공 시 데이터 새로고침
            loadDashboardData();
            alert(`사용자 이름이 "${displayName}"(으)로 변경되었습니다.`);
        } else {
            alert('사용자 이름 변경 실패: ' + data.message);
        }
    } catch (error) {
        console.error('Error updating user name:', error);
        alert('사용자 이름 변경 중 오류가 발생했습니다.');
    }
}

// 아카이브 날짜 편집
function editArchiveDate(event, computerName, currentDate) {
    event.stopPropagation(); // PC 카드 클릭 이벤트 방지

    const defaultDate = currentDate || new Date().toISOString().split('T')[0];
    const newDate = prompt('아카이브 날짜를 입력하세요 (YYYY-MM-DD):', defaultDate);

    if (newDate && newDate !== currentDate) {
        // 날짜 형식 검증
        if (!/^\d{4}-\d{2}-\d{2}$/.test(newDate)) {
            alert('날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)');
            return;
        }

        updateArchiveDate(computerName, newDate);
    }
}

// 아카이브 날짜 업데이트 API 호출
async function updateArchiveDate(computerName, archiveDate) {
    try {
        const response = await fetch(`/api/archive-date/${computerName}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                archive_date: archiveDate
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // 성공 시 데이터 새로고침
            loadDashboardData();
            alert(`아카이브 날짜가 "${archiveDate}"(으)로 변경되었습니다.`);
        } else {
            alert('아카이브 날짜 변경 실패: ' + data.message);
        }
    } catch (error) {
        console.error('Error updating archive date:', error);
        alert('아카이브 날짜 변경 중 오류가 발생했습니다.');
    }
}
