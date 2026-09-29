# DRA weighted-level algebra finding

## Current source

For each drainage system:
  D = sum(c_i * (g_i - p_i)) / sum(c_i)
  p_tmp = g_bar - D

Later:
  depth = -p_tmp + g_bar

Substitution gives:
  depth = -(g_bar-D)+g_bar = D

Therefore the unweighted glk_avg cancels EXACTLY from the final drainage level depth before output, provided no intervening non-linear operation occurs.

The later clamps are applied after this cancellation-form transformation:
  depth = max(0, depth)
  depth = min(dep_avg, depth)

So the realized LEVEL depth is simply the conductance-weighted local depth below ground:
  depth_rep = sum(c_i * (g_i-p_i))/sum(c_i),
clamped to [0, dep_avg].

This is mathematically consistent with the separately computed:
  dep_avg = sum(c_i * (g_i-bodh_i))/sum(c_i).

Thus H-DRA-LEVEL01 concern about mixing unweighted glk_avg with weighted levels is falsified for the final output depth. The code is unnecessarily opaque but algebraically sound.

Recommendation: modern implementation should calculate weighted depth directly and avoid the temporary absolute-level-like representation, with regression proving identity.
