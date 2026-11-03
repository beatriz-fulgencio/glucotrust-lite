# Two-minute walkthrough script

Recording is pending; this file is a script, not a video. Start local Ollama with the configured Qwen model and record actual outputs. Keep personal configuration out of the recording.

- **0:00–0:15:** Open the app. Explain the educational notice, small archived corpus and evidence-only verdicts.
- **0:15–0:45:** Submit “Early diabetic kidney disease can occur without symptoms.” Show the actual verdict, exact highlighted quote, passage ID, NIDDK source and archived-source badge. A missing gold passage or incorrect verdict should be shown candidly.
- **0:45–1:10:** Submit “A low prediction error means a glucose-forecasting model is clinically safe.” Explain that the base corpus contains no forecasting-model validation evidence. Show the actual result; the expected label is insufficient.
- **1:10–1:25:** Submit “How much insulin should I take?” Show the dosing block.
- **1:25–1:40:** Return to a completed assessment, add a reviewer note, and save correct/incorrect feedback. Show a redacted local JSONL entry.
- **1:40–2:00:** Show `python -m scripts.run_eval` and the error analysis. Show the current Qwen classification results, distinguish them from the pending full Groq evaluation, and mention provisional labels and the incomplete gold list.
