"""
Ground Truth 데이터를 사람이 보기 좋은 형식으로 엑셀 파일로 변환하는 스크립트

출력 파일:
- 01_hotpotqa_seed_1000.xlsx: HotpotQA 시드 데이터 1,000개
- 02_opendialkg_seed_1000.xlsx: OpenDialKG 시드 데이터 1,000개
- 03_cnndm_seed_1000.xlsx: CNN/DailyMail 시드 데이터 1,000개
- 04_qa_benchmark_1000.xlsx: QA 벤치마크 (정답 + 환각) 1,000개
- 05_dialogue_benchmark_1000.xlsx: Dialogue 벤치마크 (정답 + 환각) 1,000개
- 06_summarization_benchmark_1000.xlsx: Summarization 벤치마크 (정답 + 환각) 1,000개
- 07_human_annotated_general_ALL.xlsx: Human-annotated 일반 데이터 전체
"""
import json
import csv
import pandas as pd
from pathlib import Path

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
GROUND_TRUTH_DIR = Path(__file__).parent / "ground_truth_data"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path(__file__).parent / "excel_output"
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLE_SIZE = 1000


def load_hotpotqa(filepath, n=SAMPLE_SIZE):
    """HotpotQA 데이터 로드 및 변환"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    for i, item in enumerate(data[:n]):
        # supporting_facts에서 관련 지식 추출
        supporting_facts = item.get('supporting_facts', [])
        context = item.get('context', [])

        # 관련 문단만 추출
        knowledge_parts = []
        for fact in supporting_facts:
            title = fact[0]
            sent_idx = fact[1]
            for ctx in context:
                if ctx[0] == title and sent_idx < len(ctx[1]):
                    knowledge_parts.append(ctx[1][sent_idx])

        knowledge = ' '.join(knowledge_parts)

        records.append({
            '번호': i + 1,
            '난이도': item.get('level', ''),
            '질문': item.get('question', ''),
            '정답': item.get('answer', ''),
            '관련_지식': knowledge,
        })

    return pd.DataFrame(records)


def load_opendialkg(filepath, n=SAMPLE_SIZE):
    """OpenDialKG 데이터 로드 및 변환"""
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= n:
                break

            try:
                messages = eval(row['Messages'])
            except:
                continue

            # 대화 내역과 지식 추출
            dialogue_parts = []
            knowledge_parts = []

            for msg in messages:
                if 'message' in msg:
                    sender = '[User]' if msg['sender'] == 'user' else '[Assistant]'
                    dialogue_parts.append(f"{sender}: {msg['message']}")

                if 'metadata' in msg and 'path' in msg['metadata']:
                    path_info = msg['metadata']['path']
                    if len(path_info) >= 3:
                        knowledge_parts.append(path_info[2])

            dialogue = '\n'.join(dialogue_parts)
            knowledge = ' | '.join(set(knowledge_parts))  # 중복 제거

            records.append({
                '번호': i + 1,
                '대화_내역': dialogue,
                '관련_지식': knowledge,
            })

    return pd.DataFrame(records)


def load_cnndm(filepath, n=SAMPLE_SIZE):
    """CNN/DailyMail 데이터 로드 및 변환"""
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n:
                break

            try:
                item = json.loads(line.strip())
            except:
                continue

            document = item.get('document', '')
            summary = item.get('summary', '')

            # 문서가 너무 길면 앞부분만
            if len(document) > 3000:
                document = document[:3000] + '... [truncated]'

            records.append({
                '번호': i + 1,
                '원문_문서': document,
                '정답_요약': summary
            })

    return pd.DataFrame(records)


def load_benchmark_data(filepath, task_type, n=SAMPLE_SIZE):
    """최종 벤치마크 데이터 로드 (정답 + 환각 답변 포함)"""
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n:
                break

            try:
                item = json.loads(line.strip())
            except:
                continue

            if task_type == 'qa':
                records.append({
                    '번호': i + 1,
                    '지식': item.get('knowledge', ''),
                    '질문': item.get('question', ''),
                    '정답': item.get('right_answer', ''),
                    '환각_답변': item.get('hallucinated_answer', ''),
                })
            elif task_type == 'dialogue':
                records.append({
                    '번호': i + 1,
                    '지식': item.get('knowledge', ''),
                    '대화_내역': item.get('dialogue_history', ''),
                    '정답_응답': item.get('right_response', ''),
                    '환각_응답': item.get('hallucinated_response', ''),
                })
            elif task_type == 'summarization':
                document = item.get('document', '')
                if len(document) > 3000:
                    document = document[:3000] + '... [truncated]'

                records.append({
                    '번호': i + 1,
                    '원문_문서': document,
                    '정답_요약': item.get('right_summary', ''),
                    '환각_요약': item.get('hallucinated_summary', ''),
                })

    return pd.DataFrame(records)


def load_general_data(filepath):
    """Human-annotated 일반 데이터 로드 (전체)"""
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                item = json.loads(line.strip())
            except:
                continue

            hallucination_spans = item.get('hallucination_spans', [])
            spans_str = '\n'.join(hallucination_spans) if hallucination_spans else ''

            records.append({
                '번호': i + 1,
                'ID': item.get('ID', ''),
                '사용자_쿼리': item.get('user_query', ''),
                'ChatGPT_응답': item.get('chatgpt_response', ''),
                '환각_여부': item.get('hallucination', ''),
                '환각_구간': spans_str,
            })

    return pd.DataFrame(records)


def main():
    print("=" * 60)
    print("Ground Truth 데이터 엑셀 변환 시작")
    print("=" * 60)

    # 1. HotpotQA (QA 시드 데이터)
    hotpot_path = GROUND_TRUTH_DIR / "hotpot_train_v1.1.json"
    if hotpot_path.exists():
        print(f"\n[1/7] HotpotQA 로드 중... ({SAMPLE_SIZE}개)")
        try:
            df_hotpot = load_hotpotqa(hotpot_path)
            output_path = OUTPUT_DIR / "01_hotpotqa_seed_1000.xlsx"
            df_hotpot.to_excel(output_path, index=False, engine='openpyxl')
            print(f"  → 저장 완료: {output_path}")
        except Exception as e:
            print(f"  → 오류 발생 (파일 손상 가능): {e}")
            print(f"  → HotpotQA를 건너뜁니다. QA 벤치마크 데이터를 대신 사용하세요.")
    else:
        print(f"\n[1/7] HotpotQA 파일 없음: {hotpot_path}")

    # 2. OpenDialKG (Dialogue 시드 데이터)
    dialkg_path = GROUND_TRUTH_DIR / "opendialkg.csv"
    if dialkg_path.exists():
        print(f"\n[2/7] OpenDialKG 로드 중... ({SAMPLE_SIZE}개)")
        df_dialkg = load_opendialkg(dialkg_path)
        output_path = OUTPUT_DIR / "02_opendialkg_seed_1000.xlsx"
        df_dialkg.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path}")
    else:
        print(f"\n[2/7] OpenDialKG 파일 없음: {dialkg_path}")

    # 3. CNN/DailyMail (Summarization 시드 데이터)
    cnndm_path = BASE_DIR / "generation" / "cnndm.json"
    if cnndm_path.exists():
        print(f"\n[3/7] CNN/DailyMail 로드 중... ({SAMPLE_SIZE}개)")
        df_cnndm = load_cnndm(cnndm_path)
        output_path = OUTPUT_DIR / "03_cnndm_seed_1000.xlsx"
        df_cnndm.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path}")
    else:
        print(f"\n[3/7] CNN/DailyMail 파일 없음: {cnndm_path}")

    # 4. QA 벤치마크 데이터 (정답 + 환각)
    qa_path = DATA_DIR / "qa_data.json"
    if qa_path.exists():
        print(f"\n[4/7] QA 벤치마크 데이터 로드 중... ({SAMPLE_SIZE}개)")
        df_qa = load_benchmark_data(qa_path, 'qa')
        output_path = OUTPUT_DIR / "04_qa_benchmark_1000.xlsx"
        df_qa.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path}")

    # 5. Dialogue 벤치마크 데이터 (정답 + 환각)
    dialogue_path = DATA_DIR / "dialogue_data.json"
    if dialogue_path.exists():
        print(f"\n[5/7] Dialogue 벤치마크 데이터 로드 중... ({SAMPLE_SIZE}개)")
        df_dialogue = load_benchmark_data(dialogue_path, 'dialogue')
        output_path = OUTPUT_DIR / "05_dialogue_benchmark_1000.xlsx"
        df_dialogue.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path}")

    # 6. Summarization 벤치마크 데이터 (정답 + 환각)
    summ_path = DATA_DIR / "summarization_data.json"
    if summ_path.exists():
        print(f"\n[6/7] Summarization 벤치마크 데이터 로드 중... ({SAMPLE_SIZE}개)")
        df_summ = load_benchmark_data(summ_path, 'summarization')
        output_path = OUTPUT_DIR / "06_summarization_benchmark_1000.xlsx"
        df_summ.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path}")

    # 7. Human-annotated 일반 데이터 (별도 파일)
    general_path = DATA_DIR / "general_data.json"
    if general_path.exists():
        print(f"\n[7/7] Human-annotated 일반 데이터 로드 중... (전체)")
        df_general = load_general_data(general_path)
        output_path = OUTPUT_DIR / "07_human_annotated_general_ALL.xlsx"
        df_general.to_excel(output_path, index=False, engine='openpyxl')
        print(f"  → 저장 완료: {output_path} ({len(df_general)}개)")

    print("\n" + "=" * 60)
    print("변환 완료!")
    print(f"출력 폴더: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
