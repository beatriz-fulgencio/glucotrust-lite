import json
import httpx
from ollama import Client
from glucotrust.assess import OllamaAssessor


def test_real_sdk_serializes_and_parses_without_network(passage, tmp_path):
    def handle(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"model": "test:latest", "digest": "abc"}]})
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body["format"]["type"] == "object"
        assert body["options"] == {"temperature": 0, "num_ctx": 16384, "num_predict": 1800}
        assert body["stream"] is False
        assert [m["role"] for m in body["messages"]] == ["system", "user"]
        output = dict(verdict="supported", citations=[dict(passage_id=passage.passage_id,
                      quote="Insulin helps glucose enter cells.")], explanation="Direct evidence.")
        return httpx.Response(200, json=dict(model=body["model"], done=True, done_reason="stop",
            message=dict(role="assistant", content=json.dumps(output)), eval_count=20, total_duration=100))
    client = Client(host="http://localhost:11434", transport=httpx.MockTransport(handle))
    result = OllamaAssessor(client=client, model="test", cache_dir=tmp_path).assess("claim", [passage])
    assert result.verdict == "supported"
