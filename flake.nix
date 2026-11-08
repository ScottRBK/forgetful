{
  description = "forgetful-ai - MCP Server for AI Agent Memory";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # nixpkgs-lib is flake-parts' own nixpkgs-lite; following it keeps a single
    # nix source in the closure instead of a second, independently pinned one.
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };

    # Non-flake entry points (default.nix / shell.nix). flake = false: to Nix it
    # is a function, not a flake, and it contributes no outputs of its own.
    flake-compat = {
      url = "github:NixOS/flake-compat";
      flake = false;
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
      };
    };

    git-hooks-nix = {
      url = "github:cachix/git-hooks.nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        # Follow our edge so the lock holds one flake-compat node, not one per consumer.
        flake-compat.follows = "flake-compat";
      };
    };
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      # x86_64-darwin intentionally omitted (deprecated upstream)
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
      ];
      imports = [ inputs.git-hooks-nix.flakeModule ];

      # Consume the project's own binary cache. Anyone who evaluates this flake
      # substitutes the uv2nix Python environment instead of rebuilding it, with
      # no nix.conf edits and no credentials (the cache is public).
      #
      # The key is the cache's public signing key; it is not a secret. A wrong
      # value here does not break the build - Nix rejects the substituted output
      # and falls back to building locally.
      flake.nixConfig = {
        substituters = [ "https://forgetful.cachix.org" ];
        trustedPublicKeys = [ "forgetful.cachix.org-1:KsfBQxnVjRUebMzIQG623sJjscZ63annyOZYj/f8vP4=" ];
      };

      perSystem =
        { config, pkgs, ... }:
        let
          inherit (pkgs) lib;
          python = pkgs.python312;

          # 1. Load workspace (pyproject.toml + uv.lock at eval time)
          workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
            workspaceRoot = ./.;
          };

          # 2. Overlay: uv.lock -> derivations (wheels preferred, house default)
          uvLockedOverlay = workspace.mkPyprojectOverlay {
            sourcePreference = "wheel";
          };

          # 3. Version (Dockerfile ARG VERSION parity): default dev, release injects real tag.
          # Pure builds (incl. `nix flake check`) always see "" -> "0.0.0+dev", never crash.
          # Release: FORGETFUL_VERSION=$(git describe --tags) nix build --impure
          version =
            let
              r = builtins.tryEval (builtins.getEnv "FORGETFUL_VERSION");
              e = if r.success then r.value else "";
            in
            if e != "" then e else "0.0.0+dev";

          # Docker tag parity with docker/metadata-action (build.yml):
          # CI pushes ghcr.io/<owner>/forgetful with semver + major.minor + latest.
          # buildLayeredImage takes a single tag, so tag the versioned image here
          # and `docker tag` the extra aliases after load (see docs/nix.md).
          # Docker tags must match [\w][\w.-]{0,127}; `+` (e.g. 0.0.0+dev) is invalid.
          dockerTag = builtins.replaceStrings [ "+" ] [ "-" ] version;

          myOverrides = _final: prev: {
            "forgetful-ai" = prev."forgetful-ai".overrideAttrs (_old: {
              SETUPTOOLS_SCM_PRETEND_VERSION = version;
            });
          };

          # 4. Python package set
          pythonSet =
            (pkgs.callPackage inputs.pyproject-nix.build.packages { inherit python; }).overrideScope
              (
                lib.composeManyExtensions [
                  inputs.pyproject-build-systems.overlays.wheel
                  uvLockedOverlay
                  myOverrides
                ]
              );

          # 5. Runtime env from the lock (default groups)
          forgetfulEnv = pythonSet.mkVirtualEnv "forgetful-env" workspace.deps.default;

          # 6. App package (house stdenv+makeWrapper for servers)
          #
          # Limit the wrapper's source to the files copied by installPhase.
          # If installPhase copies more paths, extend this fileset.
          # forgetfulEnv still builds the project from the unfiltered workspace,
          # so docs- or CI-only changes can rebuild both the environment and
          # this package. This fileset does not make the complete package hash
          # independent of those files.
          # pyproject.toml and uv.lock are read at eval time via workspaceRoot;
          # dependency changes still invalidate the Python environment.
          packageSrc = lib.fileset.toSource {
            root = ./.;
            fileset = lib.fileset.unions [
              ./app
              ./main.py
              ./alembic.ini
              ./alembic
            ];
          };

          appPkg = pkgs.stdenv.mkDerivation {
            pname = "forgetful-ai";
            inherit version;
            src = packageSrc;
            nativeBuildInputs = [ pkgs.makeWrapper ];
            buildInputs = [ forgetfulEnv ];
            installPhase = ''
              mkdir -p $out/bin $out/lib
              cp -r app main.py alembic.ini alembic $out/lib/
              makeWrapper ${forgetfulEnv}/bin/forgetful $out/bin/forgetful-ai \
                --prefix PYTHONPATH : "$out/lib"
              ln -s $out/bin/forgetful-ai $out/bin/forgetful
            '';
            meta = {
              description = "MCP Server for AI Agent Memory";
              mainProgram = "forgetful-ai";
            };
          };

          # 7. Sandboxed test run (matrix A7/A15). Allow-listed like packageSrc:
          # the suite reads pytest.ini, its own tree, the package sources and the
          # test_harness config that test_harness_* tests load by relative path.
          testSrc = lib.fileset.toSource {
            root = ./.;
            fileset = lib.fileset.unions [
              ./pytest.ini
              ./pyproject.toml
              ./app
              ./main.py
              ./alembic.ini
              ./alembic
              ./tests
              ./test_harness
              ./skills
            ];
          };

          # Sandbox-runnable tiers only: tests/integration (stubbed I/O) and
          # tests/e2e_sqlite (in-memory SQLite). tests/e2e needs a real
          # PostgreSQL and is excluded by both the directory scoping below and
          # pytest.ini's `-m "not e2e"`; either alone would leak.
          #
          # The suite is not network-free by default: fastembed pulls its
          # embedding and reranker models from Hugging Face, and the token
          # counter pulls a BPE blob from OpenAI's blob store. `testFixtures`
          # supplies both, revision-pinned, so the tests run against the real
          # providers rather than a reduced tier.
          testFixtures = pkgs.callPackage ./nix/test-fixtures.nix {
            caCertificates = pkgs.cacert;
          };

          testsPkg = pkgs.stdenv.mkDerivation {
            pname = "forgetful-ai-tests";
            inherit version;
            src = testSrc;
            # test_harness walkthrough tests drive `git` against a fixture repo,
            # and the sandbox PATH carries only what is listed here.
            nativeBuildInputs = [
              forgetfulEnv
              pkgs.git
            ];
            doCheck = true;
            checkPhase = ''
              runHook preCheck
              # The Nix sandbox leaves HOME unset; app config resolves paths from it.
              export HOME="$TMPDIR"
              # Serve the pinned models/tokenizer from the store and forbid egress,
              # so a missing fixture fails loudly instead of reaching for the network.
              export FASTEMBED_CACHE_DIR=${testFixtures.fastembedCache}
              export FASTEMBED_LOCAL_FILES_ONLY=1
              export HF_HUB_OFFLINE=1
              export TIKTOKEN_CACHE_DIR=${testFixtures.tiktokenCache}
              export SSL_CERT_FILE=${testFixtures.caBundle}
              pytest tests/integration tests/e2e_sqlite -m "not e2e" -q
              runHook postCheck
            '';
            installPhase = ''
              runHook preInstall
              mkdir -p $out
              runHook postInstall
            '';
            meta = {
              description = "forgetful-ai sandboxed test suite";
              broken = false;
            };
          };
        in
        {
          pre-commit.settings.hooks = {
            nixfmt.enable = true;
            deadnix.enable = true;
            statix.enable = true;
            ruff.enable = true;
            typos.enable = true;
            # Expand after first green pass: markdownlint, editorconfig-checker (+ .editorconfig)
          };

          devShells.default = pkgs.mkShell {
            packages = [
              forgetfulEnv
              pkgs.uv
              pkgs.ruff
              pkgs.python312Packages.pytest
              pkgs.python312Packages.pytest-asyncio
            ]
            ++ config.pre-commit.settings.enabledPackages;
            shellHook = ''
              ${config.pre-commit.shellHook}
              export PYTHONPATH="$PWD:$PYTHONPATH"
            '';
          };

          formatter = pkgs.writeShellScriptBin "fmt" ''
            ${lib.getExe config.pre-commit.settings.package} run --all-files --config ${config.pre-commit.settings.configFile}
          '';

          # App + Docker (house patterns): stdenv+makeWrapper server + layered OCI image on 8020
          # Image repo `forgetful` matches CI (ghcr.io/<owner>/forgetful) and
          # docker-compose default (`forgetful:latest`); pname stays forgetful-ai.
          packages = {
            forgetful-ai = appPkg;
            default = appPkg;
            docker = pkgs.dockerTools.buildLayeredImage {
              name = "forgetful";
              tag = dockerTag;
              created = "now";
              contents = [
                appPkg
                pkgs.bashInteractive
                pkgs.cacert
              ];
              config = {
                Cmd = [
                  "${appPkg}/bin/forgetful-ai"
                  "--transport"
                  "http"
                  "--host"
                  "0.0.0.0"
                  "--port"
                  "8020"
                ];
                ExposedPorts = {
                  "8020/tcp" = { };
                };
                Labels = {
                  "org.opencontainers.image.title" = "forgetful";
                  "org.opencontainers.image.description" = "MCP Server for AI Agent Memory";
                  "org.opencontainers.image.version" = version;
                  "org.opencontainers.image.licenses" = "MIT";
                };
              };
            };
          };

          # Authored check: `nix flake check` must prove the suite runs, not just
          # that the pre-commit config is well-formed.
          checks = {
            inherit testsPkg;
          };

          apps = {
            forgetful-ai = {
              type = "app";
              program = "${appPkg}/bin/forgetful-ai";
            };
            default = {
              type = "app";
              program = "${appPkg}/bin/forgetful-ai";
            };
          };
        };
    };
}
