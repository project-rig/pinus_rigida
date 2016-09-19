//-----------------------------------------------------------------------------
// MatrixGenerator::ParamGenerators
//-----------------------------------------------------------------------------
namespace MatrixGenerator
{
namespace ParamGenerators
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
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int,
                        MarsKiss64 &, int32_t (&output)[1024])
  {
    // Copy constant into output
    for(uint32_t i = 0; i < number; i++)
    {
      output[i] = m_Constant;
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Constant;
};

//-----------------------------------------------------------------------------
// Uniform
//-----------------------------------------------------------------------------
class Uniform
{
public:
  //-----------------------------------------------------------------------------
  // Base virtuals
  //-----------------------------------------------------------------------------
  virtual void Generate(unsigned int number, unsigned int,
                        MarsKiss64 &rng, int32_t (&output)[1024])
  {
    // Copy constant into output
    for(uint32_t i = 0; i < number; i++)
    {
      output[i] = ;
    }
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  int32_t m_Low;
  int32_t m_High;
};
} // RNG
} // MatrixGenerator