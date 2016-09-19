#pragma once

#include "generator_factory.h"

//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerator
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace MatrixGenerator
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
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowWords,
    unsigned int weightFixedPoint/*,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng*/) const = 0;
};

//-----------------------------------------------------------------------------
// Static
//-----------------------------------------------------------------------------
template<unsigned int D, unsigned int I>
class Static : public Base
{
public:
  ADD_FACTORY_CREATOR(Static);

  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(uint32_t *matrixAddress, unsigned int maxRowWords,
    unsigned int weightFixedPoint/*,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng*/) const
  {
    // Loop through rows
    for(uint32_t i = 0; i < m_NumRows; i++)
    {
      // Generate row indices
      uint32_t indices[1024];
      unsigned int numIndices = 7;//connectorGenerator.Generate(i, maxRowWords,
      //                                                     rng, indices);

      // Generate delays and weights for each index
      int32_t delays[1024];
      int32_t weights[1024];
      //delayGenerator.Generate(numIndices, rng, delays);
      //weightGenerator.Generate(numIndices, rng, weights);

      // Write row length
      *matrixAddress++ = numIndices;

      // **TODO** support delay extension
      *matrixAddress++ = 0;
      *matrixAddress++ = 0;

      // Loop through synapses and write synaptic words
      for(unsigned int j = 0; j < numIndices; j++)
      {
        *matrixAddress++ = (indices[j] & IndexMask) |
          (((uint32_t)delays[j] & DelayMask) << I) |
          (weights[j] << (D + I));
      }

      // Skip end of row padding
      *matrixAddress += (maxRowWords - numIndices);
    }
  }

private:
  Static(uint32_t *&region)
  {
    m_NumRows = *region++;
  }
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const uint32_t DelayMask = ((1 << D) - 1);
  static const uint32_t IndexMask = ((1 << I) - 1);

  uint32_t m_NumRows;
};

} // MatrixGenerator
} // ConnectionBuilder