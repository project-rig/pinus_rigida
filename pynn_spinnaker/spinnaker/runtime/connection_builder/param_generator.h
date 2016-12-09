#pragma once

// Standard includes
#include <cstdint>

// Connection builder includes
#include "generator_factory.h"

// Forward declarations
namespace Common
{
  namespace Random
  {
    class MarsKiss64;
  }
}

// Namespaces
using namespace Common::Random;

//-----------------------------------------------------------------------------
// ConnectionBuilder::ParamGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace ParamGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
//! Base class for all parameter generators
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  //! Write a fixed number of 32-bit fixed point values to the specified array
  //!   \param number     integer specifying the number of values to generate.
  //!   \param fixedPoint unsigned integer specifying the location of the
  //!                     fixed-point in the output representation.
  //!   \param rng        random number generator to use, if required.
  //!   \param integers   reference to array to write generated parameters to.
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&integers)[1024]) const = 0;
};

//-----------------------------------------------------------------------------
// Constant
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with same value
class Constant : public Base
{
public:
  ADD_FACTORY_CREATOR(Constant);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  Constant(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! The value to generate
  int32_t m_Value;
};

//-----------------------------------------------------------------------------
// Uniform
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with uniforms distributed values
class Uniform : public Base
{
public:
  ADD_FACTORY_CREATOR(Uniform);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  Uniform(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Minimum value (inclusive)
  int32_t m_Low;

  //! Range (high-low) (exclusive)
  int32_t m_Range;
};

//-----------------------------------------------------------------------------
// Normal
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with normally distributed values
class Normal : public Base
{
public:
  ADD_FACTORY_CREATOR(Normal);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  Normal(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Mean of values
  int32_t m_Mu;

  //! Standard deviation of values
  int32_t m_Sigma;
};

//-----------------------------------------------------------------------------
// Normal clipped
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with normally distributed values.
//! Values outside of the [m_Low, m_High) interval are redrawn.
class NormalClipped : public Base
{
public:
  ADD_FACTORY_CREATOR(NormalClipped);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  NormalClipped(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Mean of values
  int32_t m_Mu;

  //! Standard deviation of values
  int32_t m_Sigma;

  //! Minimum value (inclusive)
  int32_t m_Low;

  //! Maximum value (exclusive)
  int32_t m_High;
};

//-----------------------------------------------------------------------------
// Normal clipped to boundary
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with normally distributed values.
//! Values outside of the [m_Low, m_High) interval are clamped.
class NormalClippedToBoundary : public Base
{
public:
  ADD_FACTORY_CREATOR(NormalClippedToBoundary);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  NormalClippedToBoundary(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Mean of values
  int32_t m_Mu;

  //! Standard deviation of values
  int32_t m_Sigma;

  //! Minimum value (inclusive)
  int32_t m_Low;

  //! Maximum value (exclusive)
  int32_t m_High;
};

//-----------------------------------------------------------------------------
// Exponential
//-----------------------------------------------------------------------------
//! Parameter generator which fills array with exponentially distributed values.
class Exponential : public Base
{
public:
  ADD_FACTORY_CREATOR(Exponential);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&output)[1024]) const;

private:
  Exponential(uint32_t *&region);

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  //! Mean of values
  int32_t m_Beta;
};
 
} // ParamGenerator
} // ConnectionBuilder
