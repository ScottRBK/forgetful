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

    # The web UI this server can host. Pinned by revision in flake.lock, which
    # is content-addressed, so the bundle consumed from it is reproducible and
    # does not depend on any branch moving. The same locked revision feeds the
    # container's Node stage, so every path builds one commit of one project.
    #
    # A flake, not a plain source tree: the UI project builds its own production
    # bundle and asserts the shape of it, so this repository consumes that output
    # instead of restating the recipe, the dependency hash and the version.
    forgetful-ui = {
      url = "github:twstagg/forgetful-ui/7428a5dc210009826f38aa854a034c392206aa25";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-parts.follows = "flake-parts";
        git-hooks-nix.follows = "git-hooks-nix";
        flake-compat.follows = "flake-compat";
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

  # Nix reads flake settings from this top-level key, alongside `inputs` and
  # `outputs` - NOT from an output attribute. See the flake format section of
  # the nix manual (src/nix/flake.md).
  #
  # The `extra-` forms are deliberate: they add to whatever the user already
  # has configured instead of replacing it, so a consumer's own cache and
  # signing keys keep working.
  #
  # The public signing key is not a secret. A wrong value degrades rather than
  # breaks: Nix rejects an unverifiable substitution and builds locally.
  nixConfig = {
    extra-substituters = [ "https://forgetful.cachix.org" ];
    extra-trusted-public-keys = [
      "forgetful.cachix.org-1:KsfBQxnVjRUebMzIQG623sJjscZ63annyOZYj/f8vP4="
    ];
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

      perSystem =
        {
          config,
          pkgs,
          system,
          ...
        }:
        let
          inherit (pkgs) lib;
          python = pkgs.python312;

          # 1. Load workspace (pyproject.toml + uv.lock at eval time)
          workspace = inputs.uv2nix.lib.workspace.loadWorkspace {
            workspaceRoot = ./.;
          };

          # 2. Overlay: uv.lock -> derivations (wheels preferred; they need no build step)
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

          # 5b. Web UI bundle
          #
          # Taken from the UI project's own flake rather than rebuilt here, so a
          # Nix install ships a real bundle without this repository restating
          # that project's build recipe, dependency hash or version. The UI
          # project also checks the produced bundle's shape, which this side
          # cannot assert about a tree it does not own.
          #
          # It publishes x86_64-linux only. Evaluating another architecture
          # fails here with that reason rather than a missing attribute.
          uiBundle =
            inputs.forgetful-ui.packages.${system}.default
              or (throw "forgetful-ui publishes no bundle for ${system}; add it to the UI flake's systems first");

          # 6. App package: stdenv + makeWrapper around the runtime env
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
              # Package data, so UI_ENABLED=true needs no UI_DIST_DIR and no dist/.
              # This path is inside the store, which is what makes the default
              # bundle location a store path rather than a build-time accident.
              mkdir -p $out/lib/app/web
              cp -r ${uiBundle} $out/lib/app/web/ui
              makeWrapper ${forgetfulEnv}/bin/forgetful $out/bin/forgetful-ai \
                --prefix PYTHONPATH : "$out/lib"
              ln -s $out/bin/forgetful-ai $out/bin/forgetful
            '';
            meta = {
              description = "MCP Server for AI Agent Memory";
              mainProgram = "forgetful-ai";
            };
          };

          # 7. Sandboxed test run. Allow-listed like packageSrc:
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
              # Imported by name: the benchmark test puts this directory on
              # sys.path. Listed as a file, not a directory, so the 428K
              # synthetic corpus stays out of the test source.
              ./benchmarks/retrieval/eval_lib.py
              # Imported by the packaging tests; lives at the root because the
              # build hook loads it by path, outside the installed package.
              ./ui_bundle.py
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

          # App + Docker: stdenv+makeWrapper server + layered OCI image on 8020
          # Image repo `forgetful` matches CI (ghcr.io/<owner>/forgetful) and
          # docker-compose default (`forgetful:latest`); pname stays forgetful-ai.
          packages = {
            forgetful-ai = appPkg;
            # The built bundle on its own, so a reviewer can inspect exactly what
            # the package ships without unpacking it.
            ui-bundle = uiBundle;
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
