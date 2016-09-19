//-----------------------------------------------------------------------------
// MatrixGenerator::ConnectorGenerators
//-----------------------------------------------------------------------------
namespace MatrixGenerator
{
namespace ConnectorGenerators
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
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual unsigned int Generate(unsigned int, unsigned int maxRowWords,
                                MarsKiss64 &, uint32_t (&indices)[1024]) const
  {
    // Write indices
    for(unsigned int i = 0; i < maxRowWords; i++)
    {
      indices[i] = i;
    }

    return maxRowWords;
  }
};

} // ConnectorGenerators
} // MatrixGenerator