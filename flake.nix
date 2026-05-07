{
  description = "Interactive Hyprland keybind visualizer";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs   = nixpkgs.legacyPackages.${system};
    in {
      packages.${system}.default = pkgs.callPackage ./package.nix { };
      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (p: [ p.pygobject3 ]))
          pkgs.gtk4
          pkgs.gobject-introspection
          pkgs.gtk4-layer-shell
          pkgs.glib
        ];
        shellHook = ''
          export GI_TYPELIB_PATH="${pkgs.gtk4-layer-shell}/lib/girepository-1.0:$GI_TYPELIB_PATH"
          export LD_LIBRARY_PATH="${pkgs.gtk4-layer-shell}/lib:$LD_LIBRARY_PATH"
        '';
      };
    };
}
