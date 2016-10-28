#pragma once

// Standard includes
#include <cstdint>

// Namespaces
using namespace Common::ARMIntrinsics;

//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{
// Description
//
// The above functions compute the absolute value of a fixed-point value f.
//
// Returns
//
// The functions return |f|. If the exact result cannot be represented, the
// saturated result is returned.

// 7.18a.6.3 The fixed-point rounding functions

//! \brief This function rounds the input unsigned 8-bit integer to a number of bits, returning an
//! 8-bit integer.
//! \param[in] f An 8-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.

inline uint8_t Round(uint8_t x, int n)
{
    register uint8_t r, c;

    c = (x >> (n-1)) & 0x1;
    r = x >> n;
    r = (r + c) << n;

    return (r);
}

//! \brief This function rounds the input unsigned 16-bit integer to a number of bits, returning a
//! 16-bit integer.
//! \param[in] f An 16-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline uint16_t Round(uint16_t x, int n)
{
    register uint16_t r, c;

    c = (x >> (n-1)) & 0x1;
    r = x >> n;
    r = (r + c) << n;

    return r;
}

//! \brief This function rounds the input unsigned 32-bit integer to a number of bits, returning an
//! 32-bit integer.
//! \param[in] f An 32-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline uint32_t Round(uint32_t x, int n)
{
    register uint32_t r, c;

    c = (x >> (n-1)) & 0x1;
    r = x >> n;
    r = (r + c) << n;

    return r;
}

//! \brief This function rounds the input unsigned 64-bit integer to a number of bits, returning a
//! 64-bit integer.
//! \param[in] f A 64-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline uint64_t Round(uint64_t x, int n)
{
  register uint64_t r, c;

  c = (x >> (n-1)) & 0x1;
  r = x >> n;
  r = (r + c) << n;

  return r;
}

//! \brief This function rounds the input signed 8-bit integer to a number of bits, returning an
//! 8-bit integer.
//! \param[in] f An 8-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline int8_t Round(int8_t x, int n)
{
  register int8_t r, c;

  c = (x >> (n-1)) & 0x1;
  r = x >> n;
  r = (r + c) << n;

  return r;
}

//! \brief This function rounds the input signed 16-bit integer to a number of bits, returning a
//! 16-bit integer.
//! \param[in] f An 16-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline int16_t Round(int16_t x, int n)
{
  register int16_t r, c;

  c = (x >> (n-1)) & 0x1;
  r = x >> n;
  r = (r + c) << n;

  return (r);
}

//! \brief This function rounds the input signed 32-bit integer to a number of bits, returning an
//! 32-bit integer.
//! \param[in] f An 32-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline int32_t Round(int32_t x, int n)
{
  register int32_t r, c;

  c = (x >> (n-1)) & 0x1;
  r = x >> n;
  r = (r + c) << n;

  return (r);
}

//! \brief This function rounds the input signed 64-bit integer to a number of bits, returning a
//! 64-bit integer.
//! \param[in] f A 64-bit number to be rounded.
//! \param[in] n An int.
//! \return The f rounded to the nearest n bits.
inline int64_t Round(int64_t x, int n)
{
  register int64_t r, c;

  c = (x >> (n-1)) & 0x1;
  r = x >> n;
  r = (r + c) << n;

  return (r);
}
} // Maths
} // Common