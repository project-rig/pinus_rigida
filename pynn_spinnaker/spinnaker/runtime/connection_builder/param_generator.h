#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/log.h"

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
/*binomial':       ('n', 'p'),
'gamma':          ('k', 'theta'),
'exponential':    ('beta',),
'lognormal':      ('mu', 'sigma'),
'normal':         ('mu', 'sigma'),
'normal_clipped': ('mu', 'sigma', 'low', 'high'),
'normal_clipped_to_boundary':
                  ('mu', 'sigma', 'low', 'high'),
'poisson':        ('lambda_',),
'uniform':        ('low', 'high'),
'uniform_int':    ('low', 'high'),*/
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int fixedPoint,
                        MarsKiss64 &rng, int32_t (&integers)[1024]) = 0;

};

//-----------------------------------------------------------------------------
// Constant
//-----------------------------------------------------------------------------
class Constant : public Base
{
public:
  ADD_FACTORY_CREATOR(Constant);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int,
                        MarsKiss64 &, int32_t (&output)[1024]);

private:
  Constant(uint32_t *&region)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tConstant parameter");
  }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Constant;
};

//-----------------------------------------------------------------------------
// Uniform
//-----------------------------------------------------------------------------
class Uniform : public Base
{
public:
  ADD_FACTORY_CREATOR(Uniform);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int,
                        MarsKiss64 &rng, int32_t (&output)[1024]);

private:
  Uniform(uint32_t *&region)
  {
    m_Low = *reinterpret_cast<int32_t*>(region++);
    m_High = *reinterpret_cast<int32_t*>(region++);
    LOG_PRINT(LOG_LEVEL_INFO, "\tUniform parameter: low:%d, high:%d",
              m_Low, m_High);
  }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Low;
  int32_t m_High;
};
} // ParamGenerator
} // ConnectionBuilder