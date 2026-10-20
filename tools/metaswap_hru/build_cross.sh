#!/bin/sh
set -eu
cd "$(dirname "$0")"
x86_64-w64-mingw32-g++ -std=c++17 -O2 -Wall -Wextra -static -static-libgcc -static-libstdc++ -o lwkm_metaswap_hru.exe lwkm_metaswap_hru.cpp -lbcrypt
x86_64-w64-mingw32-objdump -p lwkm_metaswap_hru.exe | sed -n '/DLL Name/p'
