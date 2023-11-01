{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
    buildInputs = with pkgs; [
        python310
        poetry
    ];

    LD_LIBRARY_PATH = "${pkgs.zlib}/lib:$LD_LIBRARY_PATH";
}
