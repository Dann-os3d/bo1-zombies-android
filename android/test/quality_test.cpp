// quality_test.cpp - off-device test of src/client_mp/cl_quality.h (tools/native/test-quality.sh)
#include "../../src/client_mp/cl_quality.h"
#include <assert.h>
#include <stdio.h>

static int fails;
#define EXPECT(cond) do { if (!(cond)) { printf("FAIL line %d: %s\n", __LINE__, #cond); ++fails; } } while (0)

int main()
{
    // the list the shim builds for a 2460x1080 phone (d3d9_direct3d.cpp displayModeList): standard shapes up to the
    // display, plus the display's own shape at 540, 720, 900 and 1080 lines
    const char *phone[] = { "640x480", "800x600", "1024x768", "1280x720", "1366x768", "1600x900", "1920x1080",
                            "1230x540", "1640x720", "2050x900", "2460x1080" };
    char out[32];
    EXPECT(quality::PickMode(phone, 11, 540, out, sizeof(out)) && !strcmp(out, "1230x540"));
    EXPECT(quality::PickMode(phone, 11, 720, out, sizeof(out)) && !strcmp(out, "1640x720"));   // widest of the 720s
    EXPECT(quality::PickMode(phone, 11, 900, out, sizeof(out)) && !strcmp(out, "2050x900"));
    EXPECT(quality::PickMode(phone, 11, 1080, out, sizeof(out)) && !strcmp(out, "2460x1080"));

    // a 16:9 display: only 1280x720 and 1920x1080 at those heights; 540 falls to the nearest height (480)
    const char *tv[] = { "640x480", "800x600", "1280x720", "1920x1080" };
    EXPECT(quality::PickMode(tv, 4, 720, out, sizeof(out)) && !strcmp(out, "1280x720"));
    EXPECT(quality::PickMode(tv, 4, 540, out, sizeof(out)) && !strcmp(out, "640x480"));

    // bad input
    const char *junk[] = { "", "abc", "0x720", 0 };
    EXPECT(!quality::PickMode(junk, 4, 720, out, sizeof(out)));
    EXPECT(!quality::PickMode(0, 0, 720, out, sizeof(out)));

    // table: Custom changes nothing; resolution rises and weight falls from High to Ultra low
    EXPECT(quality::kPresetCount == 5);
    for (int i = 2; i < quality::kPresetCount; ++i)
    {
        EXPECT(quality::kPresets[i].lines > quality::kPresets[i - 1].lines);
        EXPECT(quality::kPresets[i].picmip <= quality::kPresets[i - 1].picmip);
        EXPECT(quality::kPresets[i].aniso >= quality::kPresets[i - 1].aniso);
    }
    for (int i = 1; i < quality::kPresetCount; ++i)
    {
        const quality::Preset &p = quality::kPresets[i];
        EXPECT(p.picmip >= 0 && p.picmip <= 3);           // r_picmip range
        EXPECT(p.aniso >= 1 && p.aniso <= 16);            // r_texFilterAnisoMax range
        EXPECT(p.shadowLights >= 0 && p.shadowLights <= 4);   // sm_maxLights range
        EXPECT(p.aaSamples == -1 || p.aaSamples >= 1);    // r_aaSamples starts at 1 (off)
    }
    printf(fails ? "FAILED: %d\n" : "quality test: all passed\n", fails);
    return fails ? 1 : 0;
}
