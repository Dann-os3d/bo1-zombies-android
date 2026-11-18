# Mali (ARM) support (NOT part of the original game)

Work to run this port well on ARM Mali GPUs (Bifrost, Valhall, 5th Gen). Status: **probe only, nothing tuned yet**.
No Mali device has run this build; every number a Mali change needs has to come from one. Until then, no setting
here is changed for Mali.

## What is Adreno-specific today

| piece | Adreno-specific? | on Mali |
| --- | --- | --- |
| `bo1_driver.c` custom driver (libadrenotools, Mesa Turnip) | yes, Qualcomm only | not used: without `files/driver.txt` it returns at once and the system driver stays |
| `bo1_vk_async`, `bo1_vk_resolve` defaults | measured on an Adreno 830 only (`web_input.cpp`, `build-dxvk.sh`) | unknown; kept as they are |
| Vulkan renderer (DXVK 2.6.1) | no, but needs Vulkan 1.3 and `VK_EXT_robustness2` (`nullDescriptor`) | works only if the Mali driver offers both; otherwise the game falls back to OpenGL ES 3 |
| OpenGL ES 3 shim (`src/web/d3d9`) | no, but its buffer-update path was tuned on an Adreno 830 (`d3d9_draw.cpp`) | untested |
| `native_perf.cpp` GPU load | no | already reads `/sys/class/misc/mali0/device/utilization` |

## The probe (`bo1_driver.c`, `// mod (mali):`)

At start, on the system driver, one extra log line (and the environment variable `BO1_GPU_VENDOR`: `arm`,
`qualcomm` or `other`):

```
gpu: vendor arm (0x13B5), Vulkan 1.1, VK_EXT_robustness2 no, nullDescriptor no, graphics pipeline library no; DXVK needs Vulkan 1.3 and nullDescriptor
```

(the values above are an example of the format, not a measurement). It sits next to the existing `vulkan driver:`
line in `bo1.log`. Nothing reads `BO1_GPU_VENDOR` yet.

## Test protocol on a Mali device

1. Install, copy the game files, start once. Send the first 40 lines of `files/bo1.log` (`vulkan driver:`, `gpu:`,
   `renderer:`, `native:` lines).
2. Menu room, 1280x720, `+set bo1_fpscounter 1`: once with `BO1_RENDERER=vulkan`, once with `BO1_RENDERER=gles`
   (or Settings > Graphics > RENDERER). Note FPS, 1 % low and the GPU utilization line.
3. `zombie_theater`, same two runs, `r_aaSamples 1` (1 is off; the range starts at 1).
4. If the log says `renderer: Vulkan is not available here, using OpenGL ES`, keep the `vulkan:` line above it.

## Candidates, in the order to decide after the data (none done)

1. **Renderer default by GPU**: OpenGL ES 3 as the default when the `gpu:` line shows no `nullDescriptor`
   (skips the failed DXVK trial at start). Needs the log from step 1.
2. **Program binary cache for OpenGL ES** (`glGetProgramBinary` / `glProgramBinary`): first draw of a shader
   combination costs up to 250 ms on the Adreno 830 (`android-port.md`); the same stall is likely on Mali.
3. **Vulkan pipeline cache kept between runs**, if DXVK's state cache is not already persisted (to check).
4. **Automatic first-start preset** from RAM and GPU (the manual presets below exist; the automatic choice does not).
5. **Memory**: engine heap and fastfile streaming on 4 GB devices (the README asks for 6 GB).

## Graphics quality presets (`cl_quality.h`, `// mod (quality):`)

Settings > EXTRAS > GRAPHICS QUALITY: `bo1_quality` (archived, default 0, 0 to 4). Choosing 1 to 4 sets the dvars
below and restarts the video (`vid_restart`); 0 (Custom) changes nothing. The resolution is the widest mode of
`r_mode`'s list at the preset's height, so a phone's own shape is kept (the list has 540, 720, 900 and 1080 lines of
the display's shape, `d3d9_direct3d.cpp`). Settings > Graphics > VIDEO MODE still sets the resolution alone.

| | Ultra low (1) | Low (2) | Medium (3) | High (4) |
| --- | --- | --- | --- | --- |
| back buffer height | 540 | 720 | 900 | 1080 |
| `r_aaSamples` (1 = off) | 1 | 1 | 1 | unchanged |
| `r_picmip`, `_bump`, `_spec` (0..3) | 2 | 1 | 0 | 0 |
| `r_texFilterAnisoMax` | 1 | 2 | 4 | 16 |
| `sm_enable` / `sm_maxLights` | 0 / 0 | 0 / 0 | 1 / 1 | 1 / 4 |
| `r_dof_enable` | 0 | 0 | 0 | 1 |
| `r_lodScaleRigid`, `_Skinned` | 2 | 1.5 | 1 | 1 |
| `fx_drawClouds` | 0 | 1 | 1 | 1 |

Limits: the values are starting points, **not measured**; changing one row by hand leaves `bo1_quality` as it was
(it names the last preset applied); `r_picmip_manual` is set to 1 by every preset. `tools/native/test-quality.sh`
tests the table's ranges and the mode choice on the build host.

## Not done

Everything above. No Mali measurement, no device test, no build of this change (the Android build needs the
patched clang 21 container of `tools/native/docker/Dockerfile`).
