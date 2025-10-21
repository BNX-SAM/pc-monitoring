# -*- coding: utf-8 -*-
"""
데이터베이스 관리 모듈
SQLite를 사용하여 PC 정보를 저장하고 조회합니다.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "pc_monitoring.db"):
        """데이터베이스 초기화"""
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """데이터베이스 연결 생성"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn

    def init_database(self):
        """데이터베이스 테이블 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # PC 정보 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pc_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computer_name TEXT NOT NULL,
                user_name TEXT NOT NULL,
                ip_address TEXT,
                timestamp TEXT NOT NULL,
                drives_info TEXT,  -- JSON 형태로 저장
                pst_files TEXT,    -- JSON 형태로 저장
                total_pst_size_gb REAL,
                mail_info TEXT,    -- JSON 형태로 저장
                active_email_accounts TEXT,  -- JSON 형태로 저장
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 사용자 이름 매핑 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computer_name TEXT NOT NULL UNIQUE,
                windows_user TEXT NOT NULL,
                display_name TEXT NOT NULL,
                last_archive_date TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 인덱스 생성 (검색 성능 향상)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_computer_name
            ON pc_reports(computer_name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON pc_reports(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_mapping_computer
            ON user_mappings(computer_name)
        ''')

        conn.commit()
        conn.close()

    def save_report(self, report_data: Dict) -> int:
        """
        PC 리포트 저장

        Args:
            report_data: 리포트 데이터 딕셔너리

        Returns:
            저장된 리포트 ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO pc_reports (
                computer_name, user_name, ip_address, timestamp,
                drives_info, pst_files, total_pst_size_gb, mail_info, active_email_accounts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_data.get('computer_name'),
            report_data.get('user_name'),
            report_data.get('ip_address'),
            report_data.get('timestamp'),
            json.dumps(report_data.get('drives', []), ensure_ascii=False),
            json.dumps(report_data.get('pst_files', []), ensure_ascii=False),
            report_data.get('total_pst_size_gb', 0),
            json.dumps(report_data.get('mail_info', {}), ensure_ascii=False),
            json.dumps(report_data.get('active_email_accounts', []), ensure_ascii=False)
        ))

        report_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return report_id

    def get_latest_reports(self) -> List[Dict]:
        """
        각 PC의 최신 리포트 조회

        Returns:
            최신 리포트 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 각 컴퓨터별로 가장 최근 리포트만 가져오기
        cursor.execute('''
            SELECT * FROM pc_reports
            WHERE id IN (
                SELECT MAX(id)
                FROM pc_reports
                GROUP BY computer_name
            )
            ORDER BY timestamp DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        reports = []
        for row in rows:
            report = dict(row)
            # JSON 문자열을 파이썬 객체로 변환
            report['drives'] = json.loads(report['drives_info'])
            report['pst_files'] = json.loads(report['pst_files'])
            report['mail_info'] = json.loads(report['mail_info'])
            report['active_email_accounts'] = json.loads(report.get('active_email_accounts', '[]'))
            del report['drives_info']

            # 사용자 이름 매핑 및 아카이브 날짜 적용
            display_name = self.get_display_name(report['computer_name'])
            archive_date = self.get_archive_date(report['computer_name'])

            if display_name:
                report['display_name'] = display_name
            else:
                report['display_name'] = report['user_name']

            report['last_archive_date'] = archive_date

            reports.append(report)

        return reports

    def get_pc_history(self, computer_name: str, days: int = 7) -> List[Dict]:
        """
        특정 PC의 히스토리 조회

        Args:
            computer_name: 컴퓨터 이름
            days: 조회할 일수

        Returns:
            리포트 히스토리 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT * FROM pc_reports
            WHERE computer_name = ?
            AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (computer_name, since_date))

        rows = cursor.fetchall()
        conn.close()

        history = []
        for row in rows:
            report = dict(row)
            report['drives'] = json.loads(report['drives_info'])
            report['pst_files'] = json.loads(report['pst_files'])
            report['mail_info'] = json.loads(report['mail_info'])
            report['active_email_accounts'] = json.loads(report.get('active_email_accounts', '[]'))
            del report['drives_info']
            history.append(report)

        return history

    def get_statistics(self) -> Dict:
        """
        전체 통계 조회

        Returns:
            통계 데이터
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 총 PC 수
        cursor.execute('''
            SELECT COUNT(DISTINCT computer_name) as total_pcs
            FROM pc_reports
        ''')
        total_pcs = cursor.fetchone()['total_pcs']

        # 오늘 리포트 수
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) as today_reports
            FROM pc_reports
            WHERE DATE(timestamp) = DATE(?)
        ''', (today,))
        today_reports = cursor.fetchone()['today_reports']

        # 최근 리포트 시간
        cursor.execute('''
            SELECT MAX(timestamp) as last_report_time
            FROM pc_reports
        ''')
        last_report = cursor.fetchone()['last_report_time']

        conn.close()

        return {
            'total_pcs': total_pcs,
            'today_reports': today_reports,
            'last_report_time': last_report
        }

    def get_alerts(self) -> List[Dict]:
        """
        경고 사항 조회 (스토리지 80% 이상, PST 파일 2GB 이상 등)

        Returns:
            경고 리스트
        """
        alerts = []
        latest_reports = self.get_latest_reports()

        for report in latest_reports:
            # 스토리지 경고
            for drive in report['drives']:
                if drive['used_percent'] >= 80:
                    alerts.append({
                        'type': 'storage',
                        'severity': 'high' if drive['used_percent'] >= 90 else 'medium',
                        'computer_name': report['computer_name'],
                        'message': f"{drive['drive']} 드라이브 사용률 {drive['used_percent']}% (여유 공간: {drive['free_gb']}GB)",
                        'timestamp': report['timestamp']
                    })

            # PST 파일 크기 경고
            if report['total_pst_size_gb'] >= 2:
                alerts.append({
                    'type': 'pst_size',
                    'severity': 'high' if report['total_pst_size_gb'] >= 5 else 'medium',
                    'computer_name': report['computer_name'],
                    'message': f"PST 파일 총 크기: {report['total_pst_size_gb']}GB",
                    'timestamp': report['timestamp']
                })

            # 오래된 리포트 경고 (24시간 이상)
            report_time = datetime.strptime(report['timestamp'], '%Y-%m-%d %H:%M:%S')
            hours_ago = (datetime.now() - report_time).total_seconds() / 3600

            if hours_ago >= 24:
                alerts.append({
                    'type': 'outdated',
                    'severity': 'low',
                    'computer_name': report['computer_name'],
                    'message': f"마지막 리포트: {int(hours_ago)}시간 전",
                    'timestamp': report['timestamp']
                })

            # 아카이브 날짜 경고 (3개월 이상)
            if report.get('last_archive_date'):
                try:
                    archive_date = datetime.strptime(report['last_archive_date'], '%Y-%m-%d')
                    days_since_archive = (datetime.now() - archive_date).days

                    if days_since_archive >= 90:  # 3개월 = 90일
                        alerts.append({
                            'type': 'archive_overdue',
                            'severity': 'high' if days_since_archive >= 180 else 'medium',  # 6개월 이상이면 high
                            'computer_name': report['computer_name'],
                            'message': f"아카이브 필요: {days_since_archive}일 전 ({report['last_archive_date']})",
                            'timestamp': report['timestamp']
                        })
                except:
                    pass

        # 심각도 순으로 정렬
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: severity_order[x['severity']])

        return alerts

    def cleanup_old_reports(self, days: int = 30):
        """
        오래된 리포트 삭제

        Args:
            days: 보관할 일수
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            DELETE FROM pc_reports
            WHERE timestamp < ?
        ''', (cutoff_date,))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted_count

    def get_display_name(self, computer_name: str) -> Optional[str]:
        """
        컴퓨터 이름으로 표시 이름 조회

        Args:
            computer_name: 컴퓨터 이름

        Returns:
            표시 이름 (없으면 None)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT display_name FROM user_mappings
            WHERE computer_name = ?
        ''', (computer_name,))

        row = cursor.fetchone()
        conn.close()

        return row['display_name'] if row else None

    def set_display_name(self, computer_name: str, windows_user: str, display_name: str) -> bool:
        """
        표시 이름 설정/업데이트

        Args:
            computer_name: 컴퓨터 이름
            windows_user: Windows 사용자 이름
            display_name: 표시할 이름

        Returns:
            성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO user_mappings (computer_name, windows_user, display_name, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(computer_name)
                DO UPDATE SET
                    display_name = excluded.display_name,
                    updated_at = excluded.updated_at
            ''', (computer_name, windows_user, display_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting display name: {e}")
            conn.close()
            return False

    def set_archive_date(self, computer_name: str, archive_date: str, windows_user: str = None, user_name: str = None) -> bool:
        """
        마지막 아카이브 날짜 설정/업데이트

        Args:
            computer_name: 컴퓨터 이름
            archive_date: 아카이브 날짜 (YYYY-MM-DD)
            windows_user: Windows 사용자 이름 (새 레코드 생성 시 필요)
            user_name: 표시 이름 (새 레코드 생성 시 필요)

        Returns:
            성공 여부
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Check if record exists
            cursor.execute('SELECT id FROM user_mappings WHERE computer_name = ?', (computer_name,))
            exists = cursor.fetchone()

            if exists:
                # Update existing record
                cursor.execute('''
                    UPDATE user_mappings
                    SET last_archive_date = ?, updated_at = ?
                    WHERE computer_name = ?
                ''', (archive_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), computer_name))
            else:
                # Insert new record - use provided values or defaults
                win_user = windows_user if windows_user else 'unknown'
                display = user_name if user_name else 'unknown'
                cursor.execute('''
                    INSERT INTO user_mappings (computer_name, windows_user, display_name, last_archive_date, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (computer_name, win_user, display, archive_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting archive date: {e}")
            conn.close()
            return False

    def get_archive_date(self, computer_name: str) -> Optional[str]:
        """
        마지막 아카이브 날짜 조회

        Args:
            computer_name: 컴퓨터 이름

        Returns:
            아카이브 날짜 (없으면 None)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT last_archive_date FROM user_mappings
            WHERE computer_name = ?
        ''', (computer_name,))

        row = cursor.fetchone()
        conn.close()

        return row['last_archive_date'] if row and row['last_archive_date'] else None

    def get_all_user_mappings(self) -> List[Dict]:
        """
        모든 사용자 이름 매핑 조회

        Returns:
            매핑 리스트
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user_mappings ORDER BY computer_name')
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
