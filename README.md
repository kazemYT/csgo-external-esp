# External ESP for CS:GO using a DirectX9 Overlay

This is an external ESP for CS:GO written in C++.

## Preview
![](https://i.imgur.com/4Vo5dem.png)

## Getting Started

Download the source, update the offsets, configure your project and finally compile.

### Building

1. Install [Visual Studio 2022](https://visualstudio.microsoft.com/) with the
   *Desktop development with C++* workload.
2. Install the legacy [DirectX SDK (June 2010)](https://www.microsoft.com/en-us/download/details.aspx?id=6812).
   It ships `d3dx9.h` / `d3dx9.lib`, which the Windows SDK does not. The installer
   sets the `DXSDK_DIR` environment variable that the project reads - if you
   extracted it by hand, either set `DXSDK_DIR` yourself or replace the two paths
   in the `PropertyGroup` of `csgo-external-esp.vcxproj`.
3. Open `csgo-external-esp.sln`, pick `Debug` or `Release` and build. The output
   lands in `build\Win32-<Configuration>\`.

The project targets the `v143` toolset. If you are on Visual Studio 2019, accept
the retarget prompt or set *Platform Toolset* to `v142` in the project properties.

### Why x86 only

`csgo.exe` is a 32 bit process, and the code stores entity pointers in
`std::uintptr_t`. An x64 build would read 8 byte pointers out of a 4 byte process
and every entity lookup would break, so the solution only offers `x86`
configurations.

### Character set

The project uses the *MultiByte* character set on purpose: with `UNICODE` defined,
`Module32First` / `Process32First` resolve to their `W` variants, whose
`szModule` / `szExeFile` are `WCHAR` arrays that `std::string_view::compare` will
not accept.

## Offsets

All offsets live in [`csgo_sdk/offsets.h`](csgo_sdk/offsets.h), which is generated
from [`offsets.cs`](offsets.cs) - do not edit the header by hand. To update after a
game patch:

1. Drop a fresh `offsets.cs` from [hazedumper](https://github.com/frk1/hazedumper)
   over the one in the repository root.
2. Run `python tools/generate_offsets.py` to regenerate `csgo_sdk/offsets.h`.

`m_iIndex` is not part of a hazedumper dump and is kept by hand in the generator.

Note that the offsets are dumped from `client.dll`. Valve merged
`client_panorama.dll` into `client.dll`, so if your dump targets the merged module
you also have to change the module name in `sdk::modules_t` and `esp::draw`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
