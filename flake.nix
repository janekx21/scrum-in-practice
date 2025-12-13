{
  description = "Node.js development environment with pnpm";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Nodejs and pnpm
            nodejs
            corepack

            # Node dev
            vue-language-server
            typescript-language-server

            # Python with libs
            python3
            python3Packages.flask

            # Python dev
            ty
            ruff
            python3Packages.jedi-language-server
            python3Packages.python-lsp-server

            # REST API dev
            restish
          ];
        };
      }
    );
}
