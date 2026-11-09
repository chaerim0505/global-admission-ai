from admission.parser import parse_query
from admission.validation import validate_request

text = (
    "미얀마에서 학사를 졸업했고 GPA는 3.4/4.0이에요. "
    "아일랜드나 네덜란드에서 석사를 하고 싶어요. "
    "관심 분야는 AI이고 학비는 연간 2만 유로 이하를 원해요. "
    "장학금이 필요해요."
)

print("Parsing...", flush=True)
context = parse_query(text)
print(context.model_dump_json(indent=2))
print("Input errors:", validate_request(context))