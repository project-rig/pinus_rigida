//-----------------------------------------------------------------------------
// ConnectionBuilder::MatrixGenerators
//-----------------------------------------------------------------------------
namespace ConnectionBuilder
{
namespace MatrixGenerators
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
  virtual void Write(uint32_t *matrixAddress, unsigned int rowWords, unsigned int numRows
    unsigned int weightFixedPoint,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng) const = 0;
};

//-----------------------------------------------------------------------------
// Static
//-----------------------------------------------------------------------------
template<unsigned int D, unsigned int I>
class Static : public Base
{
public:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Write(uint32_t *matrixAddress, unsigned int maxRowWords, unsigned int numRows
    unsigned int weightFixedPoint,
    const ParamGenerators::Base &delayGenerator, const ParamGenerators::Base &weightGenerator,
    const ConnectorGenerators::Base &connectorGenerator, MarsKiss64 &rng) const
  {
    // Loop through rows
    for(uint32_t i = 0; i < numRows; i++)
    {
      // Generate row indices
      uint32_t indices[1024];
      unsigned int numIndices = connectorGenerator.Generate(i, maxRowWords,
                                                            rng, indices);

      // Generate delays and weights for each index
      int32_t delays[1024];
      int32_t weights[1024];
      delayGenerator.Generate(numIndices, rng, delays);
      weightGenerator.Generate(numIndices, rng, weights);

      // Write row length
      *matrixAddress++ = numIndices;

      // **TODO** support delay extension
      *matrixAddress++ = 0;
      *matrixAddress++ = 0;

      // Loop through synapses and write synaptic words
      for(unsigned int j = 0; j < numIndices; j++)
      {
        *matrixAddress++ = (indices[j] & IndexMask) |
          ((delays[j] & DelayMask) << I) |
          (weights[j] << (D + I));
      }

      // Skip end of row padding
      *matrixAddress += (maxRowWords - numIndices);
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const T DelayMask = ((1 << D) - 1);
  static const T IndexMask = ((1 << I) - 1);
};

} // MatrixGenerators
} // ConnectionBuilder