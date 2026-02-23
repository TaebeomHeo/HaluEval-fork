# HaluEval 분석 및 활용 방안

## 1. 개요

HaluEval(Hallucination Evaluation Benchmark)은 거대 언어 모델(LLM)이 문장 속에 섞인 '환각(Hallucination)'을 얼마나 잘 찾아내고 구별하는지 성능을 평가하기 위한 벤치마크 도구입니다. 이 프로젝트는 모델이 주어진 문맥에서 사실과 다른 거짓 정보를 식별하는 능력을 측정하고, 어떤 유형의 환각에 취약한지 분석할 수 있도록 설계되었습니다.

## 2. 데이터 생성 프로세스 (Generation)

HaluEval은 방대한 양의 환각 평가 데이터를 만들기 위해 ChatGPT를 활용한 자동화된 파이프라인을 구축했습니다.

- **시드 데이터 준비:** 기존의 검증된 데이터셋(QA의 경우 HotpotQA, 요약은 CNN/DailyMail 등)을 활용하여 기준이 되는 지식(Knowledge), 질문(Question), 정답(Right Answer)을 준비합니다.
- **환각 강제 주입:** ChatGPT에게 명시적인 지시문(`qa_one-turn_instruction.txt` 등)을 주어 사실과 다르지만 그럴싸한 4가지 유형의 환각 오답을 생성하게 합니다.
  1.  **의도 파악 오류 (Misunderstanding):** 질문의 문맥을 잘못 이해한 오답.
  2.  **사실 관계 모순 (Factual Contradiction):** 주어진 지식과 정면으로 배치되는 오답.
  3.  **수준 부적합 (Specificity Error):** 정답이긴 하지만 요구하는 구체성이 맞지 않는 답변.
  4.  **추론 오류 (Reasoning Error):** 주어진 지식으로 유추할 수 없는 잘못된 결론.

## 3. 데이터 필터링 및 검증 (Filtering)

생성된 데이터가 정말로 환각이 섞인 오답인지 보장하기 위해, 전적으로 ChatGPT에게 의존하면서도 질을 높이기 위한 필터링 과정을 거칩니다.

- **다중 생성:** 한 질문당 서로 다른 2개의 환각 후보(One-pass 및 Conversational 방식)를 생성합니다.
- **ChatGPT 기반 선별:** ChatGPT를 "판사(Judge)"로 투입하여(`filtering.py`), 2개의 후보 중 질문에 가장 잘 맞고 논리적으로 들리면서도 실제 지식과는 어긋나는 가장 속기 쉬운(Plausible) 환각 답변 1개만을 최종 선별합니다.

## 4. 평가 방식 (Evaluation)

평가는 모델의 "환각 탐지(Recognition)" 능력을 측정하는 이진 분류(Binary Classification) 방식으로 진행됩니다.

- 모델에게 `qa_evaluation_instruction.txt`와 같은 지시문을 주어 "답변에 환각 정보가 포함되어 있는지 'Yes' 또는 'No'로 대답하라"고 지시합니다.
- 데이터셋에서 50%는 실제 정답, 50%는 환각 정답을 섞어 제시합니다.
- 모델이 환각 답변에 "Yes", 정상 답변에 "No"를 정확히 출력하는지 비교하여 Accuracy(정확도)를 계산합니다.

## 5. 분석 방식 (Analysis)

모델이 제대로 찾아내지 못하고 속아 넘어간 환각 데이터(`failed` 샘플)들을 모아 분석합니다.

- LDA(Latent Dirichlet Allocation) 토픽 모델링을 사용하여, 평가 대상 모델이 특정 지식 주제나 환각 유형 중 어디에 특히 취약한지 심층적으로 파악합니다.

## 6. 한계점 (Limitations)

- **자동 생성 의존:** 데이터 생성을 전적으로 ChatGPT에 일임하기 때문에, 생성된 환각 후보 자체가 원활하지 않거나 완벽한 오류 필터링이 어려울 수 있습니다.
- **시드 데이터 종속성:** 파생되는 환각 데이터의 품질은 시드 데이터의 정확성에 크게 의존합니다.
- **보완책:** 이를 보완하기 위해 5,000개의 일반 사용자 질의응답(Alpaca 베이스) 데이터는 사람이 직접 개입(Human-annotated)하여 검증하고 라벨링하는 방식을 혼용하여 신뢰도를 높였습니다.

## 7. Ground Data (Seed Data)의 의미

HaluEval에서 'Ground Data' (또는 Seed Data)는 모델의 환각 생성 및 평가를 위한 기준점이 되는 **'진실만이 담긴 원본 데이터'**입니다.

- **출처:** HotpotQA (질의응답), OpenDialKG (대화), CNN/DailyMail (요약) 등 학계에서 이미 사실관계가 검증되고 널리 쓰이는 고품질 데이터셋을 그대로 가져옵니다.
- **역할:** ChatGPT가 환각(거짓)을 지어내기 위해서는 먼저 '진짜 사실'이 무엇인지 알아야 합니다. Ground Data는 ChatGPT에게 "이것이 변하지 않는 진실(Knowledge)이고 정답(Right Answer)이야. 자, 이제 이것과 _다르게_ 거짓말을 해봐"라고 기준을 제시하는 역할을 합니다.
- **평가 시:** 최종 테스트에서 50%의 확률로 모델에게 던져지는 "환각이 없는 정상적인 답변"이 바로 이 Ground Data의 정답(Right Answer)입니다.

## 8. 지식 테스트(Knowledge Test)와의 차별점: RAG의 필요성 여부

평가 대상인 LLM이 Ground Data를 학습하지 않았을 수 있다는 중요한 지적이 있습니다. LLM이 해당 사실을 모른다면 환각을 탐지하는 것이 아니라, 단순히 지식의 유무(Knowledge Test)를 묻는 것이 아니냐는 의문입니다.

HaluEval은 이 맹점을 **프롬프트 내 지식 주입(In-context Knowledge Provision)**을 통해 해결합니다.

- 평가 스크립트(`evaluate.py`)와 지시문(`qa_evaluation_instruction.txt`)을 보면, 모델에게 질문과 답변만 덜렁 주지 않습니다.
- **"#Knowledge#: [실제 위키백과 등 본문]"** 이라는 형태로 평가를 위한 완벽한 지식(Ground Truth)을 프롬프트 안에 함께 제공합니다.
- 즉, 모델은 자신의 내부 지식(Parametric Memory)에 의존하여 진실 게임을 하는 것이 아니라, **방금 주어진 참고 지식(Knowledge)을 읽고, 그 지식에 비추어 볼 때 이 답변이 사실과 일치하는지(No Hallucination) 아니면 지식과 모순되거나 지식 범위를 벗어난 허튼소리(Yes Hallucination)를 하는지 판별**하는 '독해 및 논리적 대조 능력'을 평가받게 됩니다.
- 그러므로 별도의 RAG(Retrieval-Augmented Generation) 파이프라인이나 사전 학습 없이도, HaluEval 평가 프롬프트 자체가 이미 미니 RAG의 "검색된 문서를 주입하는 단계"와 똑같은 역할을 수행하고 있습니다.
