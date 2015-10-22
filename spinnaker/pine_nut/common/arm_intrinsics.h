#pragma once

#include <cstdint>

//-----------------------------------------------------------------------------
// Common::ARMIntrinsics
//-----------------------------------------------------------------------------
namespace Common
{
namespace ARMIntrinsics
{
// This instruction multiplies two signed 32-bit integers
inline int64_t __smull(int32_t x, int32_t y)
{
  register union {struct {int32_t lo; int32_t hi;} words; int64_t val;} result;

  asm volatile("smull %[r_lo], %[r_hi], %[x], %[y]"
              : [r_lo] "=r" ((result.words).lo),
                [r_hi] "=r" ((result.words).hi)
              : [x] "r" (x),
                [y] "r" (y)
              :);

  return result.val;
}

// This instruction multiplies two signed 32-bit integers and accumulates the
// result.
inline int64_t __smlal(int64_t acc, int32_t x, int32_t y)
{
  register union {struct {int32_t lo; int32_t hi;} words; int64_t val;} result;
  result.val = acc;

  asm volatile("smlal %[r_lo], %[r_hi], %[x], %[y]"
              : [r_lo] "+r" ((result.words).lo),
                [r_hi] "+r" ((result.words).hi)
              : [x] "r" (x),
                [y] "r" (y)
              :);

  return result.val;
}


//! This function multiplies two 16-bit signed integers, each from the lower
//! half word
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smulbb (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smulbb %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
}

//! This function multiplies two 16-bit signed integers.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smulbt (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smulbt %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
} 

//! This function multiplies two 16-bit signed integers.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smultb (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smultb %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
}

//! This function multiplies two 16-bit signed integers.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smultt (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smultt %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
}

//! This function multiplies a 32-bit signed integer by the lower 16-bit
//! signed integer of the second argument, giving the topmost 32-bits of the
//! answer.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smulwb (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smulwb %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
}

//! This function multiplies a 32-bit signed integer by the higher 16-bit
//! signed integer of the second argument, giving the topmost 32-bits of the
//! answer.
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \return signed result.

static inline int32_t __smulwt (int32_t x, int32_t y)
{
  register int32_t r;

  asm volatile("smulwt %[r], %[x], %[y]"
              : [r] "=r" (r) : [x] "r" (x), [y] "r" (y) : );

  return r;
}
} // ARMIntrinsics
} // Common