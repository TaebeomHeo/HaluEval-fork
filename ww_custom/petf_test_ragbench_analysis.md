# petf_test_ragbench 리포지토리 분석 리포트

## 1. 프로젝트 개요 (Overview)

`petf_test_ragbench`는 **RAGBench 데이터셋(galileo-ai/ragbench)을 활용하여 LLM의 환각(Hallucination) 분류용 LoRA 어댑터를 학습하고 평가하는 경량 파이프라인**입니다.
베이스 모델(Qwen/Qwen3-1.7B) 하나에 여러 개의 서로 다른 LoRA 어댑터(직교 어댑터, Orthogonal Adapters)를 부착하여 환각 판별 성능을 다각도로 테스트하고 비교 분석(코사인 유사도 등)하는 연구/실험용 목적을 가집니다.

## 2. 주요 아키텍처 및 특징

### A. 사용 모델 및 데이터셋

- **Base Model:** `Qwen/Qwen3-1.7B` (빠르고 가벼운 1.7B 파라미터 모델 사용)
- **Dataset:** `galileo-ai/ragbench`
  - 사용 subset: `finqa`(금융), `tatqa`(표/텍스트), `pubmedqa`(의료), `hagrid`
  - HuggingFace에 등록된 train/validation/test 분할을 그대로 활용하며, 클래스 밸런싱(yes/no 비율 조정) 및 토큰 길이 필터링 등 2단계 전처리를 수행합니다.

### B. 직교 어댑터 (Orthogonal Adapters) 학습

이 프로젝트의 가장 큰 특징은 단일 모델을 학습시키는 것이 아니라, 설정 파일(`configs/train_ragbench.yaml`)에 정의된 다양한 하이퍼파라미터 차원(Dimensions)을 조합하여 **N개의 독립적인 어댑터를 순차적으로 학습**시킨다는 점입니다.
조합되는 4가지 축(D, R, M, P)은 다음과 같습니다.

1.  **D (Data):** 데이터 랜덤 샘플링 시드(Seed)
2.  **R (Rank & Alpha):** LoRA의 핵심 파라미터인 `r`과 `lora_alpha`의 조합 (예: [8, 8], [16, 32], [32, 64] 등)
3.  **M (Target Modules):** LoRA를 적용할 Attention 계층의 파라미터 조합 (예: q_proj, v_proj, o_proj, gate_proj 등)
4.  **P (Prompt):** 환각을 판별할 때 모델에게 지시하는 프롬프트 템플릿의 변형 패턴들

### C. 평가 및 코사인 유사도 연산 (Cosine Similarity)

- `run_eval_ex.py`: 학습된 N개의 어댑터를 각 subset의 test셋으로 평가하여 yes/no 정확도를 추출합니다.
- `run_cosine_similarity.py`: 여러 어댑터들이 **환각을 판별해 낸 결과(예측값)들의 패턴이 얼마나 유사한지 코사인 유사도를 계산**합니다. 이를 통해 각 어댑터(전문가 모델)들이 서로 얼마나 '독립적인(Orthogonal)' 판단을 내리는지 앙상블 관점에서 분석하게 됩니다.

## 3. 파일 및 디렉토리 구조

- `configs/`: 모델 학습 설정이 담긴 YAML 파일들 (`train_ragbench.yaml` 등)
- `pipeline/`: 실질적인 데이터 로딩(`data.py`), 전처리 및 모델 학습(`train_ex.py`), 평가(`eval.py`), 유사도 계산(`cosine_similarity.py`) 로직이 모듈화된 폴더.
- 진입점 스크립트:
  - `run_train_orthogonal.py`: 직교 어댑터 묶음 학습 실행
  - `run_eval_ex.py`: 학습된 어댑터 테스트 추론
  - `run_cosine_similarity.py`: 예측 결과의 유사도 분석
- `pyproject.toml` / `uv.lock`: 최신 Python 패키지 의존성 관리 도구인 `uv`를 사용하도록 세팅됨.

## 4. 시사점 및 HaluEval과의 연계 가능성

이전에 저희가 논의했던 **"특정 측면(Aspect)별 전문가 경량 모델 앙상블" 구조와 매우 깊게 맞닿아 있는 파이프라인**입니다.

### A. Rank와 Target Modules의 한계 (단순 파라미터 튜닝의 맹점)

이 프로젝트는 Rank크기(8 vs 32)나 모듈 타겟(q_proj vs v_proj) 설정을 다르게 주면서 여러 어댑터를 학습시킵니다.

- **Rank:** 값이 작으면 단순한 핵심 규칙만 빠르고 범용적으로 외우고, 값이 크면 미묘하고 지엽적인 정보까지 세밀하게 외웁니다.
- **Target Modules:** 모델의 뇌 구조에서 문맥 스캔(Attention) 부위를 위주로 학습할지, 논리적 추론(MLP) 부위를 위주로 학습할지를 결정합니다.

하지만 **"학습 파라미터를 요리조리 바꾼다고 해서 무조건 서로 독립적(Orthogonal)이고 똑똑한 앙상블이 되는가?"** 하면 **결코 아닙니다.**
똑같은 원본 RAGBench 데이터를 먹인다면, 어댑터들은 결국 가장 쉬운 지름길(Shortcut) 패턴을 공통적으로 학습하게 되어 **맞는 문제도 같이 맞고 틀리는 문제도 같이 틀리는 '복제 인간'**이 될 확률이 매우 높습니다. 이 파이프라인 시스템의 끝에 `run_cosine_similarity.py` (유사도 검증 스크립트)가 굳이 존재하는 이유도, "무지성으로 찍어낸 어댑터들이 진짜 서로 다르게 생각(상호보완적 앙상블)하는지"를 걸러내기 위함입니다.

### B. "D(Data)축을 Aspect별 데이터셋으로 치환한다"의 완벽한 의미

따라서 진정한 의미의 '전문가(직교성을 가진) 앙상블'을 구축하려면 파라미터 조작만으로는 부족합니다.

`petf_test_ragbench` 프레임워크의 기존의 안정적인 학습/평가/배포 뼈대를 그대로 가져오되, **설정 파일에서 어댑터를 생성할 때(D축) "수치 특화 에러셋", "어휘 특화 에러셋" 처럼 애초에 담당 과목이 완전히 다른 데이터를 먹이도록 치환**해야 합니다.
이렇게 하면 복잡한 시스템 구축 과정 없이, 기존 프레임워크의 반복 루프 로직에 데이터 슬롯만 갈아 끼우는 것으로 **"서로 바라보는 관점(Aspect)이 완벽히 직교하여 환상적인 시너지를 내는 전문가 모델 앙상블 평가 시스템"**을 초고속으로 런칭할 수 있습니다. 이미 vLLM을 통한 LoRA 멀티어댑터 동시 운용 테스트 가능성까지 염두에 두고 작성된 완성도 높은 프레임워크이므로 응용하기에 최적의 베이스라인입니다.
