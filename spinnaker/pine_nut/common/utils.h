#ifndef UTILS_H
#define UTILS_H

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// Macros
//-----------------------------------------------------------------------------
// The following can be used to silence gcc's "-Wall -Wextra"
// warnings about failure to use function arguments.
//
// Obviously you'll only be using this during debug, for unused
// arguments of callback functions, or where conditional compilation
// means that the accessor functions return a constant
//#define USE(x) do {} while ((x)!=(x))

// Define int/uint helper macros to create the correct
// type names for int/uint of a particular size.
//
// This requires an extra level of macro call to "stringify"
// the result.
//#define __INT_HELPER(b) int ## b ## _t
//#define __UINT_HELPER(b) uint ## b ## _t
//#define INT(b) __INT_HELPER(b)
//#define UINT(b) uint32_t//__UINT_HELPER(b)

#endif  // UTILS_H