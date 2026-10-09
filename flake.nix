{
  description = "forgetful-ai - MCP Server for AI Agent Memory";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";

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
      inputs.nixpkgs.follows = "nixpkgs";
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
          appPkg = pkgs.stdenv.mkDerivation {
            pname = "forgetful-ai";
            inherit version;
            src = ./.;
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
          packages = {
            forgetful-ai = appPkg;
            default = appPkg;
            docker = pkgs.dockerTools.buildLayeredImage {
              name = "forgetful-ai";
              tag = "latest";
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
              };
            };
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
