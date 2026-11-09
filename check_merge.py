from admission.context_merge import merge_context
from admission.schemas import RequestContext
from admission.validation import validate_request

previous = RequestContext(
    applicantType="master",
    interests=["AI"],
    preferredCountries=["IE"],
)

update = RequestContext(
    currentEducationLevel="bachelor",
    transcriptCountry="MM",
    academicScore=3.4,
    gradingSystem="gpa",
    maximumScore=4.0,
)

merged = merge_context(previous, update)

print(merged.model_dump_json(indent=2))
print("Input errors:", validate_request(merged))