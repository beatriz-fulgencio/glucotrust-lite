"""Download model weights to the ignored project-local cache."""
from huggingface_hub import snapshot_download
from glucotrust.retrieve import EMBEDDING_MODEL, EMBEDDING_REVISION


def main():
    snapshot_download(EMBEDDING_MODEL, revision=EMBEDDING_REVISION,
                      local_dir="data/cache/all-MiniLM-L6-v2",
                      ignore_patterns=["onnx/*", "openvino/*", "*.h5", "*.ot", "pytorch_model.bin"])


if __name__ == "__main__":
    main()
