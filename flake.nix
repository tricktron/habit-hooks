{
  description = "Habit-hooks development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "aarch64-linux"
        "x86_64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};

          pmd = pkgs.stdenvNoCC.mkDerivation {
            pname = "pmd";
            version = "7.26.0";
            src = pkgs.fetchurl {
              url = "https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.26.0/pmd-dist-7.26.0-bin.zip";
              sha256 = "9f55cb7ff0e9f9a66dd2f005eaa370e84c8a4cd971b134aa14a930c4a283ebc9";
            };
            nativeBuildInputs = [ pkgs.unzip ];
            installPhase = ''
              runHook preInstall
              # unpackPhase leaves us inside the dist's pmd-bin-<version>/ dir,
              # so a plain copy of `.` puts bin/pmd on PATH at $out/bin/pmd.
              test -d bin -a -f bin/pmd || {
                echo "pmd dist layout changed; expected bin/pmd inside the zip" >&2
                exit 1
              }
              mkdir -p $out
              cp -R . $out/
              runHook postInstall
            '';
          };

          corepackBin = "$HOME/.cache/habit-hooks/corepack/bin";
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python3
              pkgs.uv # needed for the test suite only
              pkgs.ruff
              pkgs.deptry
              pkgs.nodejs_22
              pkgs.php
              pkgs.jq
              pkgs.git
              pkgs.procps
              pkgs.jre_headless
              pmd
            ];
            shellHook = ''
              export UV_SYSTEM_CERTS=1
              mkdir -p "${corepackBin}"
              corepack enable --install-directory "${corepackBin}" >/dev/null
              export PATH="${corepackBin}:$PATH"

              # Dev environment, built once (marker file, idempotent): a venv
              # over the nix python with the whole workspace editable and only
              # the pure-Python dev tools. ruff and deptry are deliberately NOT
              # installed here — they are Nix binaries on PATH, so a run never
              # reaches a manylinux wheel that the NixOS loader refuses.
              if [ ! -f .venv/.habit-hooks-nix-dev ]; then
                python3 -m venv .venv
                uv pip install --python .venv/bin/python \
                  -e plugins/generic -e plugins/python \
                  -e plugins/typescript -e plugins/php -e plugins/java \
                  -e . pytest markdown-it-py packaging
                touch .venv/.habit-hooks-nix-dev
              fi
              export VIRTUAL_ENV="$PWD/.venv"
              export PATH="$PWD/.venv/bin:$PATH"
            '';
          };
        });
    };
}
