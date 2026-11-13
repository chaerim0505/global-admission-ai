# evals — 품질 측정

| 파일 | 내용 |
| --- | --- |
| [`EVAL_DESIGN.md`](EVAL_DESIGN.md) | evals 설계서: 지표(AC에서 도출), 채점기, 데이터셋 구성, 게이트, 베이스라인 |
| [`evalset.jsonl`](evalset.jsonl) | 평가 데이터셋 (25건) |
| [`judge_prompt.md`](judge_prompt.md) / [`judge_labels.jsonl`](judge_labels.jsonl) | LLM-as-a-Judge 채점 기준 / 사람 라벨 |
| [`run_evals.py`](run_evals.py) | 러너 |
| [`results/`](results/) | 실행마다 `<YYYY-MM-DDTHHMM>.json`, 이력 `history.csv` |
| [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md) / [`collect_failures.py`](collect_failures.py) | 오류 분석 / 실패 원문 수집 |

```bash
PYTHONPATH=src python evals/run_evals.py                                   # offline (모델 호출 없음)
PYTHONPATH=src python evals/run_evals.py --live --judge --repeat 3 --note "변경 내역"
python evals/collect_failures.py                                           # 실패 원문 → ERROR_ANALYSIS.md
```
