# HRU partitioner strategy

Historical compatibility and modernization are deliberately separated.

## Compatibility backend

tools/hru_partitioners.py provides RScclustPartitioner. It passes only the two robust-scaled hydrological variables and the requested minimum cluster size to R/scclust. The eleven-round routing, area gates, adaptive groupfraction logic, qualification, donor matching, representative selection and QA live outside R.

This shrinks the R dependency from the complete historical workflow to one numerical partition primitive.

## Native backend

A native implementation is not required for the first canonical admission. It may be developed later for portability/performance, but it must pass the label-invariant R compatibility fixtures before replacing RScclustPartitioner in the historical profile.

## Why

Reimplementing scclust before a reproducible baseline exists creates unnecessary scientific risk. Keeping the real package as a narrow compatibility backend lets the surrounding workflow be modernized now while preserving a route to exact historical partitioning.
