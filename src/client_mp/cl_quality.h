// cl_quality.h - mod (quality): graphics quality presets for Settings > EXTRAS > GRAPHICS QUALITY.
// Header only and free of engine types, so android/test/quality_test.cpp tests it on the build host.
//
// A preset is a bundle of settings the retail menus spread over several rows. The values are starting points chosen
// from what each dvar does; none is measured on a device yet (docs/mali.md).
#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace quality
{
struct Preset
{
    int lines;          // height of the back buffer; the widest listed mode of that height is used
    int aaSamples;      // r_aaSamples (1 = off); -1: leave as it is
    int picmip;         // r_picmip, r_picmip_bump, r_picmip_spec (0..3, higher = smaller textures)
    int aniso;          // r_texFilterAnisoMax (1..16)
    int shadows;        // sm_enable
    int shadowLights;   // sm_maxLights (0..4)
    int dof;            // r_dof_enable
    float lod;          // r_lodScaleRigid, r_lodScaleSkinned (larger = less detail)
    int clouds;         // fx_drawClouds
};

// index 0 (Custom) changes nothing
static const Preset kPresets[] = {
    {    0,  -1, 0,  1, 0, 0, 0, 1.0f, 1 },
    {  540,   1, 2,  1, 0, 0, 0, 2.0f, 0 },   // Ultra low
    {  720,   1, 1,  2, 0, 0, 0, 1.5f, 1 },   // Low
    {  900,   1, 0,  4, 1, 1, 0, 1.0f, 1 },   // Medium
    { 1080,  -1, 0, 16, 1, 4, 1, 1.0f, 1 },   // High: the engine's defaults
};
static const int kPresetCount = (int)(sizeof(kPresets) / sizeof(kPresets[0]));

// names holds "<width>x<height>" entries (r_mode's list). Picks the one whose height is nearest to lines (the
// lower one on a tie), the widest of those; false when the list has none.
static inline bool PickMode(const char *const *names, int count, int lines, char *out, int size)
{
    int bestWidth = 0, bestHeight = 0;
    for (int i = 0; i < count; ++i)
    {
        int w = 0, h = 0;
        if (!names || !names[i] || sscanf(names[i], "%dx%d", &w, &h) != 2 || w <= 0 || h <= 0)
            continue;
        const int distance = abs(h - lines), bestDistance = abs(bestHeight - lines);
        const bool better = !bestHeight || distance < bestDistance || (distance == bestDistance && h < bestHeight) ||
            (distance == bestDistance && h == bestHeight && w > bestWidth);
        if (better)
        {
            bestWidth = w;
            bestHeight = h;
        }
    }
    if (!bestHeight)
        return false;
    snprintf(out, (size_t)size, "%dx%d", bestWidth, bestHeight);
    return true;
}
}
