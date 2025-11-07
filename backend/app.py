from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import csv
import io
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from agent import assign_department

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)


def get_supabase_client() -> Client:
    """
    .env 파일에서 Supabase 설정을 읽어 클라이언트 생성
    서버 사이드에서는 service_role key를 사용하여 RLS를 우회합니다.
    
    Returns:
        Client: Supabase 클라이언트 인스턴스
    
    Raises:
        ValueError: 필수 환경 변수가 설정되지 않은 경우
    """
    supabase_url = os.getenv("SUPABASE_URL")
    # service_role key를 우선 사용, 없으면 SUPABASE_KEY 사용
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        raise ValueError(
            "SUPABASE_URL 환경변수가 설정되지 않았습니다. "
            ".env 파일에 SUPABASE_URL을 추가해주세요."
        )
    
    if not supabase_key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY 또는 SUPABASE_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 SUPABASE_SERVICE_ROLE_KEY를 추가해주세요. "
            "(서버 사이드에서는 service_role key를 사용해야 RLS 정책을 우회할 수 있습니다.)"
        )
    
    # 사용 중인 키 타입 확인 (디버깅용)
    key_type = "SERVICE_ROLE" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "ANON"
    print(f"[DEBUG] Supabase 클라이언트 초기화: URL={supabase_url[:30]}..., Key Type={key_type}")
    
    return create_client(supabase_url, supabase_key)


# Supabase 클라이언트 초기화
supabase: Client = get_supabase_client()

@app.route('/', methods=['GET'])
def health_check():
    """
    헬스체크 엔드포인트
    """
    return jsonify({
        "status": "success",
        "message": "ChannelTalk Hackaton API Server",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "csv_upload": "/csv/upload (POST)",
            "department_all": "/department/all (GET)",
            "msg_all": "/msg/all?d_id={id} (GET)"
        }
    }), 200


