#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../common/log.h"
#include "../common/random/mars_kiss64.h"

// Connection builder includes
#include "generator_factory.h"

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
  virtual unsigned int Generate(unsigned int row, unsigned int maxRowWords,
                                MarsKiss64 &rng, uint32_t (&indices)[1024]) const = 0;

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
  virtual unsigned int Generate(unsigned int, unsigned int maxRowWords,
                                MarsKiss64 &, uint32_t (&indices)[1024]) const;

private:
  AllToAll(uint32_t *&region)
  {
    LOG_PRINT(LOG_LEVEL_INFO, "\tAll-to-all connector");
  }
};

} // ConnectorGenerators
} // ConnectionBuilder