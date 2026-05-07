{ lib
, python3Packages
, gtk4
, gtk4-layer-shell
, gobject-introspection
, libadwaita
, wrapGAppsHook4
}:

python3Packages.buildPythonApplication {
  pname = "hyprland-keys";
  version = "0.1.0";
  format = "pyproject";

  src = ./.;

  nativeBuildInputs = [
    wrapGAppsHook4
    gobject-introspection
  ];

  buildInputs = [
    gtk4
    gtk4-layer-shell
    gobject-introspection
    libadwaita
  ];

  propagatedBuildInputs = with python3Packages; [
    pygobject3
  ];

  # Install the CSS file alongside the package
  postInstall = ''
    install -Dm644 style.css $out/lib/hyprland-keys/style.css
  '';

  # Make gtk4-layer-shell typelib available at runtime
  preFixup = ''
    gappsWrapperArgs+=(
      --prefix GI_TYPELIB_PATH : "${gtk4-layer-shell}/lib/girepository-1.0"
    )
  '';

  meta = {
    description = "Interactive Hyprland keybind visualizer with keyboard layout and modifier filtering";
    mainProgram = "hyprland-keys";
  };
}