@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    채널톡 webhook API
    채널톡 webhook 형식의 JSON을 받아서 처리
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "요청 본문이 필요합니다."
            }), 400
        
        # 채널톡 webhook 구조에서 메시지 내용 추출
        # entity.plainText 우선, 없으면 entity.blocks[0].value 사용
        msg_content = None
        
        # 디버깅: 받은 데이터 구조 확인
        print(f"[DEBUG] Webhook received - event: {data.get('event')}, type: {data.get('type')}")
        
        if 'entity' in data:
            entity = data['entity']
            # plainText 우선 확인
            if 'plainText' in entity and entity['plainText']:
                msg_content = entity['plainText']
                print(f"[DEBUG] Extracted message from plainText: {msg_content[:50]}...")
            # blocks에서 추출
            elif 'blocks' in entity and len(entity['blocks']) > 0:
                if 'value' in entity['blocks'][0]:
                    msg_content = entity['blocks'][0]['value']
                    print(f"[DEBUG] Extracted message from blocks[0].value: {msg_content[:50]}...")
        
        # 기존 형식도 지원 ({"msg": "..."})
        if not msg_content and 'msg' in data:
            msg_content = data['msg']
            print(f"[DEBUG] Extracted message from msg field: {msg_content[:50]}...")
        
        if not msg_content:
            print(f"[DEBUG] Failed to extract message. Data keys: {list(data.keys())}")
            if 'entity' in data:
                print(f"[DEBUG] Entity keys: {list(data['entity'].keys())}")
            return jsonify({
                "status": "error",
                "message": "메시지 내용을 찾을 수 없습니다. entity.plainText 또는 entity.blocks[0].value가 필요합니다."
            }), 400
        
        # 1) msg를 DB에 저장 (table: message, field: msg_id, content, timestamp)
        # msg_id는 int8이므로 숫자로 생성 (마이크로초 타임스탬프 사용)
        msg_id = int(time.time() * 1000000)  # 마이크로초 타임스탬프 사용
        # 현재 시간을 ISO 8601 형식으로 저장 (UTC)
        current_timestamp = datetime.now(timezone.utc).isoformat()
        
        print(f"[DEBUG] 메시지 저장 시도 - msg_id: {msg_id}, content 길이: {len(msg_content)}")
        
        # 중복 ID 발생 시 재시도 로직
        max_retries = 3
        msg_id_saved = None
        
        for attempt in range(max_retries):
            try:
                print(f"[DEBUG] DB 저장 시도 {attempt + 1}/{max_retries} - msg_id: {msg_id}")
                response = supabase.table('message').insert({
                    'msg_id': msg_id,
                    'content': msg_content,
                    'timestamp': current_timestamp
                }).execute()
                msg_id_saved = msg_id
                print(f"[DEBUG] 메시지 저장 성공 - msg_id: {msg_id}")
                break  # 성공 시 루프 종료
                
            except Exception as e:
                error_str = str(e)
                print(f"[ERROR] DB 저장 실패 (시도 {attempt + 1}/{max_retries}): {error_str}")
                
                # 중복 키 에러인 경우에만 재시도
                if ('duplicate key' in error_str.lower() or 
                    '23505' in error_str or
                    'unique constraint' in error_str.lower()):
                    
                    if attempt < max_retries - 1:
                        # 실패했을 때만 max msg_id 조회
                        try:
                            max_result = supabase.table('message')\
                                .select('msg_id')\
                                .order('msg_id', desc=True)\
                                .limit(1)\
                                .execute()
                            
                            # 다음 ID 계산 (max + 1)
                            if max_result.data:
                                msg_id = max_result.data[0]['msg_id'] + 1
                            else:
                                msg_id = 1
                            
                            print(f"[WARN] 중복 ID 발생, 재시도 {attempt + 1}/{max_retries}, 새 msg_id: {msg_id}")
                        except Exception as query_error:
                            # max 조회 실패 시 타임스탬프 기반으로 재생성
                            msg_id = int(time.time() * 1000000) + attempt + 1
                            print(f"[WARN] max 조회 실패, 타임스탬프 기반 재생성: {msg_id}")
                        
                        continue  # 재시도
                    else:
                        # 최대 재시도 횟수 초과
                        return jsonify({
                            "status": "error",
                            "message": f"메시지 저장 실패: 중복 ID가 계속 발생합니다. (재시도 {max_retries}회 실패)"
                        }), 500
                else:
                    # 중복 키가 아닌 다른 에러는 즉시 반환
                    return jsonify({
                        "status": "error",
                        "message": f"DB 저장 실패: {str(e)}"
                    }), 500
        
        if not msg_id_saved:
            return jsonify({
                "status": "error",
                "message": "메시지 저장 실패"
            }), 500
        
        # 메시지 저장 완료 후 부서 배정 실행
        print(f"[DEBUG] 메시지 저장 완료 - msg_id: {msg_id_saved}")
        print(f"[DEBUG] 부서 배정 시작 - msg_id: {msg_id_saved}")
        
        try:
            assign_result = assign_department(str(msg_id_saved), top_k=5)
            if assign_result == 1:
                print(f"[DEBUG] 부서 배정 성공 - msg_id: {msg_id_saved}")
            else:
                print(f"[DEBUG] 부서 배정 실패 또는 일반 채팅으로 처리됨 - msg_id: {msg_id_saved}")
        except Exception as e:
            import traceback
            print(f"[ERROR] 부서 배정 중 오류 발생: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            # 부서 배정 실패해도 메시지는 저장되었으므로 성공으로 반환
        
        return jsonify({
            "status": "success",
            "message": "처리 완료",
            "msg_id": msg_id_saved
        }), 200
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Webhook handler exception: {str(e)}")
        print(f"[ERROR] Traceback: {error_trace}")
        return jsonify({
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }), 500


@app.route('/csv/upload', methods=['POST'])
def upload_csv():
    """
    CSV 파일 업로드 API
    dept_id, dept_name, dept_desc 컬럼을 파싱하여 DB에 저장
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "파일이 없습니다."
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "파일명이 없습니다."
            }), 400
        
        # CSV 파일 읽기
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        departments = []
        for row in csv_reader:
            # dept_name과 dept_desc가 필수, dept_id는 선택적
            if 'dept_name' in row and 'dept_desc' in row:
                dept_name = row['dept_name'].strip()
                dept_desc = row['dept_desc'].strip()
                
                if dept_name:  # 빈 값 제외
                    dept_data = {
                        'dept_name': dept_name,
                        'dept_desc': dept_desc
                    }
                    
                    # dept_id가 있으면 포함 (없으면 DB에서 자동 생성)
                    if 'dept_id' in row and row['dept_id'].strip():
                        try:
                            dept_data['dept_id'] = int(row['dept_id'].strip())
                        except ValueError:
                            # dept_id가 숫자가 아니면 무시
                            pass
                    
                    departments.append(dept_data)
        
        if not departments:
            return jsonify({
                "status": "error",
                "message": "유효한 데이터가 없습니다. CSV 파일에 dept_name과 dept_desc 컬럼이 필요합니다."
            }), 400
        
        # 2) 파싱한 결과를 DB에 저장 (table: department, field: dept_id, dept_name, dept_desc)
        try:
            for dept in departments:
                supabase.table('department').insert(dept).execute()
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in upload_csv: {str(e)}")
            print(f"Traceback: {error_trace}")
            
            # RLS 정책 위반 오류인 경우 명확한 메시지 제공
            error_str = str(e)
            if 'row-level security policy' in error_str.lower() or '42501' in error_str:
                return jsonify({
                    "status": "error",
                    "message": "RLS 정책 위반: 서버 사이드에서는 SUPABASE_SERVICE_ROLE_KEY를 사용해야 합니다. .env 파일에 SUPABASE_SERVICE_ROLE_KEY를 추가해주세요."
                }), 500
            
            return jsonify({
                "status": "error",
                "message": f"DB 저장 실패: {str(e)}"
            }), 500
        
        return jsonify({
            "status": "success",
            "message": f"{len(departments)}개의 부서가 저장되었습니다.",
            "count": len(departments)
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in upload_csv: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }), 500


@app.route('/department/all', methods=['GET'])
def getAllDepartmentLists():
    """
    department 테이블의 모든 레코드에서 dept_id와 name 반환
    """
    try:
        response = supabase.table('department').select('dept_id, dept_name').execute()
        
        departments = []
        for row in response.data:
            departments.append({
                'department_id': row.get('dept_id'),
                'name': row.get('dept_name')
            })
        
        return jsonify({
            "status": "success",
            "data": departments
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in getAllDepartmentLists: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }), 500


@app.route('/msg/all', methods=['GET'])
def get_messages_by_department():
    """
    assigned_message 테이블에서 메시지 조회
    - d_id가 있으면: 해당 부서의 메시지만 반환
    - d_id가 없으면: assigned_message 전체 반환
    query parameter: d_id (선택사항)
    """
    try:
        d_id = request.args.get('d_id')
        
        # d_id가 없으면 assigned_message 전체 조회
        if not d_id:
            assigned_response = supabase.table('assigned_message').select('msg_id').execute()
        else:
            # assigned_message 테이블에서 d_id에 맞는 msg_id 조회
            assigned_response = supabase.table('assigned_message').select('msg_id').eq('dept_id', d_id).execute()
        
        if not assigned_response.data:
            return jsonify({
                "status": "success",
                "data": []
            }), 200
        
        # msg_id 리스트 추출
        msg_ids = [row['msg_id'] for row in assigned_response.data]
        
        # message 테이블에서 해당 msg_id들의 content와 timestamp 조회
        msg_response = supabase.table('message').select('content, timestamp').in_('msg_id', msg_ids).execute()
        
        # content와 timestamp를 함께 반환
        messages = [
            {
                'content': row['content'],
                'timestamp': row.get('timestamp', None)
            }
            for row in msg_response.data
        ]
        
        return jsonify({
            "status": "success",
            "data": messages
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"서버 오류: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

