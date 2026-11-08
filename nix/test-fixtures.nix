{
  lib,
  fetchurl,
  runCommand,
  caCertificates,
}:
let
  # Embedding and reranking models are fetched from Hugging Face at process
  # start, and the token counter fetches a BPE blob from OpenAI's blob store.
  # The Nix sandbox has no network, so the check environment has to supply all
  # three up front. These fixtures reproduce, byte for byte, the on-disk layout
  # that `huggingface_hub` and `tiktoken` read from their caches, which lets the
  # existing offline switches (FASTEMBED_LOCAL_FILES_ONLY, HF_HUB_OFFLINE) do
  # the work instead of patching the tests.
  #
  # Revision-pinned: updating settings.EMBEDDING_MODEL / RERANKING_MODEL means
  # updating the manifest below, and a stale sha256 fails the build loudly
  # rather than silently fetching something else.

  # Each entry: revision-pinned snapshot files, addressed by sha256 of the
  # served content. `path` is relative to the repository root.
  hubManifest = {
    "Qdrant/bge-small-en-v1.5-onnx-Q" = {
      # settings.EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5" resolves here:
      # fastembed maps the model alias to this ONNX-quantised export.
      rev = "aa8f8b060edb00e03bfdd08813a2949946c8ba55";
      files = [
        {
          path = "config.json";
          size = 706;
          sha256 = "13582bcf2effc85b7bf3d3f5532e686bc1c9ce86bb009d10f0ec33cbe92299dd";
        }
        {
          path = "special_tokens_map.json";
          size = 695;
          sha256 = "5d5b662e421ea9fac075174bb0688ee0d9431699900b90662acd44b2a350503a";
        }
        {
          path = "tokenizer_config.json";
          size = 1242;
          sha256 = "0b29c7bfc889e53b36d9dd3e686dd4300f6525110eaa98c76a5dafceb2029f53";
        }
        {
          path = "tokenizer.json";
          size = 711396;
          sha256 = "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66";
        }
        {
          path = "model_optimized.onnx";
          size = 66465124;
          sha256 = "51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431";
        }
      ];
    };
    "Xenova/ms-marco-MiniLM-L-12-v2" = {
      # settings.RERANKING_MODEL.
      rev = "42a4a787e30451cf9dbd09080c2a5b8dde332c1e";
      files = [
        {
          path = "config.json";
          size = 826;
          sha256 = "681b15ee0e4ec2cc2320b4e32e01266ebcbc8a84d55c9f0fac04cfefb7eece30";
        }
        {
          path = "special_tokens_map.json";
          size = 125;
          sha256 = "b6d346be366a7d1d48332dbc9fdf3bf8960b5d879522b7799ddba59e76237ee3";
        }
        {
          path = "tokenizer_config.json";
          size = 1242;
          sha256 = "0b29c7bfc889e53b36d9dd3e686dd4300f6525110eaa98c76a5dafceb2029f53";
        }
        {
          path = "tokenizer.json";
          size = 711396;
          sha256 = "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66";
        }
        {
          path = "onnx/model.onnx";
          size = 133708208;
          sha256 = "3a6d50ce60de831c8c68197df674eeb878d4ff34bb1aca5d1f3cb346c9075dba";
        }
      ];
    };
  };

  # huggingface_hub names blobs by etag for regular files and by sha256 for LFS
  # objects. Naming everything by sha256 is self-consistent, which is all the
  # reader requires: snapshots resolve through symlinks, and the blob name is
  # never re-derived while offline.
  fetchHubFile =
    repo: rev:
    { path, sha256, ... }:
    fetchurl {
      name = "hf-${builtins.replaceStrings [ "/" ] [ "+" ] repo}-${baseNameOf path}";
      url = "https://huggingface.co/${repo}/resolve/${rev}/${path}";
      inherit sha256;
    };

  repoDir =
    repo:
    { rev, files }:
    let
      entries = builtins.map (f: {
        inherit (f) path size;
        blob = f.sha256;
        src = fetchHubFile repo rev f;
        # A snapshot entry is a symlink into blobs/, so the climb out of
        # snapshots/<rev>/ depends on how deep the path nests inside the repo:
        # `config.json` needs ../../, `onnx/model.onnx` needs ../../../.
        up =
          let
            slashes = builtins.foldl' (n: c: n + (if c == "/" then 1 else 0)) 0 (lib.stringToCharacters f.path);
          in
          lib.concatStrings (lib.genList (_: "../") (2 + slashes));
      }) files;
    in
    ''
      repoDir="$out/models--${builtins.replaceStrings [ "/" ] [ "--" ] repo}"
      mkdir -p "$repoDir/blobs" "$repoDir/refs" "$repoDir/snapshots/${rev}"

      printf '%s' '${rev}' > "$repoDir/refs/main"

      metadata='{'
      first=1
    ''
    + lib.concatMapStrings (e: ''
      if [ "$first" = 1 ]; then first=0; else metadata="$metadata,"; fi
      cp '${e.src}' "$repoDir/blobs/${e.blob}"
      mkdir -p "$repoDir/snapshots/${rev}/$(dirname '${e.path}')"
      ln -s '${e.up}blobs/${e.blob}' "$repoDir/snapshots/${rev}/${e.path}"
      metadata="$metadata\"snapshots/${rev}/${e.path}\": {\"size\": ${toString e.size}, \"blob_id\": \"${e.blob}\"}"
    '') entries
    + ''
      printf '%s' "$metadata}" > "$repoDir/files_metadata.json"
    '';

  fastembedCache = runCommand "forgetful-fastembed-cache" { } ''
    mkdir -p $out
    ${lib.concatStringsSep "\n" (lib.mapAttrsToList repoDir hubManifest)}
  '';

  # tiktoken's cache key is sha1 of the blob URL, stored with no extension
  # (tiktoken/load.py: `cache_key = hashlib.sha1(blobpath.encode()).hexdigest()`).
  # TokenCounter defaults to gpt-4, which maps to cl100k_base.
  cl100k = fetchurl {
    name = "cl100k_base.tiktoken";
    url = "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken";
    sha256 = "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7";
  };

  tiktokenCache = runCommand "forgetful-tiktoken-cache" { } ''
    mkdir -p $out
    cp ${cl100k} $out/9b5ad71b2ce5302211f9c61530b329a4922fc6a4
  '';

  # httpx builds its SSL context from $SSL_CERT_FILE when the variable is set.
  # The sandbox inherits it pointing at /etc/ssl/certs, which does not exist
  # there, so every HTTPS client construction raises FileNotFoundError.
  caBundle = "${caCertificates}/etc/ssl/certs/ca-bundle.crt";
in
{
  inherit fastembedCache tiktokenCache caBundle;
}
