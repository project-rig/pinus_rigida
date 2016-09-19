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
// ConnectionBuilder::ConnectorGenerators
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace ConnectorGenerator
{
//-----------------------------------------------------------------------------
// Base
//-----------------------------------------------------------------------------
class Base
{
public:
  //-----------------------------------------------------------------------------
  // Declared virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int maxRowSynapses,
                                unsigned int numPostNeurons, MarsKiss64 &rng,
                                uint32_t (&indices)[1024]) const = 0;

};

//-----------------------------------------------------------------------------
// AllToAll
//-----------------------------------------------------------------------------
class AllToAll : public Base
{
public:
  ADD_FACTORY_CREATOR(AllToAll);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int row, unsigned int maxRowSynapses,
                                unsigned int numPostNeurons, MarsKiss64 &rng,
                                uint32_t (&indices)[1024]) const;

private:
  AllToAll(uint32_t *&)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tAll-to-all connector");
  }
};

} // ConnectorGenerators
} // ConnectionBuilder