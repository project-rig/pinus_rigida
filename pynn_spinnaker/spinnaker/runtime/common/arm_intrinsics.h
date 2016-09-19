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
  register union {struct {uint32_t lo; uint32_t hi;} words; int64_t val;} result;

  asm volatile("smull %[r_lo], %[r_hi], %[x], %[y]"
              : [r_lo] "=&r" ((result.words).lo),
                [r_hi] "=&r" ((result.words).hi)
              : [x] "r" (x),
                [y] "r" (y)
              :);

  return result.val;
}

// This instruction multiplies two signed 32-bit integers and accumulates the
// result.
inline int64_t __smlal(int64_t acc, int32_t x, int32_t y)
{
  register union {struct {uint32_t lo; uint32_t hi;} words; int64_t val;} result;
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

//! This function performs a 16x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies two 16-bit signed integers, the low halfwords of the first two
//! operands, and adds to the third operand. Sets the Q flag if the addition
//! overflows. (Note that the addition is the usual 32-bit modulo addition which:) 
//! wraps on overflow, not a saturating addition. The multiplication cannot
//! overflow.) 
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline int32_t __smlabb (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlabb %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}


//! This function performs a 16x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies the low halfword of the first operand and the high halfword of
// the second operand, and adds to the third operand, as for __smlabb. 
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline int32_t __smlabt (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlabt %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}

//! This function performs a 16x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies the high halfword of the first operand and the low halfword of
//! the second operand, and adds to the third operand, as for __smlabb. 
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline  int32_t __smlatb (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlatb %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}

//! This function performs a 16x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies the high halfwords of the first two operands and adds to the
//! third operand, as for __smlabb.
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline  int32_t __smlatt (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlatt %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}

//! This function performs a 32x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies the 32-bit signed first operand with the low halfword (as a
//! 16-bit signed integer) of the second operand. Adds the top 32 bits of the
//! 48-bit product to the third operand. Sets the Q flag if the addition
//! overflows. (See note for __smlabb.)
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline  int32_t __smlawb (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlawb %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}

//! This function performs a 32x16 multiply-accumulate, saturating the addition.
//!
//! Multiplies the 32-bit signed first operand with the high halfword (as a
//! 16-bit signed integer) of the second operand and adds the top 32 bits of
//! the 48-bit result to the third operand as for __smlawb.
//!
//! \param[in] x first argument.
//! \param[in] y second argument.
//! \param[in] acc accumulation argument.
//! \return x*y+acc.

static inline  int32_t __smlawt (int32_t x, int32_t y, int32_t acc)
{
    register int32_t r;

    asm volatile ("smlawt %[r], %[x], %[y], %[a]"
                  : [r] "=r" (r) : [x] "r" (x), [y] "r" (y), [a] "r" (acc) : );

    return (r);
}

} // ARMIntrinsics
} // Common