#ifndef LWKM_HUM_SOURCE_CONTRACT_HPP
#define LWKM_HUM_SOURCE_CONTRACT_HPP
// MET08 primary-production repair. Same source contract as the passed MET07 trials.
// This is the prepared LHM UG vapour-pressure raster, NOT raw KNMI relative humidity.
#include <algorithm>
#include <cctype>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
namespace lwkm_hum {
constexpr std::size_t index = 5;
constexpr const char* version = "MET08_PRIMARY_UG_HUM_20261117";
inline const std::string& require(const std::map<std::string,std::string>& c,
                                  const std::string& key) {
    const auto it = c.find(key);
    if (it == c.end() || it->second.empty())
        throw std::runtime_error("HUM_CONFIG_MISSING: " + key);
    return it->second;
}
inline void validate_config(const std::map<std::string,std::string>& c) {
    if (c.count("path_FG") || c.count("scale_FG"))
        throw std::runtime_error("LEGACY_FG_HUM_REJECTED: use path_HUM=LHM UG; no FG alias");
    if (require(c,"quantity_HUM") != "actual_vapour_pressure" ||
        require(c,"unit_HUM") != "kPa")
        throw std::runtime_error("HUM_REQUIRES_ACTUAL_VAPOUR_PRESSURE_KPA");
    const auto& token = require(c,"scale_HUM");
    std::size_t end = 0;
    const double scale = std::stod(token,&end);
    if (end != token.size() || !std::isfinite(scale) || scale != 1.0)
        throw std::runtime_error("LHM_UG_REQUIRES_SCALE_ONE: no conversion or clipping");
    std::string path = require(c,"path_HUM");
    std::replace(path.begin(),path.end(),'\\','/');
    std::transform(path.begin(),path.end(),path.begin(),
                   [](unsigned char ch){return char(std::tolower(ch));});
    const std::string suffix = "ug/ug_{date}.asc";
    if (path.size() < suffix.size() ||
        path.compare(path.size()-suffix.size(),suffix.size(),suffix) != 0 ||
        (path.size() > suffix.size() && path[path.size()-suffix.size()-1] != '/') ||
        path.find("{date}") != path.rfind("{date}"))
        throw std::runtime_error("HUM_SOURCE_MUST_BE_IDENTIFIED_LHM_UG: " + path);
}
inline void validate_value(double value,const std::string& where) {
    if (!std::isfinite(value) || value < 0.0 || value > 10.0)
        throw std::runtime_error("HUM_OUTSIDE_0_10_KPA: " + where);
}
inline void validate_grid(const std::vector<double>& values,double nodata,
                          const std::string& day) {
    if (!std::isfinite(nodata)) throw std::runtime_error("HUM_NONFINITE_NODATA");
    bool any = false;
    // Check ORIGINAL values, before nearest-valid filling. Invalid physics is not NoData.
    for (std::size_t i=0;i<values.size();++i) {
        if (values[i] == nodata) continue;
        if (!std::isfinite(values[i]) || values[i] < 0.0 || values[i] > 10.0)
            validate_value(values[i],day+" pixel="+std::to_string(i));
        any = true;
    }
    if (!any) throw std::runtime_error("HUM_ALL_NODATA: " + day);
}
}
#endif
