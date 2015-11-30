#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../fixed_point_number.h"

// Namespaces
using namespace Common::FixedPointNumber;

//-----------------------------------------------------------------------------
// Common::Random::NonUniform
//-----------------------------------------------------------------------------
namespace Common
{
namespace Random
{
namespace NonUniform
{
//-----------------------------------------------------------------------------
//  Von Neumann's exponential distribution generator
//
//  from Ripley p.230 and adapted for our types
//
//  Mean number of U(0,1) per call = 5.2
//
//  I have been lazy and copied the GOTOs, sorry!
//-----------------------------------------------------------------------------
// **TODO** to use fully-templated fixed-point types
template<typename R>
S1615 ExponentialDistVariate(R &rng)
{
  S1615 a = 0;

outer:
  uint32_t u = rng.GetNext();
  const uint32_t u0 = u;

inner:
  uint32_t uStar = rng.GetNext();
  if (u < uStar)
  {
    return  a + (S1615)(u0 >> 17);
  }

  u = rng.GetNext();
  if (u < uStar)
  {
    goto inner;
  }

  a += S1615One;
  goto outer;
}

// A poisson distributed random variable, given exp (-lambda).
// **TODO** to use fully-templated fixed-point types
template<typename R>
unsigned int PoissonDistVariate(R &rng, U032 expMinusLambda)
{
  U032 p = 0xFFFFFFFF;
  unsigned int k = 0;

  do
  {
    k++;
    p = MulU032(p, rng.GetNext());
  } while (p > expMinusLambda);

  return (k - 1);
}
} // NonUniform
} // Random
} // Common