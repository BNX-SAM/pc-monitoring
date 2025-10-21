# -*- coding: utf-8 -*-
"""
PC 모니터링 서버
Flask를 사용한 웹 서버 및 API
"""

from flask import Flask, request, jsonify, render_template
from database import Database
from datetime import datetime
import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 한글 지원
db = Database()

# ==================== 웹 페이지 라우트 ====================

@app.route('/')
def index():
    """대시보드 메인 페이지"""
    return render_template('dashboard.html')

# ==================== API 라우트 ====================

@app.route('/api/report', methods=['POST'])
def receive_report():
    """
    클라이언트로부터 PC 정보 수신

    POST /api/report
    Body: JSON 형태의 PC 정보
    """
    try:
        report_data = request.get_json()

        if not report_data:
            return jsonify({
                'status': 'error',
                'message': '데이터가 없습니다.'
            }), 400

        # 필수 필드 검증
        required_fields = ['computer_name', 'user_name', 'timestamp']
        for field in required_fields:
            if field not in report_data:
                return jsonify({
                    'status': 'error',
                    'message': f'필수 필드가 누락되었습니다: {field}'
                }), 400

        # 데이터베이스에 저장
        report_id = db.save_report(report_data)

        # 아카이브 날짜가 있으면 자동으로 저장
        if report_data.get('last_archive_date'):
            # Extract date only (YYYY-MM-DD) from timestamp format
            archive_date = report_data['last_archive_date']
            if ' ' in archive_date:
                archive_date = archive_date.split(' ')[0]

            db.set_archive_date(
                report_data['computer_name'],
                archive_date,
                report_data.get('windows_user'),
                report_data.get('user_name')
            )
            print(f"  아카이브 날짜 자동 저장: {archive_date}")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"리포트 수신: {report_data['computer_name']} "
              f"(사용자: {report_data['user_name']}) - ID: {report_id}")

        return jsonify({
            'status': 'success',
            'message': '리포트가 성공적으로 저장되었습니다.',
            'report_id': report_id
        }), 200

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/reports/latest', methods=['GET'])
def get_latest_reports():
    """
    각 PC의 최신 리포트 조회

    GET /api/reports/latest
    """
    try:
        reports = db.get_latest_reports()
        return jsonify({
            'status': 'success',
            'data': reports,
            'count': len(reports)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/reports/history/<computer_name>', methods=['GET'])
def get_pc_history(computer_name):
    """
    특정 PC의 히스토리 조회

    GET /api/reports/history/<computer_name>?days=7
    """
    try:
        days = request.args.get('days', default=7, type=int)
        history = db.get_pc_history(computer_name, days)

        return jsonify({
            'status': 'success',
            'data': history,
            'count': len(history)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    전체 통계 조회

    GET /api/statistics
    """
    try:
        stats = db.get_statistics()
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    경고 사항 조회

    GET /api/alerts
    """
    try:
        alerts = db.get_alerts()
        return jsonify({
            'status': 'success',
            'data': alerts,
            'count': len(alerts)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_data():
    """
    오래된 데이터 정리

    POST /api/cleanup?days=30
    """
    try:
        days = request.args.get('days', default=30, type=int)
        deleted_count = db.cleanup_old_reports(days)

        return jsonify({
            'status': 'success',
            'message': f'{deleted_count}개의 오래된 리포트를 삭제했습니다.',
            'deleted_count': deleted_count
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/user-mappings', methods=['GET'])
def get_user_mappings():
    """
    모든 사용자 이름 매핑 조회

    GET /api/user-mappings
    """
    try:
        mappings = db.get_all_user_mappings()
        return jsonify({
            'status': 'success',
            'data': mappings,
            'count': len(mappings)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/user-mappings/<computer_name>', methods=['PUT'])
def update_user_mapping(computer_name):
    """
    사용자 이름 매핑 업데이트

    PUT /api/user-mappings/<computer_name>
    Body: {"windows_user": "...", "display_name": "..."}
    """
    try:
        data = request.get_json()

        if not data or 'display_name' not in data:
            return jsonify({
                'status': 'error',
                'message': 'display_name이 필요합니다.'
            }), 400

        windows_user = data.get('windows_user', '')
        display_name = data['display_name']

        success = db.set_display_name(computer_name, windows_user, display_name)

        if success:
            return jsonify({
                'status': 'success',
                'message': '사용자 이름이 업데이트되었습니다.'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '업데이트 실패'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/archive-date/<computer_name>', methods=['PUT'])
def update_archive_date(computer_name):
    """
    아카이브 날짜 업데이트

    PUT /api/archive-date/<computer_name>
    Body: {"archive_date": "YYYY-MM-DD"}
    """
    try:
        data = request.get_json()

        if not data or 'archive_date' not in data:
            return jsonify({
                'status': 'error',
                'message': 'archive_date가 필요합니다.'
            }), 400

        archive_date = data['archive_date']

        # 날짜 형식 검증
        try:
            datetime.strptime(archive_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': '날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)'
            }), 400

        success = db.set_archive_date(computer_name, archive_date)

        if success:
            return jsonify({
                'status': 'success',
                'message': '아카이브 날짜가 업데이트되었습니다.'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '업데이트 실패'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'서버 오류: {str(e)}'
        }), 500

# ==================== 메인 실행 ====================

if __name__ == '__main__':
    import socket

    # Get local IP address
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unable to get IP"

    local_ip = get_local_ip()

    print("=" * 60)
    print("PC 모니터링 서버 시작")
    print("=" * 60)
    print("📊 대시보드:")
    print(f"   - Local:   http://localhost:5000")
    print(f"   - Network: http://{local_ip}:5000")
    print()
    print("🔌 API 엔드포인트:")
    print("   - POST   /api/report                : 리포트 수신")
    print("   - GET    /api/reports/latest        : 최신 리포트 조회")
    print("   - GET    /api/reports/history/<pc>  : PC 히스토리 조회")
    print("   - GET    /api/statistics            : 통계 조회")
    print("   - GET    /api/alerts                : 경고 조회")
    print("   - GET    /api/user-mappings         : 사용자 이름 매핑 조회")
    print("   - PUT    /api/user-mappings/<pc>    : 사용자 이름 변경")
    print("   - PUT    /api/archive-date/<pc>     : 아카이브 날짜 변경")
    print("   - POST   /api/cleanup               : 데이터 정리")
    print("=" * 60)
    print()

    # 서버 실행
    # debug=True: 개발 모드 (코드 변경 시 자동 재시작)
    # host='0.0.0.0': 외부 접속 허용 (같은 네트워크의 다른 PC에서 접속 가능)
    app.run(debug=True, host='0.0.0.0', port=5000)
