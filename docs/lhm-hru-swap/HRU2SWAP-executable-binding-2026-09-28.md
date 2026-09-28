# HRU2SWAP executable binding — 28 September 2026

Status: **BINARY IDENTITY BOUND; BUILD REPRODUCIBILITY OPEN**

The previously supplied `exe.zip` was inspected together with the supplied Fortran source archive.

## Binary

`HRU2SWAP.exe`

- SHA-256: `a6a56f0f17395216712cc79ddf68e2550cf67f26275dca1f86c90ed25102453d`
- size: 1,142,784 bytes
- PE timestamp: 2026-04-29 13:49:10 UTC

Embedded printable strings include:

- `HRUlist2SWAP version 0.38 apr-2026`;
- `HRUlist2SWAP v0.38 apr-26`;
- `hrulist2SWAP.f90`;
- `d:\fortran\LWKM\hrulist2swap\hrulist2swap.f90`.

## Source

The supplied source archive contains:

`hrulist2SWAP/hrulist2SWAP.f90`

- SHA-256: `17f779223db9458a8a5b95b3587b09c9af39b8bd8878a78d2d4d67481a2ad4d4`;
- source header: `HRUlist2SWAP v0.38 apr-26`.

## Conclusion

The production-named binary can now be bound to the same program identity/version/date as the inspected v0.38 source. This is strong binary/source-version evidence.

What is not yet proven is byte-reproducible compilation from that exact source file because compiler version, flags, linked libraries and build script are not bound.

Canonical status:

- program/version binding: **BOUND**;
- exact source-file semantic binding: **STRONG**;
- reproducible build provenance: **OPEN**.

The executable should therefore no longer be described merely as an unverified binary name.
