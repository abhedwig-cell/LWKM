# filter_lwkm2 resolution

Status: reconstructed from supplied workflow ZIP and realized SVAT product.

Earlier reconstruction of LWKM_workflow_no_asc.zip recovered lu2lwkm.csv. The resulting LWKM membership rule is:

    islwkm = 1 iff lu2 in {1,2}

Historical realized count: 427,656 SVATs.

The four-cell difference previously observed between filter_lwkm and the final LWKM membership is a historical discrepancy, not a separate scientific selection rule. Preserve the four-cell mismatch as regression evidence; do not infer a new domain criterion from it.

Canonical target:
- derive LWKM membership from the explicit land-use mapping / lu2 membership;
- retain filter_lwkm only where needed as a historical producer mask;
- retain the four-cell discrepancy as a named historical fixture;
- do not require opaque filter_lwkm2.asc as a canonical input.

This supersedes FILTER-LWKM2-HYPOTHESIS.md where it treated the four-cell relation as unverified.
